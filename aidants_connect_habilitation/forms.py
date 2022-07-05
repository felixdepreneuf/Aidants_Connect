from typing import List, Tuple, Union

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import (
    BaseModelFormSet,
    BooleanField,
    CharField,
    ChoiceField,
    Form,
    RadioSelect,
    Textarea,
    modelformset_factory,
)
from django.forms.formsets import MAX_NUM_FORM_COUNT, TOTAL_FORM_COUNT
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import quote, unquote
from django.utils.translation import gettext as _

from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

from aidants_connect.common.constants import MessageStakeholders, RequestOriginConstants
from aidants_connect.common.forms import (
    AcPhoneNumberField,
    PatchedErrorList,
    PatchedErrorListForm,
    PatchedForm,
)
from aidants_connect.common.gouv_address_api import Address, search_adresses
from aidants_connect_habilitation import models
from aidants_connect_habilitation.models import (
    AidantRequest,
    Manager,
    OrganisationRequest,
    PersonWithResponsibilities,
    RequestMessage,
)
from aidants_connect_web.models import OrganisationType


class AddressValidatableMixin(Form):
    DEFAULT_CHOICE = "DEFAULT"

    # Necessary so dynamically setting properties
    # in __init__ does not mess with original classes
    class XChoiceField(ChoiceField):
        def validate(self, value):
            # Disable value validation, only keep value requirement
            if value in self.empty_values and self.required:
                raise ValidationError(self.error_messages["required"], code="required")

    class XRadioSelect(RadioSelect):
        pass

    alternative_address = XChoiceField(
        label="Veuillez sélectionner votre adresse dans les propositions ci-dessous :",
        choices=((DEFAULT_CHOICE, "Laisser l'adresse inchangée"),),
        widget=XRadioSelect(attrs={"class": "choice-field"}),
        required=False,
    )

    @property
    def should_display_addresses_select(self):
        return self.__required

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__required = False

        required = property(lambda _: self.__required)
        setattr(AddressValidatableMixin.XChoiceField, "required", required)
        setattr(AddressValidatableMixin.XRadioSelect, "is_required", required)

    def clean_alternative_address(self):
        alternative_address = self.data.get(self.add_prefix("alternative_address"))

        if alternative_address == self.DEFAULT_CHOICE:
            return self.DEFAULT_CHOICE
        elif alternative_address:
            return Address.parse_raw(unquote(alternative_address))
        else:
            results = search_adresses(self.get_address_for_search())

            # Case not result returned (most likely, HTTP request failed)
            if len(results) == 0:
                return self.DEFAULT_CHOICE

            # There is 1 result and it almost 100% matches
            if (
                len(results) == 1
                and results[0].label == self.get_address_for_search()
                and results[0].score > 0.90
            ):
                return results[0]

            self.__required = True

            for result in results:
                self.fields["alternative_address"].choices = [
                    (quote(result.json()), result.label),
                    *self.fields["alternative_address"].choices,
                ]

            raise ValidationError("Plusieurs choix d'adresse sont possibles")

    def post_clean(self):
        """
        Call this method at the end of your own Form's ``clean`` method to
        prevent.
        """
        alternative_address = self.cleaned_data.pop("alternative_address", None)
        if isinstance(alternative_address, Address):
            self.autocomplete(alternative_address)

    def get_address_for_search(self) -> str:
        """
        Implement this method to provide a string to search on the address
        API. This method may, for instance, concatenate street name, zipcode
        and city fields that may otherwise be seperated.
        """
        raise NotImplementedError()

    def autocomplete(self, address: Address):
        """
        Implement this method to fill your Form with the address when the
        API returns one result that matches with more than 90% probability.
        """
        raise NotImplementedError()


