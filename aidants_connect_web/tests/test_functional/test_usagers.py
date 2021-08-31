from aidants_connect_web.tests.factories import (
    AidantFactory,
    UsagerFactory,
    MandatFactory,
    ExpiredMandatFactory,
)
from aidants_connect_web.tests.test_functional.testcases import FunctionalTestCase
from aidants_connect_web.tests.test_functional.utilities import login_aidant


class UsagersTest(FunctionalTestCase):
    def setUp(self):
        self.aidant = AidantFactory(post__with_otp_device=True)

        self.usager_josephine = UsagerFactory(
            given_name="Joséphine", family_name="ST-PIERRE"
        )

        self.usager_anne = UsagerFactory(
            given_name="Anne Cécile Gertrude", family_name="EVALOUS"
        )

        self.usager_corentin = UsagerFactory(
            given_name="Corentin", family_name="Dupont", preferred_username="Anne"
        )

        MandatFactory(
            organisation=self.aidant.organisation,
            usager=self.usager_josephine,
            post__create_authorisations=["argent", "famille"],
        )

        ExpiredMandatFactory(
            organisation=self.aidant.organisation,
            usager=self.usager_corentin,
            post__create_authorisations=["argent", "famille", "logement"],
        )

        MandatFactory(
            organisation=self.aidant.organisation,
            usager=self.usager_anne,
            post__create_authorisations=["argent", "famille", "logement"],
        )

    def test_search_feature(self):
        self.open_live_url("/usagers/")
        login_aidant(self)

        user_with_valid_mandate = self.selenium.find_elements_by_css_selector(
            ".table.with-valid-mandate tbody tr"
        )

        user_without_valid_mandate = self.selenium.find_elements_by_css_selector(
            ".table.without-valid-mandate tbody tr"
        )

        self.assertEqual(len(user_with_valid_mandate), 2)
        self.assertEqual(len(user_without_valid_mandate), 1)

        self.selenium.find_element_by_id("filter-input").send_keys("Anne")

        anne_result = self.selenium.find_element_by_xpath(
            "//*[normalize-space()='Anne Cécile Gertrude']"
        )
        josephine_result = self.selenium.find_element_by_xpath(
            "//*[normalize-space()='Joséphine']"
        )
        corentin_result = self.selenium.find_element_by_xpath(
            "//*[normalize-space()='Corentin']"
        )

        self.assertTrue(anne_result.is_displayed())
        self.assertFalse(josephine_result.is_displayed())
        self.assertTrue(corentin_result.is_displayed())