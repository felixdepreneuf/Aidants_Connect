import time
from unittest import skip

from django.conf import settings
from django.test import tag

from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import url_matches
from selenium.webdriver.support.wait import WebDriverWait

from aidants_connect_common.tests.testcases import FunctionalTestCase
from aidants_connect_web.tests.factories import AidantFactory
from aidants_connect_web.tests.test_functional.utilities import login_aidant


@tag("functional", "new_mandat")
class CreateNewMandatTests(FunctionalTestCase):
    @classmethod
    def setUpClass(cls):
        # FC only calls back on specific port
        cls.port = settings.FC_AS_FS_TEST_PORT
        super().setUpClass()

    def setUp(self) -> None:
        self.aidant = AidantFactory(email="thierry@thierry.com")
        device = self.aidant.staticdevice_set.create(id=1)
        device.token_set.create(token="123456")
        device.token_set.create(token="123455")

    def test_create_new_mandat(self):
        wait = WebDriverWait(self.selenium, 10)

        self.open_live_url("/usagers/")

        login_aidant(self)

        welcome_aidant = self.selenium.find_element(By.TAG_NAME, "h1").text
        self.assertEqual(welcome_aidant, "Vos usagères et usagers")

        usagers_before = self.selenium.find_elements(By.TAG_NAME, "tr")
        self.assertEqual(len(usagers_before), 0)

        # Create new mandat
        add_usager_button = self.selenium.find_element(By.ID, "add_usager")
        add_usager_button.click()

        demarches_section = self.selenium.find_element(By.ID, "demarches")
        demarche_title = demarches_section.find_element(By.TAG_NAME, "h2").text
        self.assertEqual(demarche_title, "Étape 1 : Sélectionnez la ou les démarche(s)")

        demarches_grid = self.selenium.find_element(By.ID, "demarches_list")
        demarches = demarches_grid.find_elements(By.TAG_NAME, "input")
        self.assertEqual(len(demarches), 10)

        demarches_section.find_element(By.ID, "argent").find_element(
            By.TAG_NAME, "label"
        ).click()
        demarches_section.find_element(By.ID, "famille").find_element(
            By.TAG_NAME, "label"
        ).click()

        duree_section = self.selenium.find_element(By.ID, "duree")
        duree_section.find_element(By.ID, "SHORT").find_element(
            By.TAG_NAME, "label"
        ).click()

        # FranceConnect
        fc_button = self.selenium.find_element(By.ID, "submit_button")
        fc_button.click()
        fc_title = self.selenium.title
        self.assertEqual("Connexion - choix du compte", fc_title)
        time.sleep(2)

        # Nouvelle mire dialog
        if len(self.selenium.find_elements(By.ID, "message-on-login")) > 0:
            temp_test_nouvelle_mire_masquer = self.selenium.find_element(
                By.ID, "message-on-login-close"
            )
            temp_test_nouvelle_mire_masquer.click()

        # Click on the 'Démonstration' identity provider
        demonstration_hex = self.selenium.find_element(
            By.ID, "fi-identity-provider-example"
        )
        demonstration_hex.click()
        time.sleep(2)

        # FC - Use the Mélaine_trois credentials
        demo_title = self.selenium.find_element(By.TAG_NAME, "h3").text
        self.assertEqual(demo_title, "Fournisseur d'identité de démonstration")
        submit_button = self.selenium.find_elements(By.TAG_NAME, "input")[2]
        self.assertEqual(submit_button.get_attribute("type"), "submit")
        submit_button.click()
        wait.until(url_matches(r"https://.+franceconnect\.fr/api/v1/authorize.+"))

        # FC - Validate the information
        submit_button = self.selenium.find_element(By.TAG_NAME, "button")
        submit_button.click()
        time.sleep(2)

        # Recap all the information for the Mandat
        recap_title = self.selenium.find_element(By.TAG_NAME, "h1").text
        self.assertEqual(recap_title, "Récapitulatif du mandat")
        recap_text = self.selenium.find_element(By.ID, "recap_text").text
        self.assertIn("Angela Claire Louise DUBOIS ", recap_text)
        checkboxes = self.selenium.find_elements(By.TAG_NAME, "input")
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
        success_title = self.selenium.find_element(By.TAG_NAME, "h1").text
        self.assertEqual(success_title, "Le mandat a été créé avec succès !")
        go_to_usager_button = self.selenium.find_element(
            By.CLASS_NAME, "tiles"
        ).find_elements(By.TAG_NAME, "a")[1]
        go_to_usager_button.click()

        # See all mandats of usager page
        active_mandats_after = self.selenium.find_elements(By.TAG_NAME, "table")[
            0
        ].find_elements(By.CSS_SELECTOR, "tbody tr")
        self.assertEqual(len(active_mandats_after), 2)

    @skip("Reactivate when SMS consent is a thing")
    def test_create_new_remote_mandat(self):
        wait = WebDriverWait(self.selenium, 10)

        self.open_live_url("/usagers/")

        login_aidant(self)

        welcome_aidant = self.selenium.find_element(By.TAG_NAME, "h1").text
        self.assertEqual(welcome_aidant, "Vos usagères et usagers")

        usagers_before = self.selenium.find_elements(By.TAG_NAME, "tr")
        self.assertEqual(len(usagers_before), 0)

        # Create new mandat
        add_usager_button = self.selenium.find_element(By.ID, "add_usager")
        add_usager_button.click()

        demarches_section = self.selenium.find_element(By.ID, "demarches")
        demarche_title = demarches_section.find_element(By.TAG_NAME, "h2").text
        self.assertEqual(demarche_title, "Étape 1 : Sélectionnez la ou les démarche(s)")

        demarches_grid = self.selenium.find_element(By.ID, "demarches_list")
        demarches = demarches_grid.find_elements(By.TAG_NAME, "input")
        self.assertEqual(len(demarches), 10)

        demarches_section.find_element(By.ID, "argent").find_element(
            By.TAG_NAME, "label"
        ).click()
        demarches_section.find_element(By.ID, "famille").find_element(
            By.TAG_NAME, "label"
        ).click()

        duree_section = self.selenium.find_element(By.ID, "duree")
        duree_section.find_element(By.ID, "SHORT").find_element(
            By.TAG_NAME, "label"
        ).click()

        self.selenium.find_element(By.ID, "id_is_remote").click()
        self.selenium.find_element(By.ID, "id_user_phone").send_keys("0 800 840 800")

        # FranceConnect
        fc_button = self.selenium.find_element(By.ID, "submit_button")
        fc_button.click()
        fc_title = self.selenium.title
        self.assertEqual("Connexion - choix du compte", fc_title)
        time.sleep(2)

        # Nouvelle mire dialog
        if len(self.selenium.find_elements(By.ID, "message-on-login")) > 0:
            temp_test_nouvelle_mire_masquer = self.selenium.find_element(
                By.ID, "message-on-login-close"
            )
            temp_test_nouvelle_mire_masquer.click()

        # Click on the 'Démonstration' identity provider
        demonstration_hex = self.selenium.find_element(
            By.ID, "fi-identity-provider-example"
        )
        demonstration_hex.click()
        time.sleep(2)

        # FC - Use the Mélaine_trois credentials
        demo_title = self.selenium.find_element(By.TAG_NAME, "h3").text
        self.assertEqual(demo_title, "Fournisseur d'identité de démonstration")
        submit_button = self.selenium.find_elements(By.TAG_NAME, "input")[2]
        self.assertEqual(submit_button.get_attribute("type"), "submit")
        submit_button.click()
        wait.until(url_matches(r"https://.+franceconnect\.fr/api/v1/authorize.+"))

        # FC - Validate the information
        submit_button = self.selenium.find_element(By.TAG_NAME, "button")
        submit_button.click()
        time.sleep(2)

        # Recap all the information for the Mandat
        recap_title = self.selenium.find_element(By.TAG_NAME, "h1").text
        self.assertEqual(recap_title, "Récapitulatif du mandat")
        recap_text = self.selenium.find_element(By.ID, "recap_text").text
        self.assertIn("Angela Claire Louise DUBOIS ", recap_text)
        checkboxes = self.selenium.find_elements(By.TAG_NAME, "input")
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
        success_title = self.selenium.find_element(By.TAG_NAME, "h1").text
        self.assertEqual(success_title, "Le mandat a été créé avec succès !")
        go_to_usager_button = self.selenium.find_element(
            By.CLASS_NAME, "tiles"
        ).find_elements(By.TAG_NAME, "a")[1]
        go_to_usager_button.click()

        # See all mandats of usager page
        active_mandats_after = self.selenium.find_elements(By.TAG_NAME, "table")[
            0
        ].find_elements(By.CSS_SELECTOR, "tbody tr")
        self.assertEqual(len(active_mandats_after), 2)
