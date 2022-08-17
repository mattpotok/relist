import logging

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


class Listing:
    def __init__(self, id):
        self._id = id

    def renew(self, browser):
        logging.debug(f"Relisting Facebook listing '{self._id}'...")

        try:
            browser.get(f"https://www.facebook.com/marketplace/item/{self._id}")
            if browser.current_url.endswith("unavailable_product=1"):
                logging.error(f"Unable to find Facebook listing '{id}'")
                return False

            renew_btn = browser.find_element(By.XPATH, "//span[text()='Renew listing']")
            renew_btn.click()
        except NoSuchElementException:
            logging.warning(f"Facebook listing '{self._id}' cannot be renewed")
            return False
        except Exception:
            logging.exception(f"Unable to relist Facbook listing '{self._id}'")
            return False

        logging.info(f"Relisted Facebook listing '{self._id}'")
        return True

    @property
    def id(self):
        return self._id


def _login(browser, credentials):
    email = credentials["email"]
    password = credentials["password"]
    logging.debug("Logging into Facebook...")

    try:
        browser.get("https://facebook.com")
        browser.find_element(By.ID, "email").send_keys(email)
        browser.find_element(By.ID, "pass").send_keys(password)
        browser.find_element(By.NAME, "login").click()
    except Exception:
        logging.exception("Unable to log into Facebook")
        return False

    logging.info("Logged into Facebook")
    return True


def _logout(browser):
    logging.debug("Logging out of Facebook...")

    try:
        browser.get("https://www.facebook.com/marketplace/you/selling")
        profile_btn = browser.find_element(
            By.XPATH, "//*[name()='svg' and @aria-label='Your profile']"
        )
        profile_btn.click()
        log_out_btn = browser.find_element(By.XPATH, "//span[text()='Log Out']")
        log_out_btn.click()
    except Exception:
        logging.exception("Unable to log out of Facebook")

    logging.info("Logged out of Facebook")


def _relist_listings(browser, listings):
    failures = []
    successes = []
    for id in listings["ids"]:
        listing = Listing(id)
        if listing.renew(browser):
            successes.append(listing.id)
        else:
            failures.append(listing.id)

    logging.info(
        f"Successfully relisted Facebook listings '{successes}', "
        f"unable to relist Facebook listings '{failures}'"
    )


def relist(browser, config):
    if _login(browser, config["credentials"]):
        _relist_listings(browser, config["listings"])
        _logout(browser)
