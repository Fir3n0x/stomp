"""
browser_config.py - Browser configuration (seeds, paths, location codes)
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class BrowserConfig:
    name: str
    seed: bytes
    default_location: int
    preferences_path: str
    secure_preferences_path: str
    proc_name: str
    profile_path: str 


class BrowserConfigurator:
    # Seeds 
    CHROME_SEED = (
        b"\xe7H\xf36\xd8^\xa5\xf9\xdc\xdf%\xd8\xf3G\xa6[L\xdffv\x00\xf0-"
        b"\xf6rJ*\xf1\x8a!-&\xb7\x88\xa2P\x86\x91\x0c\xf3\xa9\x03\x13ihq"
        b"\xf3\xdc\x05\x8270\xc9\x1d\xf8\xba\\O\xd9\xc8\x84\xb5\x05\xa8"
    )
    EDGE_SEED: bytes = b""
    BRAVE_SEED: bytes = b""
    VIVALDI_SEED: bytes = b""

    # Registry
    @staticmethod
    def get_browser_configs() -> Dict[str, BrowserConfig]:
        return {
            "chrome": BrowserConfig(
                name="Chrome",
                seed=BrowserConfigurator.CHROME_SEED,
                default_location=4,
                preferences_path=r"AppData\Local\Google\Chrome\User Data\Default\Preferences",
                secure_preferences_path=r"AppData\Local\Google\Chrome\User Data\Default\Secure Preferences",
                proc_name="chrome.exe",
                profile_path=r"Google\Chrome\User Data\Default",
            ),
            "edge": BrowserConfig(
                name="Microsoft Edge",
                seed=BrowserConfigurator.EDGE_SEED,
                default_location=4,
                preferences_path=r"AppData\Local\Microsoft\Edge\User Data\Default\Preferences",
                secure_preferences_path=r"AppData\Local\Microsoft\Edge\User Data\Default\Secure Preferences",
                proc_name="msedge.exe",
                profile_path=r"Microsoft\Edge\User Data\Default",
            ),
            "brave": BrowserConfig(
                name="Brave",
                seed=BrowserConfigurator.BRAVE_SEED,
                default_location=4,
                preferences_path=r"AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Preferences",
                secure_preferences_path=r"AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Secure Preferences",
                proc_name="brave.exe",
                profile_path=r"BraveSoftware\Brave-Browser\User Data\Default",
            ),
            "vivaldi": BrowserConfig(
                name="Vivaldi",
                seed=BrowserConfigurator.VIVALDI_SEED,
                default_location=4,
                preferences_path=r"AppData\Local\Vivaldi\User Data\Default\Preferences",
                secure_preferences_path=r"AppData\Local\Vivaldi\User Data\Default\Secure Preferences",
                proc_name="vivaldi.exe",
                profile_path=r"Vivaldi\User Data\Default",
            ),
        }