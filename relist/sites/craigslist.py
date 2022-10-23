import logging
from enum import Enum
from pathlib import Path

from relist.common import Result, reprint
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(Path(__file__).stem)


class PostingStatus(Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    EXPIRED = "expired"
    INVALID = "invalid"

    @classmethod
    def from_posting_status_color(cls, color):
        if color == "rgb(144, 238, 144)":
            return PostingStatus.ACTIVE
        elif color == "rgb(173, 216, 230)":
            return PostingStatus.DELETED
        elif color == "rgb(204, 153, 255)":
            return PostingStatus.EXPIRED
        else:
            raise ValueError(f"Invalid posting status color '{color}'")


class Posting:
    def __init__(self, id):
        self._id = id

    def relist(self, browser):
        try:
            # Navigate to listing
            browser.get(f"https://post.craigslist.org/manage/{self._id}")

            # Validate listing exists
            try:
                browser.find_element(
                    By.XPATH, "//p[normalize-space()='Page Not Found']"
                )
                logger.warning(f"Cannot find posting '{self.id}'")
                return Result.INVALID
            except NoSuchElementException:
                pass

            # Determine posting status
            manage_status = browser.find_element(By.CLASS_NAME, "managestatus")
            color = manage_status.value_of_css_property("background-color")
            status = PostingStatus.from_posting_status_color(color)

            # Handle posting
            if status == PostingStatus.ACTIVE:
                try:
                    self._relist(browser)
                    return Result.RENEWED
                except NoSuchElementException:
                    return Result.ACTIVE

            elif status == PostingStatus.EXPIRED:
                self._repost(browser)
                return Result.REPOSTED

            else:
                logger.warning(
                    f"Cannot relist '{status}' Craigslist posting '{self.id}'"
                )
                return Result.INVALID

        except:
            logger.exception(f"Exception relisting Craigslist posting '{self.id}'")
            return Result.EXCEPTION

    def _relist(self, browser):
        renew_btn = browser.find_element(
            By.XPATH, "//input[@value='Renew this Posting']"
        )
        renew_btn.click()

    def _repost(self, browser):
        repost_btn = browser.find_element(By.CLASS_NAME, "managebtn")
        repost_btn.click()

        submit_btn = browser.find_element(
            By.XPATH, "//button[contains(@class, 'submit-button')]"
        )
        submit_btn.click()

        draft_warning = browser.find_element(By.CLASS_NAME, "draft_warning")
        publish_btn = draft_warning.find_element(By.TAG_NAME, "button")
        publish_btn.click()

        # TODO wait for the page to load here
        posting_link = browser.find_element(By.LINK_TEXT, "Manage your post")
        posting_url = posting_link.get_attribute("href")
        self._id = posting_url[(posting_url.rfind("/") + 1) :]

    @property
    def id(self):
        return self._id


def _login(browser, credentials):
    reprint("Logging into Craigslist - executing...")

    email = credentials["email"]
    password = credentials["password"]

    try:
        browser.get("https://accounts.craigslist.org/login")
        browser.find_element(By.ID, "inputEmailHandle").send_keys(email)
        browser.find_element(By.ID, "inputPassword").send_keys(password)
        browser.find_element(By.ID, "login").click()

        WebDriverWait(browser, 1).until(
            EC.visibility_of_element_located((By.XPATH, f"//a[text()='log out']"))
        )
    except:
        logger.exception("Unable to log into Craigslist")
        return False

    reprint("Logging into Craigslist - done", overwrite=True)
    return True


def _logout(browser):
    reprint("Logging out of Craigslist - executing...")

    try:
        browser.get("https://accounts.craigslist.org/login/home")
        browser.find_element(By.XPATH, "//a[text()='log out']").click()
    except:
        logger.exception("Unable to log out of Craigslist")

    reprint("Logging out of Craigslist - done", overwrite=True)


def _relist(browser, postings):
    reprint("Relisting Craigslist postings")

    ids = []
    for id in postings["ids"]:
        reprint(f"  Posting '{id}' - relisting...")

        posting = Posting(id)
        result = posting.relist(browser)
        ids.append(posting.id)

        reprint(f"  Posting '{id}' - {result.with_color}", overwrite=True)

    postings["ids"] = sorted(ids)


def relist(browser, config):
    if _login(browser, config["credentials"]):
        _relist(browser, config["postings"])
        _logout(browser)
