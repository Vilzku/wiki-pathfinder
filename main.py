import xmlrpc.client
from dotenv import load_dotenv
import os
import threading
import time

load_dotenv()
WORKERS = int(os.environ.get("WORKERS", 10))
DEFAULT_PORT = int(os.environ.get("DEFAULT_PORT", "8000"))

workers = []

for i in range(WORKERS):
    try:
        worker = {
            "name": "worker{}".format(i + 1),
            "status": 0,
            "proxy": xmlrpc.client.ServerProxy(
                "http://localhost:" + str(DEFAULT_PORT + i)
            ),
        }
        workers.append(worker)
    except Exception as e:
        print(e)


class Node:
    def __init__(self, name):
        self.name = name
        self.linked_pages = []

    def __str__(self):
        return self.name

    def getName(self):
        return self.name

    def addLink(self, page):
        self.linked_pages.append(page)

    def getLinkedPages(self):
        return self.linked_pages

    def getLinks(self):
        return [x.getName() for x in self.linked_pages]

    def resetLinkedPages(self):
        self.linked_pages = []


searched_pages = []

# Traverse tree horizontally and find first empty page
def findNextPage(page):
    if page.getName() not in searched_pages:
        return page
    for child in page.getLinkedPages():
        if child.getName() not in searched_pages:
            return child
    for child in page.getLinkedPages():
        next_page = findNextPage(child)
        if next_page != None:
            return next_page


def findPath(root, end):
    path = [end]

    def findLink(node, link):
        if link in node.getLinks():
            return node.getName()
        for child in node.getLinkedPages():
            if link in child.getLinks():
                return child.getName()
        for child in node.getLinkedPages():
            next_link = findLink(child, link)
            if next_link != None:
                return next_link

    link = end
    while True:
        link = findLink(root, link)
        path.insert(0, link)
        if link == root.getName():
            break
    return path


def findWorker():
    should_loop = True
    while should_loop:
        should_loop = False
        for worker in workers:
            if worker["status"] == 0:
                return worker
            if worker["name"] == workers[-1]["name"]:
                should_loop = True


def getLinks(worker, page):
    try:
        worker["status"] = 1
        # print("getLinks", page, worker["name"])
        links = worker["proxy"].getLinks(page.getName())
        if links != False:
            for link in links:
                if (
                    link not in searched_pages
                    and "File:" not in link
                    and "Help:" not in link
                    and "Template:" not in link
                    and "Talk:" not in link
                    and "Template talk:" not in link
                    and "Wikipedia:" not in link
                    and "Category:" not in link
                ):
                    page.addLink(Node(link))
        else:
            raise Exception(
                "{} failed to get links for {}".format(worker["name"], page.getName())
            )
    except Exception as e:
        searched_pages.remove(page.getName())
        page.resetLinkedPages()
        print("Error:", e)
        # TODO: if cannot connect remove worker from list or idk do something
    finally:
        worker["status"] = 0
        return True


def checkIfPageExists(page_name):
    try:
        worker = findWorker()
        worker["status"] = 1
        links = worker["proxy"].getLinks(page_name)
        if links != False and len(links) > 0:
            return True
        else:
            return False
    except Exception as e:
        print(e)
    finally:
        worker["status"] = 0


def mainLoop(start, end):
    root = Node(start)
    while True:
        if end in searched_pages:
            return findPath(root, end)
        page = findNextPage(root)
        if page == None:
            continue
        searched_pages.append(page.getName())
        try:
            worker = findWorker()
            threading.Thread(
                target=getLinks,
                args=(
                    worker,
                    page,
                ),
            ).start()
        except Exception as e:
            print(e)


show_loading = True


def showLoading(start, end):
    bar = [
        " [=     ]",
        " [==    ]",
        " [ ==   ]",
        " [  ==  ]",
        " [   == ]",
        " [    ==]",
        " [     =]",
        " [      ]",
        " [     =]",
        " [    ==]",
        " [   == ]",
        " [  ==  ]",
        " [ ==   ]",
        " [==    ]",
        " [=     ]",
        " [      ]",
    ]
    i = 0
    while show_loading:
        print(
            "Searching path from {} to {}... {}".format(start, end, bar[i % len(bar)]),
            end="\r",
        )
        time.sleep(0.075)
        i += 1


start = "Josh Wardle"
end = "Mona Lisa"

if start == end:
    print("Start and end page cannot be the same")
elif not checkIfPageExists(end):
    print("End page does not exist")
elif not checkIfPageExists(start):
    print("Start page does not exist")
else:
    start_time = time.time()
    threading.Thread(
        target=showLoading,
        args=(
            start,
            end,
        ),
    ).start()
    path = mainLoop(start, end)
    end_time = time.time()
    show_loading = False
    print("Path found! {}".format(path))
    minutes, seconds = divmod(end_time - start_time, 60)
    print("Time taken: {:.0f} min {:.0f} s".format(minutes, seconds))
