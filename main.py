import xmlrpc.client
from dotenv import load_dotenv
import os
import threading
import time
import sys

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
        self.all_searched = False

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

    def setAllSearched(self):
        self.all_searched = True

    def getAllSearched(self):
        return self.all_searched


# Traverse tree horizontally and find first empty child pages
def findNextPages(root):
    if root.getAllSearched() == False:
        for child in root.getLinkedPages():
            if child.getName() not in searched_pages:
                return child
            elif root.getLinkedPages().index(child) == len(root.getLinkedPages()) - 1:
                root.setAllSearched()

    for child in root.getLinkedPages():
        if child.getAllSearched() == False:
            for grandchild in child.getLinkedPages():
                if grandchild.getName() not in searched_pages:
                    return grandchild
                elif (
                    child.getLinkedPages().index(grandchild)
                    == len(child.getLinkedPages()) - 1
                ):
                    child.setAllSearched()

    for child in root.getLinkedPages():
        for grandchild in child.getLinkedPages():
            if grandchild.getAllSearched() == False:
                for greatgrandchild in grandchild.getLinkedPages():
                    if greatgrandchild.getName() not in searched_pages:
                        return greatgrandchild
                    elif (
                        grandchild.getLinkedPages().index(greatgrandchild)
                        == len(grandchild.getLinkedPages()) - 1
                    ):
                        grandchild.setAllSearched()


# At the end find the path from start to end
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


# Find a worker that is not busy
def findWorker():
    while True:
        for worker in workers:
            if worker["status"] == 0:
                return worker


# Get all links from a page using selected worker
def getLinks(worker, page):
    global page_found
    try:
        worker["status"] = 1
        links = worker["proxy"].getLinks(page.getName())
        if links != False:
            for link in links:
                if any(
                    [
                        x in link
                        for x in [
                            "File:",
                            "Help:",
                            "Template:",
                            "Talk:",
                            "Template talk:",
                            "Wikipedia:",
                            "Category:",
                        ]
                    ]
                ):
                    continue
                if link not in searched_pages:
                    page.addLink(Node(link))
        else:
            raise Exception("Failed to get links for {}".format(page.getName()))
        if end in links:
            page_found = True
        worker["status"] = 0
    except Exception as e:
        worker["status"] = -1
        searched_pages.remove(page.getName())
        page.resetLinkedPages()
        print(
            "Error: {}: {}".format(worker["name"], e),
            end=" " * 50 + "\n",
        )


# Use wroker to find out if a Wikipedia page exists
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


# Go through all the links and find the end page
def mainLoop(start, end):
    root = Node(start)
    getLinks(workers[0], root)
    while True:
        if page_found:
            return findPath(root, end)
        start_time = time.time()
        page = findNextPages(root)
        end_time = time.time()
        print(end_time - start_time)
        if page == None:
            continue
        try:
            searched_pages.append(page.getName())
            worker = findWorker()
            threading.Thread(
                target=getLinks,
                args=(
                    worker,
                    page,
                ),
            ).start()
        except Exception as e:
            print(
                "Error: {}".format(e),
                end=" " * 50 + "\n",
            )


# Display status bar animation and page counter
def showLoading(start, end):
    bar = [
        "[=     ]",
        "[==    ]",
        "[ ==   ]",
        "[  ==  ]",
        "[   == ]",
        "[    ==]",
        "[     =]",
        "[    ==]",
        "[   == ]",
        "[  ==  ]",
        "[ ==   ]",
        "[==    ]",
    ]
    i = 0
    while show_loading:
        print(
            "Searching path from {} to {}... {} {}".format(
                start, end, bar[i % len(bar)], len(searched_pages)
            ),
            end="\r",
        )
        time.sleep(0.075)
        i += 1


def main():
    global show_loading
    print("Starting the program...", end="\r")

    if start == end:
        print("Start and end page cannot be the same")
        return
    if not checkIfPageExists(end):
        print("End page does not exist")
        return
    if not checkIfPageExists(start):
        print("Start page does not exist")
        return

    threading.Thread(
        target=showLoading,
        args=(
            start,
            end,
        ),
    ).start()

    start_time = time.time()
    path = mainLoop(start, end)
    end_time = time.time()

    show_loading = False
    time.sleep(0.075)
    print(" " * 70, end="\r")
    print("Path found!")
    print("   " + path[0])
    for link in path[1:]:
        print("-> {}".format(link))
    print("Length: {} links.".format(len(path) - 1), end="")
    print(" {} pages searched.".format(len(searched_pages)))
    minutes, seconds = divmod(end_time - start_time, 60)
    print("Time taken: {:.0f} min {:.0f} s".format(minutes, seconds))


start = sys.argv[1]  # Start page
end = sys.argv[2]  # End page
searched_pages = [start]  # Pages that have already been searched
page_found = False  # Is the end page found in searched pages
show_loading = True  # Show loading animation

main()
