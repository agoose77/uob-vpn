import pathlib
import re
import subprocess
from typing import Sequence
from urllib.request import urlopen

import traitlets.config
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

VERSION_NUMBER_PATTERN = r"(\d+)\.(\d+)\.(\d+)\.(\d+)"


class VersionMismatch(Exception):
    pass


def get_chrome_version() -> Sequence[str]:
    result = (
        subprocess.run(["google-chrome", "--version"], capture_output=True, check=True)
        .stdout.decode()
        .strip()
    )
    return re.search(VERSION_NUMBER_PATTERN, result).groups()


def get_chromedriver_version() -> Sequence[str]:
    result = (
        subprocess.run(["chromedriver", "--version"], capture_output=True, check=True)
        .stdout.decode()
        .strip()
    )
    return re.search(VERSION_NUMBER_PATTERN, result).groups()


def get_required_chromedriver_version(chrome_version: Sequence[str]) -> Sequence[str]:
    version_string = ".".join(chrome_version[:3])
    with urlopen(
        f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version_string}"
    ) as response:
        return re.search(VERSION_NUMBER_PATTERN, response.read().decode()).groups()


_VERSION_MISMATCH_ERROR = """
Version mismatch between chromedriver version {version} and Chrome required version {required_version}.
Download the correct chromedriver from https://chromedriver.storage.googleapis.com/{required_version_string}/chromedriver_linux64.zip
"""


class VPNApp(traitlets.config.Application):
    name = "vpn"
    description = "UoB VPN launcher"

    aliases = {
        "username": "VPNApp.username",
        "password": "VPNApp.password",
        "2fa": "VPNApp.two_factor",
        "config": "VPNApp.config_file_path",
    }
    flags = {"full": ({"VPNApp": {"use_full_vpn": True}}, "use full VPN")}

    config_file_path = traitlets.Unicode(
        config=True,
        help="Full path of a config file.",
    )
    username = traitlets.Unicode(config=True, help="username")
    password = traitlets.Unicode(config=True, help="password")
    two_factor = traitlets.Unicode(config=True, help="2fa code")
    use_full_vpn = traitlets.Bool(
        config=True,
        help="Use the full VPN (for all connections).",
    )
    wait_duration = traitlets.Float(
        config=True, help="delay before page load is considered a failure"
    )

    def _load_config_file(self):
        if (path := pathlib.Path(self.config_file_path)).exists() and path.is_file():
            self.load_config_file(path.name, str(path.parent))

        else:
            self.load_config_file(
                f"{self.name}_config",
                [str(pathlib.Path.cwd()), str(pathlib.Path.home() / ".config")],
            )

    @traitlets.config.catch_config_error
    def initialize(self, argv=None):
        super().initialize(argv)
        self._load_config_file()

    def start(self):
        version = get_chromedriver_version()
        required_version = get_required_chromedriver_version(get_chrome_version())

        if version != required_version:
            raise VersionMismatch(
                _VERSION_MISMATCH_ERROR.format(
                    version=version,
                    required_version=required_version,
                    required_version_string=".".join(required_version),
                )
            )

        # Input validation
        if not (username := self.username):
            raise ValueError("Please specify non-empty username string")
        if not (password := self.password):
            raise ValueError("Please specify non-empty password string")
        if not (two_factor := self.two_factor):
            raise ValueError("Please specify non-empty two factor string")

        # Create chromedriver
        driver = webdriver.Chrome()
        driver.get("https://remoteaccess.bham.ac.uk")

        while True:
            try:
                driver.find_element_by_link_text("Click here to continue").click()
            except NoSuchElementException:
                break

        driver.find_element_by_id("input_1").send_keys(username)
        driver.find_element_by_id("input_2").send_keys(password)
        driver.find_element_by_id("input_3").send_keys(two_factor)

        if self.use_full_vpn:
            driver.find_element_by_id("input_4").click()

        driver.find_element_by_xpath('//input[@type="submit"]').click()

        if driver.page_source.find("username or password is not correct") != -1:
            raise ValueError("Username, password, or 2fa was incorrect")

        if driver.page_source.find("session could not be established") != -1:
            raise RuntimeError("An error occurred, re-try with new 2fa?")

        # Launch VPN
        required_id = (
            "/Common/UoB_Research_full_NA"
            if self.use_full_vpn
            else "/Common/UoB_Research_NA"
        )
        launch_elem = WebDriverWait(driver, self.wait_duration).until(
            expected_conditions.presence_of_element_located((By.ID, required_id))
        )
        launch_elem.click()
        input()

        return 0


if __name__ == "__main__":
    VPNApp.launch_instance()
