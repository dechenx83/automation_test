import json
import os
SETTING = None


def _load_setting(setting):
    global SETTING
    with open(setting) as file:
        SETTING = json.load(file)


_load_setting(os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json"))
