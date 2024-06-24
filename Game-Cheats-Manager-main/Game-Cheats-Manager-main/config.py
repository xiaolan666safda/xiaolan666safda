import gettext
import json
import locale
import os
import shutil
import sys
import tempfile

import pinyin
import polib
from PyQt6.QtWidgets import QMessageBox
ts = None


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        full_path = os.path.join(sys._MEIPASS, relative_path)
    else:
        full_path = os.path.join(os.path.abspath("."), relative_path)

    if not os.path.exists(full_path):
        resource_name = os.path.basename(relative_path)
        formatted_message = tr("Couldn't find {missing_resource}. Please try reinstalling the application.").format(
            missing_resource=resource_name)
        QMessageBox.critical(
            None, tr("Missing resource file"), formatted_message)
        sys.exit(1)

    return full_path


def apply_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def load_settings():
    locale.setlocale(locale.LC_ALL, '')
    system_locale = locale.getlocale()[0]
    locale_mapping = {
        "English_United States": "en_US",
        "Chinese (Simplified)_China": "zh_CN",
        "Chinese (Simplified)_Hong Kong SAR": "zh_CN",
        "Chinese (Simplified)_Macao SAR": "zh_CN",
        "Chinese (Simplified)_Singapore": "zh_CN",
        "Chinese (Traditional)_Hong Kong SAR": "zh_TW",
        "Chinese (Traditional)_Macao SAR": "zh_TW",
        "Chinese (Traditional)_Taiwan": "zh_TW"
    }
    app_locale = locale_mapping.get(system_locale, 'en_US')

    default_settings = {
        "downloadPath": os.path.join(os.environ["APPDATA"], "GCM Trainers"),
        "language": app_locale,
        "theme": "black",
        "enSearchResults": False,
        "autoUpdateDatabase": True,
        "autoUpdate": True,
        "WeModPath": os.path.join(os.environ["LOCALAPPDATA"], "WeMod"),
        "autoStart": False,
        "showWarning": True,
        "downloadServer": "intl",
        "removeBgMusic": True,
    }

    try:
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
    except Exception as e:
        print("Error loading settings json" + str(e))
        settings = default_settings

    for key, value in default_settings.items():
        settings.setdefault(key, value)

    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

    return settings


def get_translator():
    if not hasattr(sys, 'frozen'):
        for root, dirs, files in os.walk(resource_path("locale/")):
            for file in files:
                if file.endswith(".po"):
                    po = polib.pofile(os.path.join(root, file))
                    po.save_as_mofile(os.path.join(
                        root, os.path.splitext(file)[0] + ".mo"))

    lang = settings["language"]
    gettext.bindtextdomain("Game Cheats Manager",
                           resource_path("locale/"))
    gettext.textdomain("Game Cheats Manager")
    lang = gettext.translation(
        "Game Cheats Manager", resource_path("locale/"), languages=[lang])
    lang.install()
    return lang.gettext


def is_chinese(text):
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


def sort_trainers_key(name):
    if is_chinese(name):
        return pinyin.get(name, format="strip", delimiter=" ")
    return name


def ensure_trainer_details_exist():
    dst = os.path.join(DATABASE_PATH, "xgqdetail.json")
    if not os.path.exists(dst):
        shutil.copyfile(resource_path("dependency/xgqdetail.json"), dst)


setting_path = os.path.join(
    os.environ["APPDATA"], "GCM Settings/")
os.makedirs(setting_path, exist_ok=True)

SETTINGS_FILE = os.path.join(setting_path, "settings.json")
DATABASE_PATH = os.path.join(setting_path, "db")
os.makedirs(DATABASE_PATH, exist_ok=True)
DOWNLOAD_TEMP_DIR = os.path.join(tempfile.gettempdir(), "GameCheatsManagerTemp", "download")
VERSION_TEMP_DIR = os.path.join(tempfile.gettempdir(), "GameCheatsManagerTemp", "version")
WEMOD_TEMP_DIR = os.path.join(tempfile.gettempdir(), "GameCheatsManagerTemp", "wemod")

settings = load_settings()
tr = get_translator()

ensure_trainer_details_exist()
resourceHacker_path = resource_path("dependency/ResourceHacker.exe")
unzip_path = resource_path("dependency/7z/7z.exe")
binmay_path = resource_path("dependency/binmay.exe")
emptyMidi_path = resource_path("dependency/TrainerBGM.mid")

language_options = {
    "English (US)": "en_US",
    "简体中文": "zh_CN",
    "繁體中文": "zh_TW"
}

theme_options = {
    tr("Black"): "black",
    tr("white"): "white"
}

server_options = {
    tr("International"): "intl",
    tr("China"): "china"
}
