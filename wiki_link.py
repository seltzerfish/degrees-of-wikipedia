from bs4 import BeautifulSoup
import urllib.request
from pprint import pprint
import json
from pathlib import Path
from queue import Queue
import re

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
    return links


def load_cache():
    table_file = Path(CACHE_FILE)
    if table_file.exists():
        return json.load(open(CACHE_FILE))
    return dict()


def write_cache(table):
    with open(CACHE_FILE, 'w') as file:
        file.write(json.dumps(table))

# def load_table():
#     table_file = Path("table.json")
#     if table_file.exists():
#         return json.load(open("table.json"))
#     return dict()


# def write_table(table):
#     with open("table.json", 'w') as file:
#         file.write(json.dumps(table))


def build_path(current):
    path = []
    while current.parent:
        path.append(current.title)
        current = current.parent
    path.append(current.title)
    path.reverse()
    return path


def relate(start, destination):
    visited = set()
    cache = load_cache()
    q = Queue()
    # add initial state with no parent
    q.put(Page(strip_url(start), strip_url(start), None))
    visited.add(strip_url(start))
    goal_suffix = strip_url(destination)
    while True:
        page = q.get()
        if page.url in cache:
            print("*** ", end="")
            links = cache[page.url]
        else:
            anchor_tags = get_links_from_page(
                "https://en.wikipedia.org/wiki/" + page.url)
            links = [(a.get('href')[6:], a.contents[0]) for a in anchor_tags]
            # cache[page.url] = links
        print(build_path(page))
        for url, title in links:
            if url not in visited:
                if url == goal_suffix:
                    # write_cache(cache)
                    p = build_path(page)
                    p.append(title)
                    return p
                visited.add(url)
                q.put(Page(url, title, page))


if __name__ == "__main__":
    print(" -> ".join(relate("https://en.wikipedia.org/wiki/Jasper_High_School_(Alabama)",
                             "https://en.wikipedia.org/wiki/DYWP")))
