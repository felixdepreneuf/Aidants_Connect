from datetime import timedelta

from django.test import tag

from django.utils import timezone
from aidants_connect_web.models import Mandat

from aidants_connect_web.tests.factories import (
    AidantFactory,
    MandatFactory,
    UsagerFactory,
)
from aidants_connect_web.tests.test_functional.testcases import FunctionalTestCase
from aidants_connect_web.tests.test_functional.utilities import login_aidant


@tag("functional", "renew_mandat")
class RenewMandatTests(FunctionalTestCase):
    def test_renew_mandat(self):
        self.aidant = AidantFactory()
        device = self.aidant.staticdevice_set.create(id=1)
        device.token_set.create(token="123456")
        device.token_set.create(token="123455")

        self.usager = UsagerFactory(given_name="Fabrice")
        MandatFactory(
            organisation=self.aidant.organisation,
            usager=self.usager,
            expiration_date=timezone.now() + timedelta(days=5),
        )
        self.assertEqual(Mandat.objects.filter(usager=self.usager).count(), 1)

        self.open_live_url(f"/renew_mandat/{self.usager.pk}")

        login_aidant(self)

        demarches_section = self.selenium.find_element_by_id("demarches")
        demarche_title = demarches_section.find_element_by_tag_name("h2").text
        self.assertEqual(demarche_title, "Étape 1 : Sélectionnez la ou les démarche(s)")

        demarches_grid = self.selenium.find_element_by_id("demarches_list")
        demarches = demarches_grid.find_elements_by_tag_name("input")
        self.assertEqual(len(demarches), 10)

        demarches_section.find_element_by_id("argent").find_element_by_tag_name(
            "label"
        ).click()
        demarches_section.find_element_by_id("famille").find_element_by_tag_name(
            "label"
        ).click()

        duree_section = self.selenium.find_element_by_id("duree")
        duree_section.find_element_by_id("SHORT").find_element_by_tag_name(
            "label"
        ).click()

        # Renew Mandat
        fc_button = self.selenium.find_element_by_id("submit_renew_button")
        fc_button.click()

        # Recap all the information for the Mandat
        recap_title = self.selenium.find_element_by_tag_name("h1").text
        self.assertEqual(recap_title, "Récapitulatif du mandat")
        recap_text = self.selenium.find_element_by_id("recap_text").text
        self.assertIn("Fabrice Simpson ", recap_text)
        checkboxes = self.selenium.find_elements_by_tag_name("input")
        id_personal_data = checkboxes[1]
        self.assertEqual(id_personal_data.get_attribute("id"), "id_personal_data")
        id_personal_data.click()
        id_otp_token = checkboxes[2]
        self.assertEqual(id_otp_token.get_attribute("id"), "id_otp_token")
        id_otp_token.send_keys("123455")
        submit_button = checkboxes[-1]
        self.assertEqual(submit_button.get_attribute("type"), "submit")
        submit_button.click()

        # Success page
        success_title = self.selenium.find_element_by_tag_name("h1").text
        self.assertEqual(success_title, "Le mandat a été créé avec succès !")
        go_to_usager_button = self.selenium.find_element_by_class_name(
            "tiles"
        ).find_elements_by_tag_name("a")[1]
        go_to_usager_button.click()

        self.assertEqual(Mandat.objects.filter(usager=self.usager).count(), 2)
