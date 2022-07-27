import logging
from datetime import datetime, timezone
from enum import Enum

from colorama import Fore
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from tabulate import tabulate

logger = logging.getLogger("craigslist")


class PostingStatus(str, Enum):
    ACTIVE = "Active"
    DELETED = "Deleted"
    EXPIRED = "Expired"
    INVALID = "Invalid"

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

    @property
    def table_color(self):
        if self == PostingStatus.ACTIVE:
            return Fore.LIGHTGREEN_EX
        elif self == PostingStatus.DELETED:
            return Fore.LIGHTBLUE_EX
        elif self == PostingStatus.EXPIRED:
            return Fore.LIGHTMAGENTA_EX
        else:
            return Fore.LIGHTRED_EX


class PostingNotFoundError(Exception):
    def __init__(self, id):
        message = f"Unable to find posting with id {id}"
        super().__init__(message)


class Posting:
    def __init__(self, id):
        self._id = id
        self._price = ""
        self._status = PostingStatus.INVALID
        self._title = ""
        self._post_datetime = ""
        self._update_datetime = ""

    @classmethod
    def from_craigslist(cls, browser, id):
        posting = cls(id)
        posting._parse_posting(browser)
        return posting

    def renew(self, browser):
        if self._status != PostingStatus.ACTIVE:
            return False

        try:
            renew_btn = browser.find_element(
                By.XPATH, "//input[@value='Renew this Posting']"
            )
            renew_btn.click()
        except NoSuchElementException:
            return False

        posting_infos = browser.find_element(
            By.XPATH, "//div[contains(@class, 'postinginfos')]"
        )
        update_datetime = posting_infos.find_element(
            By.XPATH, "(.//time)[2]"
        ).get_attribute("datetime")
        self._update_datetime = datetime.strptime(
            update_datetime, "%Y-%m-%dT%H:%M:%S%z"
        ).astimezone(timezone.utc)

        return True

    def repost(self, browser):
        if self.status != PostingStatus.EXPIRED:
            return None

        try:
            repost_btn = browser.find_element(By.CLASS_NAME, "managebtn")
            repost_btn.click()

            submit_btn = browser.find_element(
                By.XPATH, "//button[contains(@class, 'submit-button')]"
            )
            submit_btn.click()

            draft_warning = browser.find_element(By.CLASS_NAME, "draft_warning")
            publish_btn = draft_warning.find_element(By.TAG_NAME, "button")
            publish_btn.click()

            posting_link = browser.find_element(By.LINK_TEXT, "Manage your post")
            posting_url = posting_link.get_attribute("href")
            posting_id = posting_url[(posting_url.rfind("/") + 1) :]

            prev_posting_id = self._id
            self._id = posting_id
            self._parse_posting(browser)

            return prev_posting_id
        except NoSuchElementException:
            return None

    @property
    def id(self):
        return self._id

    @property
    def price(self):
        return self._price

    @property
    def status(self):
        return self._status

    @property
    def title(self):
        return self._title

    @property
    def post_datetime(self):
        return self._post_datetime

    @property
    def update_datetime(self):
        return self._update_datetime

    def _parse_posting(self, browser):
        browser.get(f"https://post.craigslist.org/manage/{self._id}")

        path = browser.find_element(By.CLASS_NAME, "breadcrumbs").text
        if path == "Page Not Found":
            raise PostingNotFoundError(id)

        manage_status = browser.find_element(By.CLASS_NAME, "managestatus")
        color = manage_status.value_of_css_property("background-color")
        self._status = PostingStatus.from_posting_status_color(color)

        posting_title = browser.find_element(
            By.XPATH, "//span[contains(@class, 'postingtitletext')]"
        )
        self._title = posting_title.find_element(By.ID, "titletextonly").text
        self._price = posting_title.find_element(By.CLASS_NAME, "price").text

        posting_infos = browser.find_element(
            By.XPATH, "//div[contains(@class, 'postinginfos')]"
        )

        post_datetime = posting_infos.find_element(
            By.XPATH, "(.//time)[1]"
        ).get_attribute("datetime")
        self._post_datetime = datetime.strptime(
            post_datetime, "%Y-%m-%dT%H:%M:%S%z"
        ).astimezone(timezone.utc)

        try:
            update_datetime = posting_infos.find_element(
                By.XPATH, "(.//time)[2]"
            ).get_attribute("datetime")
            self._update_datetime = datetime.strptime(
                update_datetime, "%Y-%m-%dT%H:%M:%S%z"
            ).astimezone(timezone.utc)
        except NoSuchElementException:
            self._update_datetime = None


