import logging
from pathlib import Path

from relist.common import Result, reprint
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tabulate import tabulate

logger = logging.getLogger(Path(__file__).stem)


class Listing:
    def __init__(self, title):
        self._title = title

    def relist(self, browser):
        title = self._title

        try:
            # Navigate to listing
            browser.get(
                f"https://www.facebook.com/marketplace/you/selling?title_search={title}"
            )

            WebDriverWait(browser, 1000).until(
                EC.visibility_of_element_located(
                    (By.XPATH, f"//span[text()='{title}']")
                )
            )

            # Validate listing exists
            try:
                browser.find_element(
                    By.XPATH, '//span[text()="We didn\'t find anything"]'
                )
                logger.warning(f"Invalid Facebook listing '{title}'")
                return Result.INVALID
            except NoSuchElementException:
                pass

            # TODO if multiple listing exist, then iterate over each one of them
            # Relist listing
            try:
                button = browser.find_element(
                    By.XPATH, "//div[contains(@aria-label, 'Delete & Relist')]"
                )
                button.click()
                logger.info(f"Relisted Facebook listing '{title}'")
                return Result.RELISTED
            except NoSuchElementException:
                pass

            # Renew listing
            try:
                button = browser.find_element(
                    By.XPATH, "//div[contains(@aria-label, 'Renew listing')]"
                )
                button.click()
                logger.info(f"Renewed Facebook listing '{title}'")
                return Result.RENEWED
            except NoSuchElementException:
                logger.info(f"Facebook listing '{title}' is currently active")
                return Result.ACTIVE

        except:
            logger.exception(f"Exception relisting Facebook listing '{title}'")
            return Result.EXCEPTION

    @property
    def title(self):
        return self._title


def _login(browser, credentials):
    reprint("Logging into Facebook - executing...")

    email = credentials["email"]
    password = credentials["password"]

    try:
        browser.get("https://facebook.com")
        browser.find_element(By.ID, "email").send_keys(email)
        browser.find_element(By.ID, "pass").send_keys(password)
        browser.find_element(By.NAME, "login").click()

        # TODO wait until some element is visible
    except:
        logger.exception("Unable to log into Facebook")
        return False

    reprint("Logging into Facebook - done", overwrite=True)
    logger.info("Logged into Facebook")

    return True


def _logout(browser):
    reprint("Logging out of Facebook - executing...")

    try:
        browser.get("https://www.facebook.com/marketplace/you/selling")
        # FIXME may need to add a wait here
        profile_btn = browser.find_element(
            By.XPATH, "//*[name()='svg' and @aria-label='Your profile']"
        )
        profile_btn.click()

        WebDriverWait(browser, 3000).until(
            EC.visibility_of_element_located((By.XPATH, "//span[text()='Log Out']"))
        )
        log_out_btn = browser.find_element(By.XPATH, "//span[text()='Log Out']")
        log_out_btn.click()
    except:
        logger.exception("Unable to log out of Facebook")

    reprint("Logging out of Facebook - done", overwrite=True)


def _relist(browser, listings):
    reprint("Relisting Facebook postings")

    for title in listings["titles"]:
        reprint(f"  Listing '{title}' - relisting...")

        listing = Listing(title)
        result = listing.relist(browser)

        reprint(f"  Listing '{title}' - {result.with_color}", overwrite=True)


def relist(browser, config):
    if _login(browser, config["credentials"]):
        _relist(browser, config["listings"])
        _logout(browser)
