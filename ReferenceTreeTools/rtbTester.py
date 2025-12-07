import os
import random

from ReferenceTreeTools.ReferenceTreeBuilder import ReferenceTreeBuilder

NUMBER_NODES = 20
EDGE_FREQUENCY = 1/4
UNKNOWN_WEIGHT_FREQUENCY = 9/10
RARENESS_EXP = 7


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
    gb_loaded.printTree()
    gb_loaded.plotTree()
    return gb_loaded


if __name__ == "__main__":
    run()