class IssuerForm(PatchedErrorListForm):
    phone = AcPhoneNumberField(
        initial="",
        label="Téléphone",
        region=settings.PHONENUMBER_DEFAULT_REGION,
        widget=PhoneNumberInternationalFallbackWidget(
            region=settings.PHONENUMBER_DEFAULT_REGION
        ),
        required=False,
    )

    def __init__(self, render_non_editable=False, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(**kwargs)
        self.render_non_editable = render_non_editable
        if self.render_non_editable:
            self.auto_id = False
            for name, field in self.fields.items():
                field.disabled = True
                field.widget.attrs.update(id=f"id_{name}")

    def add_prefix(self, field_name):
        """
        Return empty ``name`` HTML attribute when ``self.render_non_editable is True``
        """
        return "" if self.render_non_editable else super().add_prefix(field_name)

    def add_initial_prefix(self, field_name):
        """
        Return empty ``name`` HTML attribute when ``self.render_non_editable is True``
        """
        return (
            "" if self.render_non_editable else super().add_initial_prefix(field_name)
        )

    class Meta:
        model = models.Issuer
        exclude = ["issuer_id", "email_verified"]


class OrganisationRequestForm(PatchedErrorListForm):
    type = ChoiceField(required=True, choices=RequestOriginConstants.choices)

    name = CharField(
        label="Nom de la structure",
    )

    zipcode = CharField(
        label="Code Postal",
        max_length=10,
        error_messages={
            "required": "Le champ « code postal » est obligatoire.",
        },
    )
    city = CharField(
        label="Ville",
        max_length=255,
        error_messages={
            "required": "Le champ « ville » est obligatoire.",
        },
    )

    is_private_org = BooleanField(
        label=(
            "Cochez cette case si vous faites cette demande pour une structure privée "
            "(hors associations)"
        ),
        required=False,
    )

    partner_administration = CharField(
        label="Renseignez l’administration avec laquelle vous travaillez",
        required=False,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.widget_attrs(
            "type_other",
            {
                "data-dynamic-form-target": "typeOtherInput",
                "data-displayed-label": "Veuillez préciser le type d’organisation",
            },
        )
        self.widget_attrs(
            "type",
            {
                "data-action": "change->dynamic-form#onTypeChange",
                "data-dynamic-form-target": "typeInput",
                "data-other-value": RequestOriginConstants.OTHER.value,
            },
        )
        self.widget_attrs(
            "is_private_org",
            {
                "data-action": "change->dynamic-form#onIsPrivateOrgChange",
                "data-dynamic-form-target": "privateOrgInput",
            },
        )
        self.widget_attrs(
            "france_services_label",
            {
                "data-action": "change->dynamic-form#onFranceServicesChange",
                "data-dynamic-form-target": "franceServicesInput",
            },
        )

    def clean_type(self):
        return OrganisationType.objects.get(pk=int(self.data["type"]))

    def clean_type_other(self):
        if int(self.data["type"]) != RequestOriginConstants.OTHER.value:
            return ""

        if not self.data["type_other"]:
            label = self.fields["type_other"].label
            raise ValidationError(
                f"Le champ « {label} » doit être rempli si la "
                f"structure est de type {RequestOriginConstants.OTHER.label}."
            )

        return self.data["type_other"]

    def clean_partner_administration(self):
        if not self.data.get("is_private_org", False):
            return ""

        if not self.data["partner_administration"]:
            raise ValidationError(
                "Vous avez indiqué que la structure est privée : merci de renseigner "
                "votre administration partenaire."
            )

        return self.data["partner_administration"]

    def clean_france_services_number(self):
        if not self.data.get("france_services_label", False):
            return ""

        if not self.data["france_services_number"]:
            raise ValidationError(
                "Vous avez indiqué que la structure est labellisée France Services : "
                "merci de renseigner son numéro d’immatriculation France Services."
            )

        return self.data["france_services_number"]

    def clean_zipcode(self):
        data: str = self.cleaned_data["zipcode"]
        if not data.isnumeric():
            raise ValidationError("Veuillez entrer un code postal valide")

        return data

    class Meta:
        model = models.OrganisationRequest
        fields = [
            "type",
            "type_other",
            "name",
            "siret",
            "address",
            "zipcode",
            "city",
            "is_private_org",
            "partner_administration",
            "france_services_label",
            "france_services_number",
            "web_site",
            "mission_description",
            "avg_nb_demarches",
        ]


class PersonWithResponsibilitiesForm(PatchedErrorListForm):
    phone = AcPhoneNumberField(
        initial="",
        region=settings.PHONENUMBER_DEFAULT_REGION,
        widget=PhoneNumberInternationalFallbackWidget(
            region=settings.PHONENUMBER_DEFAULT_REGION
        ),
        required=False,
    )

    class Meta:
        model = PersonWithResponsibilities
        exclude = ["id"]


class ManagerForm(PersonWithResponsibilitiesForm, AddressValidatableMixin):
    zipcode = CharField(
        label="Code Postal",
        max_length=10,
        error_messages={
            "required": "Le champ « code postal » est obligatoire.",
        },
    )

    city = CharField(
        label="Ville",
        max_length=255,
        error_messages={
            "required": "Le champ « ville » est obligatoire.",
        },
    )

    def get_address_for_search(self) -> str:
        return (
            f"{self.data[self.add_prefix('address')]} "
            f"{self.data[self.add_prefix('zipcode')]} "
            f"{self.data[self.add_prefix('city')]}"
        )

    def autocomplete(self, address: Address):
        self.cleaned_data["address"] = address.name
        self.cleaned_data["zipcode"] = address.postcode
        self.cleaned_data["city"] = address.city

    def clean_zipcode(self):
        data: str = self.cleaned_data["zipcode"]
        if not data.isnumeric():
            raise ValidationError("Veuillez entrer un code postal valide")

        return data

    def clean(self):
        result = super().clean()
        super().post_clean()
        return result

    class Meta(PersonWithResponsibilitiesForm.Meta):
        model = Manager


class EmailOrganisationValidationError(ValidationError):
    def __init__(self, email):
        super().__init__(
            _(
                "Il y a déjà un aidant ou une aidante avec l'adresse email '%(email)s' "
                "dans cette organisation. Chaque aidant ou aidante doit avoir "
                "son propre e-mail nominatif."
            ),
            code="unique_together",
            params={"email": email},
        )


class AidantRequestForm(PatchedErrorListForm):
    def __init__(self, organisation: OrganisationRequest, **kwargs):
        self.organisation = organisation
        super().__init__(**kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"]
        # If self.instance is defined, se are modfiying an existing instance
        # not creating a new one
        if (not self.instance or not self.instance.pk) and AidantRequest.objects.filter(
            organisation=self.organisation, email=email
        ).exists():
            raise EmailOrganisationValidationError(email)

        return email

    class Meta:
        model = AidantRequest
        exclude = ["organisation"]


class BaseAidantRequestFormSet(BaseModelFormSet):
    def __init__(self, organisation: OrganisationRequest, **kwargs):
        self.organisation = organisation
        kwargs.setdefault("queryset", AidantRequest.objects.none())
        kwargs.setdefault("error_class", PatchedErrorList)

        super().__init__(**kwargs)

        self.__management_form_widget_attrs(
            TOTAL_FORM_COUNT, {"data-personnel-form-target": "managmentFormCount"}
        )
        self.__management_form_widget_attrs(
            MAX_NUM_FORM_COUNT, {"data-personnel-form-target": "managmentFormMaxCount"}
        )

    def clean(self):
        emails = {}
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue

            email = form.cleaned_data.get("email")

            # Do not test if email is empty: may be a legitimate empty form
            if email:
                emails.setdefault(email, [])
                emails[email].append(form)

        for email, grouped_forms in emails.items():
            if len(grouped_forms) > 1:
                for form in grouped_forms:
                    form.add_error(
                        "email",
                        EmailOrganisationValidationError(email),
                    )

        super().clean()

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["organisation"] = self.organisation
        return kwargs

    def add_non_form_error(self, error: Union[ValidationError, str]):
        if not isinstance(error, ValidationError):
            error = ValidationError(error)
        self._non_form_errors.append(error)

    def is_empty(self):
        for form in self.forms:
            # If the form is not valid, it has data to correct so it is not empty
            if not form.is_valid() or form.is_valid() and len(form.cleaned_data) != 0:
                return False

        return True

    def __management_form_widget_attrs(self, widget_name: str, attrs: dict):
        widget = self.management_form.fields[widget_name].widget
        for attr_name, attr_value in attrs.items():
            widget.attrs[attr_name] = attr_value


AidantRequestFormSet = modelformset_factory(
    AidantRequestForm.Meta.model, AidantRequestForm, formset=BaseAidantRequestFormSet
)


class PersonnelForm:
    MANAGER_FORM_PREFIX = "manager"
    AIDANTS_FORMSET_PREFIX = "aidants"

    @property
    def errors(self):
        if self._errors is None:
            self._clean()
        return self._errors

    def __init__(self, organisation: OrganisationRequest, **kwargs):
        self.organisation = organisation

        def merge_kwargs(prefix):
            previous_prefix = kwargs.get("prefix")
            local_kwargs = {}

            form_kwargs_prefixes = {
                self.MANAGER_FORM_PREFIX,
                self.AIDANTS_FORMSET_PREFIX,
            }

            for k, v in kwargs.items():
                """
                Let us dispatch form kwargs to specific forms by using their prefixes.

                For instance, PersonnelForm(manager_instance=some_instance) will
                disptach to ManagerForm(instance=some_instance).
                """
                kwarg_prefix = k.split("_")
                if len(kwarg_prefix) > 1 and kwarg_prefix[0] in form_kwargs_prefixes:
                    if kwarg_prefix[0] == prefix:
                        k_prefix_removed = k[len(f"{prefix}_") :]
                        local_kwargs[k_prefix_removed] = v
                else:
                    local_kwargs[k] = v

            return {
                **local_kwargs,
                "prefix": prefix
                if not previous_prefix
                else f"{prefix}_{previous_prefix}",
            }

        self._errors = None

        self.manager_form = ManagerForm(**merge_kwargs(self.MANAGER_FORM_PREFIX))

        self.aidants_formset = AidantRequestFormSet(
            organisation=self.organisation, **merge_kwargs(self.AIDANTS_FORMSET_PREFIX)
        )

    def _clean(self):
        self._errors = PatchedErrorList()

        if not self.manager_form.is_bound or not self.aidants_formset.is_bound:
            # Stop processing if form does not have data
            return

        if (
            not self.manager_form.cleaned_data["is_aidant"]
            and self.aidants_formset.is_empty()
        ):
            self._errors.append(
                "Vous devez déclarer au moins 1 aidant si le ou la responsable de "
                "l'organisation n'est pas elle-même déclarée comme aidante"
            )
            self.manager_form.add_error(
                "is_aidant",
                "Veuillez cocher cette case ou déclarer au moins un aidant ci-dessous",
            )
            self.aidants_formset.add_non_form_error(
                "Vous devez déclarer au moins 1 aidant si le ou la responsable de "
                "l'organisation n'est pas elle-même déclarée comme aidante"
            )

    def add_error(self, error: Union[ValidationError, str]):
        if not isinstance(error, ValidationError):
            error = ValidationError(error)
        self._errors.append(error)

    def is_valid(self) -> bool:
        # Eagerly compute the result of `is_valid` calls
        # to prevent early return of the boolean computation.

        # 'self.errors' must be last called so that subforms are
        # validated before performing a global validation
        is_valid = [
            self.manager_form.is_valid(),
            self.aidants_formset.is_valid(),
            not self.errors,
        ]

        return all(is_valid)

    def save(self, commit=True) -> Tuple[Manager, List[AidantRequest]]:
        for form in self.aidants_formset:
            form.instance.organisation = self.organisation

        manager_instance, aidants_instances = (
            self.manager_form.save(commit),
            self.aidants_formset.save(commit),
        )

        self.organisation.manager = manager_instance
        self.organisation.save()

        return manager_instance, aidants_instances

    save.alters_data = True


class ValidationForm(PatchedForm):
    cgu = BooleanField(
        required=True,
        label='J’ai pris connaissance des <a href="{url}">'
        "conditions générales d’utilisation</a> et je les valide.",
    )
    dpo = BooleanField(
        required=True,
        label="Je confirme que le délégué à la protection des données "
        "de mon organisation est informé de ma demande.",
    )
    professionals_only = BooleanField(
        required=True,
        label="Je confirme que la liste des aidants à habiliter contient "
        "exclusivement des aidants professionnels. Elle ne contient "
        "donc ni service civique, ni bénévole, ni apprenti, ni stagiaire.",
    )
    without_elected = BooleanField(
        required=True,
        label="Je confirme qu’aucun élu n’est impliqué dans l’habilitation "
        "Aidants Connect. Le responsable Aidants Connect ainsi que les aidants "
        "à habiliter ne sont pas des élus.",
    )
    message_content = CharField(
        label="Votre message", required=False, widget=Textarea(attrs={"rows": 4})
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        cgu = self["cgu"]
        cgu.label = format_html(cgu.label, url=reverse("cgu"))

    def save(
        self, organisation: OrganisationRequest, commit=True
    ) -> OrganisationRequest:
        organisation.prepare_request_for_ac_validation(self.cleaned_data)
        if self.cleaned_data["message_content"] != "":
            RequestMessage.objects.create(
                organisation=organisation,
                sender=MessageStakeholders.ISSUER.name,
                content=self.cleaned_data["message_content"],
            )
        return organisation

    save.alters_data = True


class RequestMessageForm(PatchedErrorListForm):
    content = CharField(label="Votre message", widget=Textarea(attrs={"rows": 2}))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widget_attrs("content", {"data-message-form-target": "textarea"})

    class Meta:
        model = models.RequestMessage
        fields = ["content"]


class AdminAcceptationOrRefusalForm(PatchedForm):
    email_subject = CharField(label="Sujet de l’email", required=True)
    email_body = CharField(label="Contenu de l’email", widget=Textarea, required=True)

    def __init__(self, organisation, **kwargs):
        super().__init__(**kwargs)
        self.organisation = organisation
