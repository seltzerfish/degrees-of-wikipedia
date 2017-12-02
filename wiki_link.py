import urllib
import lxml.html
import re
from Queue import Queue
import json
from pathlib import Path
from time import time

class State:
    def __init__(self, title, link, parent):
        self.title = title
        self.link = link
        self.parent = parent

    def __hash__(self):
        return hash(self.title)

    def __eq__(self, other):
        if self.title == other.title:
            return True
        return False

def load_lookup_table():
    table_file = Path("cache.txt")
    if table_file.exists():
        return json.load(open('cache.txt'))
    return dict()

def write_lookup_table(table):
    with open('cache.txt', 'w') as file:
        file.write(json.dumps(table))

def get_title(url):
    return re.search('\/([^\/]+)\/?$', url).group(1)



def find(start_url, hard_mode=False):
    try: 
        s_time = time()
        q = Queue()
        explored = set()
        cache = load_lookup_table()
        
        start_state = State(get_title(start_url), start_url, None)
        q.put(start_state)
        explored.add(get_title(start_url))
        end_title = "/wiki/DYWP"

        if hard_mode:
            countries = []
            with open("countries.txt", 'r') as f:
                countries = f.read().splitlines()

        for x in range(100000):
            s = q.get()
            print(s.title)
            page_loaded = False
            if s.title in cache:
                links = cache[s.title]
            else:
                connection = urllib.urlopen(s.link)
                dom =  lxml.html.fromstring(connection.read())
                links = dom.xpath('//a/@href')
                page_loaded = True
                cache[s.title] = []
            for link in links:
                if (link[:6] == "/wiki/" and ":" not in link and link[6] != "/"):
                    if page_loaded:
                        cache[s.title].append(link)
                    if hard_mode and get_title(link) in countries:
                        continue
                    if get_title(link) not in explored:
                        explored.add(get_title(link))
                        if link == end_title:
                            with open("time.txt", "a") as f:
                                f.write(str(time() - s_time) + "\n")
                            print("\n******\n")
                            path = s.title + " -> " + get_title(link)
                            while s.parent:
                                path = s.parent.title + " -> " + path
                                s = s.parent
                            if path.count("->") > 3:
                                with open("long.txt", "a") as f:
                                    f.write(path + "\n")
                            print(path)
                            print(len(cache))
                            write_lookup_table(cache)
                            return None
                        q.put(State(get_title(link), "https://en.wikipedia.org" + link, s))
    except KeyboardInterrupt:
        write_lookup_table(cache)


if __name__ == "__main__":
    start_url = raw_input("start url: ")
    find(start_url)