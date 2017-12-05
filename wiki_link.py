from bs4 import BeautifulSoup
import urllib.request
import json
from pathlib import Path
from queue import Queue
import re
from time import time
import sys

CACHE_FILE = "cache.json"


class Page:
    def __init__(self, url, title, parent):
        self.url = url
        self.title = title
        self.parent = parent


def strip_url(url):
    return re.search("\/wiki\/(.+)$", url).group(1)


def link_is_valid(link):
    if link.get('href') and link.get('href')[:6] == "/wiki/":
        if (link.contents and str(link.contents[0])[0] != "<"
                and ":" not in link.get('href')):
            return True
    return False


def get_links_from_page(url):
    connection = urllib.request.urlopen(url)
    links = []
    soup = BeautifulSoup(connection, "lxml").find(
        "div", {"id": "mw-content-text"})
    # exlude "references" section
    for div in soup.find_all("div", {'class': 'reflist'}):
        div.decompose()
    for div in soup.find_all("div", {'class': 'navbox'}):
        div.decompose()
    for div in soup.find_all("div", {'class': 'refbegin'}):
        div.decompose()
    for paragraph in soup.findAll('p'):
        for link in paragraph.findAll('a'):
            if link_is_valid(link):
                links.append(link)
    for list in soup.findAll('ul'):
        for link in list.findAll('a'):
            if link_is_valid(link):
                links.append(link)
    return [(a.get('href')[6:], a.contents[0]) for a in links]


def load_cache():
    print("Loading cache... ", end="")
    sys.stdout.flush()
    start_time = time()
    table_file = Path(CACHE_FILE)
    if table_file.exists():
        cache = json.load(open(CACHE_FILE))
    else: cache = dict()
    print("Cache loaded in {:.2f} seconds.".format(time() - start_time))
    return cache


def write_cache(table):
    print("Updating cache... ", end="")
    sys.stdout.flush()
    with open(CACHE_FILE, 'w') as file:
        file.write(json.dumps(table))
    print("Done")


def build_path(current):
    path = []
    while current.parent:
        path.append(current.title)
        current = current.parent
    path.append(current.title)
    path.reverse()
    return path


def relate(start, destination, grow_cache=False):
    visited = set()
    cache = load_cache()
    q = Queue()
    # add initial state with no parent
    q.put(Page(strip_url(start), strip_url(start), None))
    goal_suffix = strip_url(destination)
    while True:
        page = q.get()
        if page.url in cache:
            print("* ", end="")
            links = cache[page.url]
        else:
            links = get_links_from_page(
                "https://en.wikipedia.org/wiki/" + page.url)
            if grow_cache:
                cache[page.url] = links
        print(" -> ".join(build_path(page)))
        for url, title in links:
            if url not in visited:
                if url == goal_suffix:
                    if grow_cache: write_cache(cache)
                    p = build_path(page)
                    p.append(title)
                    return p
                visited.add(url)
                q.put(Page(url, title, page))


if __name__ == "__main__":
    start_link = input("starting page: ")
    if input("custom destination page? [Y/N]: ").strip().upper() == "Y":
        dest_link = input("destination page: ")
    else:
        dest_link = "https://en.wikipedia.org/wiki/Adolf_Hitler"
    grow_cache = True if input(
        "grow cache? [Y/N]: ").strip().upper() == "Y" else False
    result = relate(start_link, dest_link, grow_cache=grow_cache)
    print("\n****** Solution Found ******")
    print(" -> ".join(result))
