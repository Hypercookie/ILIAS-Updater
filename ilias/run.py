import os

from repository import Repository

r = Repository(int(os.getenv("REF_ID")), "root")
r.write_files()