from cmath import exp
import xmlrpc.client
from dotenv import load_dotenv
import os
import threading

load_dotenv()
WORKERS_LIST = os.environ.get("WORKERS", "worker").split(" ")
DEFAULT_PORT = int(os.environ.get("DEFAULT_PORT", "8000"))

workers = {}

for worker in WORKERS_LIST:
    try:
        workers[worker] = xmlrpc.client.ServerProxy(
            "http://localhost:" + str(DEFAULT_PORT + WORKERS_LIST.index(worker))
        )
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


def findNextPage(page):
    if len(page.getLinkedPages()) == 0:
        return page
    else:
        for linked_page in page.getLinkedPages():
            if linked_page.getLinkedPages() == []:
                return linked_page
        for linked_page in page.getLinkedPages():
            return findNextPage(linked_page)


def mainLoop(root):
    while True:
        page = findNextPage(root)
        print(page)
        for worker_name in workers:
            worker = workers[worker_name]
            if worker.getStatus() == 0:
                links = worker.getLinks(page.getName())
                if links != None:
                    for link in links:
                        page.addLink(Node(link))
                else:
                    print(
                        "Something went wrong in worker and this page needs to be repeated"
                    )
                break


root = Node("Will Smith")
mainLoop(root)
