from selenium import webdriver
from selenium.webdriver.support.ui import Select


class InputHandler:

    @staticmethod
    def fill_text_field(driver: webdriver, xpath: str, value):

        if value is None:
            return
        value = str(value)
        input_field = driver.find_element_by_xpath(xpath)
        input_field.send_keys(value)

    @staticmethod
    def fill_custom_dropdown_list(driver: webdriver, xpath: str, value):

        # todo: check that value is within the possible values
        if value is None:
            return
        value = str(value)
        element = driver.find_element_by_xpath(xpath)
        select = Select(element)
        select.select_by_visible_text(value)
