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

    def getLinks(self):
        return self.linked_pages

    def resetLinks(self):
        self.linked_pages = []


searched_pages = []

# Traverse tree horizontally and find first empty page
def findNextPage(page):
    if page.getName() not in searched_pages:
        return page
    for child in page.getLinks():
        if child.getName() not in searched_pages:
            return child
    for child in page.getLinks():
        for grandchild in child.getLinks():
            if grandchild.getName() not in searched_pages:
                return findNextPage(child)


def findPath(root, end):
    path = [end]

    # def findLink(node, link):
    #     if link in node.getLinks():
    #         return node.getName()

    #     for child in node.getLinks():
    #         if link in child.getLinks():
    #             return child.getName()

    #     for child in node.getLinks():
    #         for grandchild in child.getLinks():
    #             if link in grandchild.getLinks():
    #                 return grandchild.getName()
    #     return findLink(child, link)

    # while True:
    #     print("Looppers")
    #     page = findLink(root, end)
    #     print(page)
    #     path.insert(0, page)
    #     if page == root.getName():
    #         break
    #     if page == None:
    #         break
    return path


def getLinks(worker, page):
    try:
        worker["status"] = 1
        print("getLinks", page, worker["name"])
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
                ):
                    page.addLink(Node(link))
        else:
            raise Exception(
                "{} failed to get links for {}".format(worker["name"], page.getName())
            )
    except Exception as e:
        searched_pages.remove(page.getName())
        page.resetLinks()
        print("Error:", e)
        # TODO: if cannot connect remove worker from list or idk do something
    finally:
        worker["status"] = 0


def mainLoop(start, end):
    root = Node(start)
    while True:
        if end in searched_pages:
            path = findPath(root, end)
            print(path)
            break
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


start = "Will Smith"
end = "Discord"


mainLoop(start, end)
