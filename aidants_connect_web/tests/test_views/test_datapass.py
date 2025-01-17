from django.conf import settings
from django.core import mail
from django.test import TestCase, tag
from django.urls import resolve

from aidants_connect_web.models import (
    HabilitationRequest,
    Organisation,
    OrganisationType,
)
from aidants_connect_web.tests.factories import (
    HabilitationRequestFactory,
    OrganisationFactory,
)
from aidants_connect_web.views import datapass


class DatapassMixin:
    def datapass_request(self, data):
        return self.client.post(
            self.datapass_url,
            data=data,
            **{"HTTP_AUTHORIZATION": f"Bearer {self.datapass_key}"},
        )

    def test_bad_authorization_header_triggers_403(self):
        response = self.client.get(
            self.datapass_url, **{"HTTP_AUTHORIZATION": "bad_token"}
        )
        self.assertEqual(response.status_code, 403)

    def test_no_authorization_header_triggers_403(self):
        response = self.client.post(self.datapass_url)
        self.assertEqual(response.status_code, 403)


@tag("datapass")
class OrganisationDatapass(DatapassMixin, TestCase):

    datapass_url = "/datapass_receiver/"

    @classmethod
    def setUpTestData(cls):
        cls.good_data_from_datapass = {
            "data_pass_id": 34,
            "organization_name": "La maison de l'aide",
            "organization_siret": 11111111111111,
            "organization_address": "4 rue du clos, 90210, La Colline de Bev",
            "organization_type": "Mairie",
            "organization_postal_code": "90210",
        }
        cls.datapass_key = settings.DATAPASS_KEY

    def test_datapass_url_triggers_the_good_view(self):
        found = resolve(self.datapass_url)
        self.assertEqual(found.func, datapass.organisation_receiver)

    def test_empty_data_triggers_400(self):
        response = self.datapass_request(data={})
        self.assertEqual(response.status_code, 400)

    def test_message_body_can_create_organisation(self):
        orga_type_count = OrganisationType.objects.count()
        response = self.datapass_request(data=self.good_data_from_datapass)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(Organisation.objects.count(), 1)
        self.assertEqual(
            Organisation.objects.first().address,
            "4 rue du clos, 90210, La Colline de Bev",
        )
        self.assertEqual(Organisation.objects.first().siret, 11111111111111)
        self.assertEqual(Organisation.objects.first().data_pass_id, 34)
        self.assertEqual(
            Organisation.objects.first().type,
            OrganisationType.objects.get(name="Mairie"),
        )
        self.assertEqual(Organisation.objects.first().zipcode, "90210")
        self.assertEqual(OrganisationType.objects.count(), orga_type_count + 1)

        another_data = self.good_data_from_datapass.copy()
        another_data["data_pass_id"] = 33
        response = self.datapass_request(data=another_data)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(Organisation.objects.count(), 2)
        self.assertEqual(OrganisationType.objects.count(), orga_type_count + 1)

    def test_message_body_dont_recreate_organisation(self):
        OrganisationFactory(data_pass_id=34)
        self.assertEqual(Organisation.objects.count(), 1)
        response = self.datapass_request(data=self.good_data_from_datapass)
        self.assertEqual(Organisation.objects.count(), 1)
        self.assertEqual(response.status_code, 200)

    def test_id_NaN_generates_bad_request(self):
        for should_be_a_number in ["data_pass_id", "organization_siret"]:

            bad_data_from_datapass = self.good_data_from_datapass.copy()
            bad_data_from_datapass[should_be_a_number] = "bad_data"

            response = self.datapass_request(data=bad_data_from_datapass)
            self.assertEqual(response.status_code, 400)

    def test_good_data_creates_email(self):
        self.datapass_request(data=self.good_data_from_datapass)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Une nouvelle structure")
        self.assertIn("La maison de l'aide", email.body)
        self.assertIn(settings.DATAPASS_FROM_EMAIL, email.from_email)
        self.assertIn(settings.DATAPASS_TO_EMAIL, email.to)


@tag("datapass")
class HabilitationDatapass(DatapassMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organisation = OrganisationFactory(data_pass_id=42)
        cls.good_data_from_datapass = {
            "data_pass_id": 42,
            "first_name": "Mario",
            "last_name": "Brosse",
            "email": "Mario.Brossse@world.fr",
            "profession": "plombier",
        }

        cls.empty_value = {
            "data_pass_id": 42,
            "first_name": "",
            "last_name": "",
            "email": "",
            "profession": "",
        }

        cls.without_email = {
            "data_pass_id": 42,
            "first_name": "Mario",
            "last_name": "Brosse",
            "email": "",
            "profession": "plombier",
        }

        cls.datapass_key = settings.DATAPASS_KEY
        cls.datapass_url = "/datapass_habilitation/"

    def test_datapass_url_triggers_the_good_view(self):
        found = resolve(self.datapass_url)
        self.assertEqual(found.func, datapass.habilitation_receiver)

    def test_datapass_dont_recreate_habilitation_request(self):
        HabilitationRequestFactory(
            organisation=self.organisation, email="mario.brossse@world.fr"
        )
        self.assertEqual(HabilitationRequest.objects.count(), 1)
        response = self.datapass_request(data=self.good_data_from_datapass)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(HabilitationRequest.objects.count(), 1)

    def test_empty_message_body_dont_return_error(self):
        self.assertEqual(HabilitationRequest.objects.count(), 0)
        response = self.datapass_request(data=self.empty_value)
        self.assertEqual(response.status_code, 200)
        response = self.datapass_request(data={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(HabilitationRequest.objects.count(), 0)

    def test_body_without_email_dont_raise_exception(self):
        self.assertEqual(HabilitationRequest.objects.count(), 0)
        response = self.datapass_request(data=self.without_email)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(HabilitationRequest.objects.count(), 0)

    def test_message_body_can_create_habilitation_request(self):
        self.assertEqual(HabilitationRequest.objects.count(), 0)
        response = self.datapass_request(data=self.good_data_from_datapass)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(HabilitationRequest.objects.count(), 1)
        habilitation_request = HabilitationRequest.objects.first()
        self.assertEqual(
            habilitation_request.origin, HabilitationRequest.ORIGIN_DATAPASS
        )
        self.assertEqual(habilitation_request.status, HabilitationRequest.STATUS_NEW)
