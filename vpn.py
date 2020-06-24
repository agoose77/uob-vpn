import getpass
import re
import shutil
import zipfile
from pathlib import Path
from subprocess import run
from typing import Sequence
from urllib.request import urlopen, urlretrieve

from selenium import webdriver

VERSION_NUMBER_PATTERN = r"(\d+)\.(\d+)\.(\d+)\.(\d+)"


class VersionMismatch(Exception):
    pass


def get_chrome_version() -> Sequence[str]:
    result = run(['google-chrome', '--version'], capture_output=True, check=True).stdout.decode().strip()
    return re.search(VERSION_NUMBER_PATTERN, result).groups()


def get_chromedriver_version() -> Sequence[str]:
    result = run(['chromedriver', '--version'], capture_output=True, check=True).stdout.decode().strip()
    return re.search(VERSION_NUMBER_PATTERN, result).groups()


def get_required_chromedriver_version(chrome_version: Sequence[str]) -> Sequence[str]:
    version_string = '.'.join(chrome_version[:3])
    with urlopen(f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version_string}") as response:
        return re.search(VERSION_NUMBER_PATTERN, response.read().decode()).groups()


def install_chromedriver(chromedriver_version: Sequence[str]):
    version_string = '.'.join(chromedriver_version)
    zip_path, headers = urlretrieve(
        f"https://chromedriver.storage.googleapis.com/{version_string}/chromedriver_linux64.zip"
    )

    # Extract zip
    install_path = Path.home() / ".local" / "bin" / "chromedriver"
    with zipfile.ZipFile(zip_path) as zip:
        zip.extract("chromedriver", install_path.parent)

    # Check we can find this installed chromedriver
    if Path(shutil.which("chromedriver")) != install_path:
        raise RuntimeError(f"newly installed chromedriver at {install_path} is not on system path ({shutil.which('chromedriver')})")


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

    chrome_version = get_chrome_version()
    try:
        if get_chromedriver_version() != get_required_chromedriver_version(chrome_version):
            raise VersionMismatch("Version mismatch for chromedriver and chrome")

    except (FileNotFoundError, VersionMismatch):
        required_chromedriver_version = get_required_chromedriver_version(chrome_version)
        install_chromedriver(required_chromedriver_version)

    # Create chromedriver
    driver = webdriver.Chrome()
    login(driver, username, password, two_factor)

    # Launch VPN
    driver.find_element_by_id("/Common/UoB_Research_NA").click()
    input()


if __name__ == "__main__":
    main()
