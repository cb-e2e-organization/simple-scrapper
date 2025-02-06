from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import csv
import time


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

    def remove_scrapped_project(self, project):
        with open("unscrapped_projects.txt", "r") as f:
            lines = f.readlines()
        with open("unscrapped_projects.txt", "w") as f:
            for line in lines:
                if line.strip("\n") != project:
                    f.write(line)

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

        WebDriverWait(self.driver, 15).until(
            lambda _: self.driver.find_element(
                By.XPATH, "//*[contains(@class, 'spectrum-Heading1')]"
            ).text
            in ["Verify your identity", "Enter your password"]
        )

        if (
            self.driver.find_element(
                By.XPATH, "//*[contains(@class, 'spectrum-Heading1')]"
            ).text
            == "Verify your identity"
        ):
            self.driver.find_element(
                By.XPATH, "//*[contains(@class, 'spectrum-Button')]"
            ).click()

            WebDriverWait(self.driver, 15).until(
                EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, "Destination--multi-line"), self.email
                )
            )

            verification_code = input("Enter verification code: ")
            if len(verification_code) != 6:
                self.driver.quit()
                raise Exception("Verification code is not 6 digits")

            code_input = self.driver.find_element(
                By.XPATH, "//*[contains(@class, 'CodeInput')]"
            )

            i = 0
            for input_ in code_input.find_elements(
                By.XPATH, "//*[contains(@class, 'spectrum-Textfield')]"
            ):
                input_.send_keys(verification_code[i])
                i += 1

        WebDriverWait(self.driver, 15).until(
            EC.text_to_be_present_in_element(
                (By.XPATH, "//*[contains(@class, 'Profile-Email')]"),
                self.email,
            )
        )
        self.driver.find_element(By.ID, "PasswordPage-PasswordField").send_keys(
            self.password
        )

        WebDriverWait(self.driver, 15).until(
            lambda _: self.driver.find_element(
                By.ID, "PasswordPage-PasswordField"
            ).get_attribute("value")
            == self.password
        )

        self.driver.find_element(
            By.XPATH, "//*[contains(@class, 'spectrum-Button')]"
        ).click()

        self.logged_in = True
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@class, 'Search-filtersAndContent')]")
            )
        )

    def _get_projects(self):
        grids = [
            self.driver.find_element(By.XPATH, f"//*[contains(@class, {i})]")
            for i in ["ContentGrid-root", "Projects-grid"]
        ]
        projects = []
        for grid in grids:
            # get all the project links
            grid_items = grid.find_elements(
                By.XPATH, "//*[contains(@class, 'ProjectCoverNeue-coverLink')]"
            )
            for item in grid_items:
                projects.append(item.get_attribute("href"))

        projects = [i for i in projects if i not in self._unscrapped_projects]
        # open links.csv abd check if any of the projects are in there
        # if they are, remove them from projects

        with open("links.csv") as f:
            scrapped_links = [row[1] for row in csv.reader(f)]
            projects = [i for i in projects if i not in scrapped_links]

        with open("unscrapped_projects.txt", "a") as f:
            for i in projects:
                f.write(i + "\n")

        return projects

    def get_projects(self):
        if not self.logged_in and not self.only_unscrapped:
            self.login()

            print("Scrolling...\n")
            i = 0

            while not self.driver.execute_script(
                "if (document.body.scrollHeight == document.body.scrollTop + window.innerHeight) { return true; } else { return false; }"
            ):
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(1)
                i += 1
                if i >= self.scrolls:
                    break

        print("Getting projects...\n")

        # from item self.from_item
        self._get_projects()
        projects = set(self._unscrapped_projects)
        with open("links.csv") as f:
            scrapped_links = [row[1] for row in csv.reader(f)]

        print(f"Total projects: {len(projects)}\n\n")

        total_steps = len(projects)
        current_step = 0
        links_found = 0

        self.driver.quit()
        self.driver = self._driver(headless=True)

        for project in set(projects):

            current_step += 1
            print(f"{current_step} out of {total_steps} done\n")
            print(f"Progress: {round(current_step/total_steps*100, 2)}%\n")
            print(f"Total links found: {links_found}\n")

            if project in scrapped_links:
                continue
            self.driver.get(project)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(@class, 'Project-project')]")
                )
            )
            embeds = self.driver.find_elements(By.TAG_NAME, "iframe")
            figma_links = list(
                set(
                    [
                        i.get_attribute("src")
                        for i in embeds
                        if i.get_attribute("src").startswith("https://www.figma")
                    ]
                )
            )
            if figma_links:
                csv_file = open("links.csv", "a")
                project_title = self.driver.find_element(
                    By.XPATH, "//*[contains(@class, 'Project-title')]"
                ).text

                csv_writer = csv.writer(csv_file)
                csv_writer.writerow([project_title, project, figma_links[0]])
                csv_file.close()
                links_found += 1
            self.remove_scrapped_project(project)

        self.driver.quit()


if __name__ == "__main__":
    url = (
        input("Enter Behance url: ")
        or "https://www.behance.net/search/projects?search=ui+ux+case+study+figma+web+design&tracking_source=typeahead_search_suggestion&tools=442140153"
    )
    email = input("Enter behance email: ") or "timothee.greyson@findours.com"
    password = input("Enter behance password: ") or "ept0ZRP6gwm*tdr7tuz"
    only_unscrapped = input("Only unscrapped projects? (y/n): ") or "n"
    scrolls = int(input("Enter number of times to scroll: ") or 5)

    scrapper = BehanceScrapper(
        email=email,
        password=password,
        scrolls=scrolls,
        url=url,
        only_unscrapped=True if only_unscrapped == "y" else False,
    )
    scrapper.get_projects()
