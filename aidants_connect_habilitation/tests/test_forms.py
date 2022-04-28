from unittest.mock import Mock, patch

from django.test import TestCase

from aidants_connect.common.constants import (
    MessageStakeholders,
    RequestOriginConstants,
    RequestStatusConstants,
)
from aidants_connect_habilitation.forms import (
    AidantRequestFormSet,
    IssuerForm,
    ManagerForm,
    OrganisationRequestForm,
    PersonnelForm,
    ValidationForm,
)
from aidants_connect_habilitation.models import OrganisationRequest
from aidants_connect_habilitation.tests.factories import (
    DraftOrganisationRequestFactory,
    ManagerFactory,
)
from aidants_connect_habilitation.tests.utils import get_form
from aidants_connect_web.models import OrganisationType


class TestIssuerForm(TestCase):
    def test_form_is_valid_with_dom_tom_phonenumber(self):
        form = IssuerForm(
            data={
                "phone": "06 90 11 12 13",
                "first_name": "Mary",
                "last_name": "Read",
                "profession": "Pirate",
                "email": "mary_read@example.com",
            }
        )

        self.assertTrue(form.is_valid())


class TestOrganisationRequestForm(TestCase):
    def test_clean_type_passes(self):
        form = get_form(
            OrganisationRequestForm,
            type_id=RequestOriginConstants.MEDIATHEQUE.value,
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["type"],
            OrganisationType.objects.get(pk=RequestOriginConstants.MEDIATHEQUE.value),
        )

    def test_clean_type_other_returns_user_value(self):
        form = get_form(
            OrganisationRequestForm,
            type_id=RequestOriginConstants.OTHER.value,
            type_other="L'organisation des travaillleurs",
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["type_other"], "L'organisation des travaillleurs"
        )

    def test_clean_type_other_returns_blank_on_specific_org_type(self):
        form = get_form(
            OrganisationRequestForm,
            type_id=RequestOriginConstants.MEDIATHEQUE.value,
            type_other="L'organisation des travaillleurs",
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["type_other"], "")

    def test_clean_type_other_unspecified_raises_error(self):
        form = get_form(
            OrganisationRequestForm,
            ignore_errors=True,
            type_id=RequestOriginConstants.OTHER.value,
            type_other=None,
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["type_other"],
            [
                f"Le champ « Type de structure si autre » doit être rempli "
                f"si la structure est de type {RequestOriginConstants.OTHER.label}."
            ],
        )

    def test_clean_type_zipcode_number_passes(self):
        form = get_form(
            OrganisationRequestForm,
            ignore_errors=True,
            type_id=RequestOriginConstants.OTHER.value,
            zipcode="01700",
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})

    def test_clean_type_zipcode_not_number_raises_error(self):
        form = get_form(
            OrganisationRequestForm,
            ignore_errors=True,
            type_id=RequestOriginConstants.OTHER.value,
            zipcode="La Commune",
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["zipcode"], ["Veuillez entrer un code postal valide"]
        )

    def test_private_org_requires_partner_administration(self):
        form = get_form(
            OrganisationRequestForm,
            ignore_errors=True,
            is_private_org=True,
            partner_administration="",
        )
        self.assertFalse(form.is_valid())
        self.assertIn("merci de renseigner", form.errors["partner_administration"][0])

    def test_private_org_keeps_partner_administration(self):
        form = get_form(
            OrganisationRequestForm,
            is_private_org=True,
            partner_administration="Beta.Gouv",
        )
        self.assertTrue(form.is_valid())
        self.assertEqual("Beta.Gouv", form.cleaned_data["partner_administration"])

    def test_non_private_org_clears_partner_administration(self):
        form = get_form(
            OrganisationRequestForm,
            is_private_org=False,
            partner_administration="Beta.Gouv",
        )
        self.assertTrue(form.is_valid())
        self.assertEqual("", form.cleaned_data["partner_administration"])

    def test_france_services_label_requires_fs_number(self):
        form = get_form(
            OrganisationRequestForm,
            france_services_label=True,
            france_services_number=None,
            ignore_errors=True,
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "merci de renseigner son numéro", form.errors["france_services_number"][0]
        )

    def test_france_services_label_keeps_fs_number(self):
        form = get_form(
            OrganisationRequestForm,
            france_services_label=True,
            france_services_number=444666999,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["france_services_number"], 444666999)

    def test_no_france_services_label_clears_fs_number(self):
        form = get_form(
            OrganisationRequestForm,
            france_services_label=False,
            france_services_number=444666999,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual("", form.cleaned_data["france_services_number"])


class TestPersonnelForm(TestCase):
    @patch("aidants_connect_habilitation.forms.ManagerForm.is_valid")
    @patch("aidants_connect_habilitation.forms.AidantRequestFormSet.is_valid")
    def test_is_valid_only_if_all_subforms_are_valid(
        self,
        mock_manager_form_is_valid: Mock,
        mock_aidants_form_is_valid: Mock,
    ):
        form = PersonnelForm()

        mock_manager_form_is_valid.return_value = True
        mock_aidants_form_is_valid.return_value = True

        self.assertTrue(form.is_valid())

        mock_manager_form_is_valid.return_value = False
        mock_aidants_form_is_valid.return_value = True

        self.assertFalse(form.is_valid())

        mock_manager_form_is_valid.return_value = True
        mock_aidants_form_is_valid.return_value = False

        self.assertFalse(form.is_valid())

    def test_save(self):
        organisation: OrganisationRequest = DraftOrganisationRequestFactory()

        manager_data = get_form(ManagerForm).clean()
        aidants_form = get_form(AidantRequestFormSet)
        aidants_data = aidants_form.data

        cleaned_data = {
            **{
                f"{PersonnelForm.MANAGER_FORM_PREFIX}-{k}": v
                for k, v in manager_data.items()
            },
            **{
                k.replace("form-", f"{PersonnelForm.AIDANTS_FORMSET_PREFIX}-"): v
                for k, v in aidants_data.items()
            },
        }

        form = PersonnelForm(data=cleaned_data)
        self.assertTrue(form.is_valid())

        self.assertIs(organisation.manager, None)
        self.assertEqual(organisation.aidant_requests.count(), 0)

        form.save(organisation)

        self.assertEqual(organisation.manager.email, manager_data["email"])
        self.assertEqual(organisation.aidant_requests.count(), len(aidants_form.forms))
        self.assertNotEqual(organisation.aidant_requests.count(), 0)


class TestValidationFormForm(TestCase):
    names_attr = ["cgu", "dpo", "professionals_only", "without_elected"]

    def test_form_valid_only_with_four_enabled_choices(self):
        form = ValidationForm()
        self.assertFalse(form.is_valid())

        form = ValidationForm(data={"cgu": True})
        self.assertFalse(form.is_valid())

        form = ValidationForm(
            data={name: True for name in TestValidationFormForm.names_attr}
        )
        self.assertTrue(form.is_valid())

    def test_form_valid_works(self):
        orga_request = DraftOrganisationRequestFactory(
            cgu=False,
            dpo=False,
            professionals_only=False,
            without_elected=False,
            manager=ManagerFactory(),
        )

        form = ValidationForm(
            data={name: True for name in TestValidationFormForm.names_attr}
        )
        form.data["message_content"] = "Bonjour"
        form.is_valid()

        orga = form.save(organisation=orga_request)
        self.assertEqual(
            orga.status, RequestStatusConstants.AC_VALIDATION_PROCESSING.name
        )
        [
            self.assertTrue(getattr(orga, name))
            for name in TestValidationFormForm.names_attr
        ]
        self.assertEqual(orga.messages.all()[0].content, "Bonjour")
        self.assertEqual(orga.messages.all()[0].sender, MessageStakeholders.ISSUER.name)


class TestManagerForm(TestCase):
    def test_clean_type_zipcode_number_passes(self):
        form = get_form(
            OrganisationRequestForm,
            ignore_errors=True,
            type_id=RequestOriginConstants.OTHER.value,
            zipcode="01700",
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})

    def test_clean_type_zipcode_not_number_raises_error(self):
        form = get_form(
            OrganisationRequestForm,
            ignore_errors=True,
            type_id=RequestOriginConstants.OTHER.value,
            zipcode="La Commune",
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["zipcode"], ["Veuillez entrer un code postal valide"]
        )
