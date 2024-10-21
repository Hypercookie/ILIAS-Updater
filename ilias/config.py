import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


def normalise(url):
    return url if urlparse(url).path else url + "/"


BASE_URL = normalise(os.getenv("URL"))
