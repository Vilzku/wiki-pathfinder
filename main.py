import xmlrpc.client
from dotenv import load_dotenv
import os
import threading

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


searched_pages = []

# Traverse tree horizontally and find first empty page
def findNextPage(page):
    if page.getName() not in searched_pages:
        return page
    for child in page.getLinkedPages():
        if child.getName() not in searched_pages:
            return child
    for child in page.getLinkedPages():
        for grandchild in child.getLinkedPages():
            if grandchild.getName() not in searched_pages:
                return findNextPage(child)


def getLinks(worker, page):
    try:
        worker["status"] = 1
        print("getlinks", page, worker["name"])
        links = worker["proxy"].getLinks(page.getName())
        if links != None:
            for link in links:
                if link not in searched_pages:
                    page.addLink(Node(link))
        else:
            raise "{} failed to get links".format(worker["name"])
    except Exception as e:
        searched_pages.remove(page.getName())
        print("getLinks error:", e)
    finally:
        worker["status"] = 0


def mainLoop(root):
    while True:
        page = findNextPage(root)
        if page == None:
            continue
        searched_pages.append(page.getName())
        should_loop = True
        while should_loop:
            for worker in workers:
                should_loop = False
                try:
                    if worker["status"] == 0:
                        threading.Thread(target=getLinks, args=(worker, page)).start()
                        break
                    if worker["name"] == workers[-1]["name"]:
                        should_loop = True
                except Exception as e:
                    print(e)


root = Node("Will Smith")
mainLoop(root)
