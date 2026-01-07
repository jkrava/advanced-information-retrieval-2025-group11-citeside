import os
import random

from herBERT.ReferenceTreeTools.ReferenceTreeBuilder import ReferenceTreeBuilder

NUMBER_NODES = 20
EDGE_FREQUENCY = 1/4
UNKNOWN_WEIGHT_FREQUENCY = 10/10
RARENESS_EXP = 7

CRAWL_NUMBER_NODES = 20
CRAWL_CONECTION = 3
CRAWL_DEPTH = 5
REVERSE_DEPTH = 2
CRAWL_ROOT = "5"



def run():
    rtb = ReferenceTreeBuilder()
    for i in range (NUMBER_NODES):
        rtb.addNode(str(i))
    for i in range(NUMBER_NODES):
        for j in range(i + 1, NUMBER_NODES):
            if random.random() < EDGE_FREQUENCY:
                rtb.addEdge(str(i), str(j))
    for edge in rtb.getEdges():
        if random.random() < UNKNOWN_WEIGHT_FREQUENCY:
            rtb.changeWeightOfEdge(edge[0], edge[1], random.random() ** RARENESS_EXP)

    built = rtb.build()

    # Persist and reload
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rtb_test.json")
    rtb.store(out_path)
    print(f"Stored to {out_path}")

    gb_loaded = rtb.load(out_path)
    #gb_loaded.printTree()
    #gb_loaded.plotTree()




    rtb_crawl = ReferenceTreeBuilder()
    for i in range (CRAWL_NUMBER_NODES):
        rtb_crawl.addNode(str(i))
    for i in range(CRAWL_NUMBER_NODES):
        for j in range(i + 1, i + 1 + CRAWL_CONECTION):
            rtb_crawl.addEdge(str(i), str(j))
    for edge in rtb_crawl.getEdges():
        if random.random() < UNKNOWN_WEIGHT_FREQUENCY:
            rtb_crawl.changeWeightOfEdge(edge[0], edge[1], random.random() ** RARENESS_EXP)

    print(rtb_crawl.getReferences("0"))
    rtb_crawl.changeWeightOfEdge("0", "1", -0.5)
    rtb_crawl.plotTree()

    rtb_crawl.addNodeIndex("0", 0.9)

    crawled = rtb_crawl.buildCrawlTree(CRAWL_ROOT, CRAWL_DEPTH, REVERSE_DEPTH)
    crawled.printTree()
    crawled.plotTree()

    crawled.buildCombCritIndex()
    crawled.printTree()
    crawled.plotTree()

    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "rtb_test.json")
    crawled.store(out_path)
    print(f"Stored to {out_path}")

    gb_loaded = crawled.load(out_path)
    gb_loaded.printTree()
    gb_loaded.plotTree()


if __name__ == "__main__":
    run()