from django.test import TestCase, tag
from django.test.client import Client

from django_otp.plugins.otp_totp.models import TOTPDevice

from aidants_connect_web.models import CarteTOTP, Journal
from aidants_connect_web.tests.factories import AidantFactory, CarteTOTPFactory


@tag("responsable-structure")
class DissociateCarteTOTPTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        # Create one responsable : Tom
        cls.responsable_tom = AidantFactory(username="tom@tom.fr")
        cls.responsable_tom.responsable_de.add(cls.responsable_tom.organisation)
        cls.org_id = cls.responsable_tom.organisation.id
        # Create one aidant : Tim
        cls.aidant_tim = AidantFactory(
            username="tim@tim.fr",
            organisation=cls.responsable_tom.organisation,
            first_name="Tim",
            last_name="Onier",
        )
        cls.dissociation_url = (
            f"/espace-responsable/aidant/{cls.aidant_tim.id}/supprimer-carte/"
        )
        cls.aidant_url = f"/espace-responsable/aidant/{cls.aidant_tim.id}/"

    def create_carte_for_tim(self):
        self.carte = CarteTOTPFactory(
            serial_number="A123", seed="FA169F10A9", aidant=self.aidant_tim
        )

    def create_device_for_tim(self, confirmed=True):
        self.device = TOTPDevice(
            tolerance=30,
            key=self.carte.seed,
            user=self.aidant_tim,
            step=60,
            confirmed=confirmed,
        )
        self.device.save()

    def do_the_checks(self):
        # Submit post and check redirection is correct
        self.client.force_login(self.responsable_tom)
        response = self.client.post(
            self.dissociation_url,
            data={"reason": "perte"},
        )
        self.assertRedirects(response, self.aidant_url, fetch_redirect_response=False)
        response = self.client.get(self.aidant_url)
        response_content = response.content.decode("utf-8")
        self.assertIn("Tout s’est bien passé", response_content)
        # Check card still exists but that TOTP Device doesn't
        carte = CarteTOTP.objects.last()
        self.assertEqual(carte.serial_number, self.carte.serial_number)
        self.assertIsNone(carte.aidant)
        self.assertEqual(TOTPDevice.objects.count(), 0)
        # Check journal entry creation
        journal_entry = Journal.objects.last()
        self.assertEqual(
            journal_entry.action,
            "card_dissociation",
            "A Journal entry should have been created on card validation.",
        )

    def test_dissociation_in_nominal_case(self):
        self.create_carte_for_tim()
        self.create_device_for_tim()
        self.do_the_checks()

    def test_dissociation_without_existing_totp_device(self):
        self.create_carte_for_tim()
        self.do_the_checks()

    def test_dissociation_with_unconfirmed_totp_device(self):
        self.create_carte_for_tim()
        self.create_device_for_tim(confirmed=False)
        self.do_the_checks()
