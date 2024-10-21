import os
import requests
import json

from config import BASE_URL


class Auth:
    def __init__(self):
        self.session = self.get_authed_session()

    def get_authed_session(self):
        url = f"{BASE_URL}ilias.php?baseClass=ilstartupgui&cmd=post&fallbackCmd=doStandardAuthentication&lang=de&client_id=ILIASKONSTANZ"

        payload = {'username': os.getenv("USERNAME"),
                   'password': os.getenv("PASSWORD"),
                   'cmd[doStandardAuthentication]': 'Anmelden'}

        with requests.Session() as s:
            s.request("POST", url, data=payload, )
            return s


INSTANCE = Auth()
