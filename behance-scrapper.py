from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait



class BehanceScrapper:
    def __init__(self, scrolls, email, password, url, only_unscrapped=False):
        self.url = url
        self.scrolls = scrolls
        self.email = email
        self.password = password
        self.logged_in = False
        self.only_unscrapped = only_unscrapped
        self.driver = self._driver()
        if not self.only_unscrapped:
            self.driver.get(self.url)

    def _driver(self, headless=False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("headless")
        options.add_argument("window-size=1200x600")
        driver = webdriver.Chrome(options=options)
        return driver

    @property
    def _unscrapped_projects(self):
        with open("unscrapped_projects.txt", "r") as f:
            data = f.read().splitlines()
        with open("unscrapped_projects.txt", "w") as f:
            for line in set(data):
                f.write(line + "\n")

        return open("unscrapped_projects.txt", "r").read().splitlines()

    def login(self):
        self.driver.get(self.url)

        print("Logging in...\n")
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@class, 'js-adobeid-signin')]")
            )
        )
        # Login to Behance
        self.driver.find_element(
            By.XPATH, "//*[contains(@class, 'PrimaryNav-loggedOutOptions')]"
        ).find_element(
            By.XPATH, "//*[contains(@class, 'e2e-PrimaryNav-Signin')]"
        ).click()

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@class, 'CardLayout')]")
            )
        )

        self.driver.find_element(By.ID, "EmailPage-EmailField").send_keys(self.email)

        WebDriverWait(self.driver, 15).until(
            lambda _: self.driver.find_element(
                By.ID, "EmailPage-EmailField"
            ).get_attribute("value")
            == self.email
        )

        self.driver.find_element(
            By.XPATH, "//*[contains(@class, 'spectrum-Button')]"
        ).click()


if __name__ == "__main__":
    url = (
        input("Enter Behance url: ")
        or "https://www.behance.net/search/projects?search=ui+ux+case+study+figma+web+design&tracking_source=typeahead_search_suggestion&tools=442140153"
    )
    email = input("Enter behance email: ")
    password = input("Enter behance password: ")
    only_unscrapped = input("Only unscrapped projects? (y/n): ") or "n"
    scrolls = int(input("Enter number of times to scroll: ") or 5)

    scrapper = BehanceScrapper(
        email=email,
        password=password,
        scrolls=scrolls,
        url=url,
        only_unscrapped=True if only_unscrapped == "y" else False,
    )
    scrapper.logged_in()
