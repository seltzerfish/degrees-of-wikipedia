from bs4 import BeautifulSoup
import urllib.request
import json
from pathlib import Path
from queue import Queue
import re
from time import time, sleep
from threading import Thread
import sys
from webdriver import *

CACHE_FILE = "cache.json"



class Page:
    def __init__(self, url, title, parent, depth=0):
        self.url = url
        self.title = title
        self.parent = parent
        self.depth = depth


def strip_url(url):
    return re.search("\/wiki\/(.+)$", url).group(1)


def link_is_valid(link):
    if link.get('href') and link.get('href')[:6] == "/wiki/":
        if (link.contents and str(link.contents[0])[0] != "<"
                and ":" not in link.get('href')):
            return True
    return False

def get_connection(page, connections):
    connections.append((page, urllib.request.urlopen("https://en.wikipedia.org/wiki/" + page.url)))

def get_links_from_page(page, connection):
    print(" -> ".join([r[1] for r in build_path(page)]))
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
        path.append((current.url, current.title))
        current = current.parent
    path.append((current.url, current.title))
    path.reverse()
    return path

def check_links(links, visited, queue, goal_suffix, page, grow_cache):
    for url, title in links:
        if url not in visited:
            if url == goal_suffix:
                if grow_cache: write_cache(cache)
                p = build_path(page)
                p.append((url, title))
                return p
            visited.add(url)
            queue.put(Page(url, title, page, page.depth + 1))
    return None

def relate(start, destination, cache, grow_cache=False):
    visited = set()
    q = Queue()
    # add initial state with no parent
    q.put(Page(strip_url(start), strip_url(start), None))
    goal_suffix = strip_url(destination)
    current_depth = 0
    web_links = []
    while True:
        if current_depth > 7:
            print("depth too high")

            return "None"
        if not q.empty():
            page = q.get()

        if q.empty() or page.depth > current_depth:
            if len(web_links) > 2000:
                print("too many web links ({} at level {}) ".format(len(web_links), current_depth))
                if grow_cache:
                    write_cache(cache)
                return None
            print("checking {} links on level {}".format(len(web_links), current_depth))
            if not q.empty():
                current_depth += 1
            
            while web_links:
                connections = []
                threads = []
                for i in range(100):
                    if web_links:
                        t = Thread(target=get_connection, args=(web_links.pop(), connections))
                        threads.append(t)
                        t.start()
                for i in range(len(threads)):
                    threads[i].join()
                for connection in connections:
                    links = get_links_from_page(connection[0], connection[1])
                    cache[connection[0].url] = links
                    result = check_links(links, visited, q, goal_suffix, connection[0], grow_cache)
                    if result: return result
                if web_links: print("{} links left to check...".format(len(web_links)))
            
            web_links = []

        if page.url in cache:
            print("(cached) " + " -> ".join([r[1] for r in build_path(page)]))
            links = cache[page.url]
        else:
            # print(" -> ".join(build_path(page)))
            web_links.append(page)
            continue
        result = check_links(links, visited, q, goal_suffix, page, grow_cache)
        if result: return result


if __name__ == "__main__":
    cache = load_cache()
    from os import system
    import requests
    while True:
        try:
            start_link = input("starting page: ")
            dest_link = input("destination page: ")
            result = relate(start_link, dest_link, cache, grow_cache=False)
            if result:
                print("\n****** Solution Found ******")
                print(" -> ".join([r[1] for r in result]))
                if input("show result? [y/n] ").upper().strip() == "Y":
                    show_results(result)
                    # pass
            else:
                print("Solution not found :(")
        except (KeyboardInterrupt) as e:
            print(e)
            write_cache(cache)
            break