# TODO add a timezone here
class PostingsSummary:
    def __init__(self):
        self._invalid_posting_ids = []
        self._postings = {}

    def add_posting(self, posting):
        self._postings[posting.id] = posting

    def __str__(self):
        posting_headers = [
            "id",
            "status",
            "title",
            "price",
            "post date (UTC)",
            "update date (UTC)",
        ]
        posting_data = []
        sorted_postings = sorted(
            self._postings.values(), key=lambda p: (p.status, p.id)
        )

        for posting in sorted_postings:
            color = posting.status.table_color
            datum = [
                color + posting.id,
                color + posting.status,
                color + (posting.title or "-"),
                color + (posting.price or "-"),
                color + (str(posting.post_datetime) or "-"),
                color + (str(posting.update_datetime) or "-"),
            ]
            posting_data.append(datum)

        posting_table = tabulate(posting_data, headers=posting_headers)

        return f"{posting_table}{Fore.RESET}"


def login(browser, config):
    try:
        logging.debug("Logging into Craigslist...")
        browser.get("https://accounts.craigslist.org/login")
        browser.find_element(By.ID, "inputEmailHandle").send_keys(config["email"])
        browser.find_element(By.ID, "inputPassword").send_keys(config["password"])
        browser.find_element(By.ID, "login").click()
        logging.info("Logged into Craigslist")
    except Exception:
        logging.exception("Unable to log into Craigslist")
        return False

    return True


def logout(browser):
    try:
        logging.debug("Logging out of Craigslist...")
        browser.get("https://accounts.craigslist.org/login/home")
        header = browser.find_element(By.CLASS_NAME, "account-header")
        header.find_element(By.XPATH, ".//a[text()='log out']").click()
        logging.info("Logged out of Craigslist")
    except Exception:
        logging.exception("Unable to log out of Craigslist")


def manage_postings(browser, postings):
    ids = []
    summary = PostingsSummary()
    for id in postings["ids"]:
        try:
            logging.debug(f"Relisting Craigslist posting '{id}'...")
            posting = Posting.from_craigslist(browser, id)
            if posting.status == PostingStatus.ACTIVE:
                posting.renew(browser)
            elif posting.status == PostingStatus.EXPIRED:
                posting.repost(browser)

            id = posting.id
            logging.info(f"Relisted Craigslist posting '{id}")

        except PostingNotFoundError:
            logging.exception(f"Unable to find Craigslist posting '{id}'")
            posting = Posting(id)
        except NoSuchElementException as e:
            logging.exception(
                f"Unable to find an element for Craigslist posting '{id}'"
            )
            posting = Posting(id)
        except Exception as e:
            logging.exception(f"Unable to relist Craigslist posting '{id}'")
            posting = Posting(id)

        ids.append(id)
        summary.add_posting(posting)

    postings["ids"] = sorted(ids)
    logging.info(f"Craigslist postings summary\n{summary}")


def relist(browser, config):
    if login(browser, config["credentials"]):
        manage_postings(browser, config["postings"])
        logout(browser)


# UNUSED
"""
def gather_active_postings(browser):
    URL = (
        "https://accounts.craigslist.org/login/home?filter_active=active&filter_page={}"
    )

    page = 1
    posting_ids = set()
    while True:
        browser.get(URL.format(page))

        try:
            rows = browser.find_elements(By.CLASS_NAME, "posting-row")
        except NoSuchElementException:
            break

        if not rows:
            break

        for row in rows:
            try:
                posting_id = row.find_element(By.CLASS_NAME, "postingID").text
                posting_ids.add(posting_id)
            except NoSuchElementException:
                continue

        page += 1

    return posting_ids
"""
