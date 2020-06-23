from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import getpass


def login(driver, username, password, two_factor):
    driver.get("https://remoteaccess.bham.ac.uk")

    driver.find_element_by_link_text("Click here to continue").click()
    driver.find_element_by_link_text("Click here to continue").click()

    driver.find_element_by_id("input_1").send_keys(username)
    driver.find_element_by_id("input_2").send_keys(password)
    driver.find_element_by_id("input_3").send_keys(two_factor)
    driver.find_element_by_xpath('//input[@type="submit"]').click()
    assert driver.title == "F5 Dynamic Webtop"


def main():
    username = input("username: ")
    password = getpass.getpass("password: ")
    two_factor = input("2fa: ")

    driver = webdriver.Chrome()
    login(driver, username, password, two_factor)

    # Launch VPN
    driver.find_element_by_id("/Common/UoB_Research_NA").click()


if __name__ == "__main__":
    main()

