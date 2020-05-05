from selenium import webdriver
from datetime import datetime
import io
import os

from inputhandler import InputHandler
from utils.constants import *


class Account:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class Scraper:

    chrome_options = webdriver.ChromeOptions()

    def __init__(self, headless=True):
        if headless:
            self.chrome_options.add_argument('--headless')

        self.driver = webdriver.Chrome(executable_path="./utils/chromedriver.exe",
                                       chrome_options=self.chrome_options)
        self.driver.maximize_window()


class Schools48MarkScraper(Scraper):

    def __init__(self, account, headless=True):
        self.account = account
        self._is_logged_in = False
        super().__init__(headless=headless)

    def log_in(self):
        """
        Be careful that after logging in you are not at the same page as before
        :return:
        """
        account = self.account
        driver = self.driver
        if self._is_logged_in:
            return

        driver.get(LOGIN_PAGE)
        InputHandler.fill_text_field(driver, '//*[@id="username"]', account.username)
        InputHandler.fill_text_field(driver, '//*[@id="password"]', account.password)
        driver.find_element_by_xpath('//*[@id="password"]').submit()
        self._is_logged_in = True

    def get_marks_page(self):
        """
        # //*[@id="summary"]/ul/li/table/tbody/tr/td[1]/div[1]/table/tbody
        """
        today = datetime.today().strftime('%Y-%m-%d')
        name = f'./cache/marks_{today}.html'

        if os.path.exists(name):
            with io.open(name, "r", encoding="utf-8") as f:
                page_source = f.read()
            return page_source

        if not self._is_logged_in:
            self.log_in()

        self.driver.get(MARKS_PAGE)
        source = self.driver.page_source
        with io.open(name, "w", encoding="utf-8") as f:
            f.write(source)


if __name__ == '__main__':

    from parsers import School48Parser

    # ======= GET AN HTML FILE WITH THE LATEST MARKS ======= #
    try:
        # try to get the latest version of marks page
        account = Account(username, password)
        ms = Schools48MarkScraper(account, headless=True)
        ms.log_in()
        marks = ms.get_marks_page()
    except:
        # couldn't scrap data from the website, using cached version
        files = sorted(os.listdir('./cache/'))
        with io.open('./cache/' + files[-1], "r", encoding="utf-8") as f:
            marks = f.read()

    # ======= READ THE FILE AND UPDATE THE DATABASE ======= #
    parser = School48Parser(marks)
