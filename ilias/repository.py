import os
import urllib
import re
from config import BASE_URL
from auth import INSTANCE
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs


def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0].replace('"', "")


def find_header_from_element(element):
    # Search upwards for the parent with class 'ilContainerBlock'
    parent_block = element.find_parent(class_='ilContainerBlock')

    if parent_block:
        # Search downwards for the element with class 'ilContainerBlockHeader'
        header_element = parent_block.find(class_='ilContainerBlockHeader')
        if header_element:
            return header_element.text.strip()  # Return the text content of the header
    return None  # Return None if not found


class Repository:
    def __init__(self, repo_id: int, name: str):
        self.repo_id = repo_id
        self.name = name
        self.url = f"{BASE_URL}ilias.php?baseClass=ilrepositorygui&ref_id={self.repo_id}"
        self.content = None

    def get_content(self):
        if not self.content:
            self.content = BeautifulSoup(INSTANCE.session.get(self.url).text, features="html.parser")
        return self.content

    def discover_items(self):
        content = self.get_content()
        items = content.find_all(class_="il_ContainerListItem")
        return items

    def discover_links(self):
        items = self.discover_items()
        for item in items:
            a = item.findNext("a", class_="il_ContainerItemTitle")
            if a:
                yield a

    def discover_direct_links(self):
        for link in self.discover_links():
            if "calldirectlink" in link["href"]:
                header_text = find_header_from_element(link)
                r = INSTANCE.session.get(f"{BASE_URL}{link["href"]}")
                if r.history:
                    for req in r.history:
                        if not req.url.startswith(BASE_URL) or len(r.history) == 1:
                            if header_text and header_text != "Inhalt":
                                yield {"name": link.decode_contents(), "url": req.url, "path": header_text}
                            else:
                                yield {"name": link.decode_contents(), "url": req.url}
                            break

    def discover_files(self):
        for link in self.discover_links():
            if "target=file" in link["href"]:
                header_text = find_header_from_element(link)
                if header_text and header_text != "Inhalt":
                    yield {"name": link.decode_contents(), "url": link["href"], "path": header_text}
                else:
                    yield {"name": link.decode_contents(), "url": link["href"]}

    def discover_sub_repos(self):
        for link in self.discover_links():
            if "cmd=view" in link["href"]:
                url = urlparse(f"{BASE_URL}{link["href"]}")
                captured_value = parse_qs(url.query)['ref_id'][0]
                if captured_value:
                    # Is sub-repo
                    yield Repository(int(captured_value), link.decode_contents())

    def write_files(self, base_path: str = "."+os.sep):

        for f in self.discover_files():
            p = base_path
            if "path" in f:
                p = p + os.sep + f["path"] + os.sep
            os.makedirs(p, exist_ok=True)
            r = INSTANCE.session.get(f["url"])
            filename = get_filename_from_cd(r.headers.get('content-disposition'))
            print(f"Writing {p + filename}")
            with open(p + filename, 'wb') as f_write:
                f_write.write(r.content)
        for l in self.discover_direct_links():
            p = base_path
            if "path" in l:
                p = p + os.sep + l["path"] + os.sep
            print(f"Writing {p + l['name'] + ".url"}")
            os.makedirs(p, exist_ok=True)
            with open(p + l['name'] + ".url", 'w') as f_write:
                f_write.write(l['url'])
        for sub_repo in self.discover_sub_repos():
            sub_repo.write_files(base_path + sub_repo.name + os.sep)
