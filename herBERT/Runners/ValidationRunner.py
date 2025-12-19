from herBERT.FileHandler.JsonHandler import JsonHandler
from herBERT.ReferenceTreeTools.ReferenceTreeBuilder import ReferenceTreeBuilder
from herBERT.UsageValidator.UsageValidator import UsageValidator

def run():
    UsageValidator.validate_usage( "", "", "")
    # Loading the Data
    jh = JsonHandler()
    jh.loadRefTrain()

    rtb = ReferenceTreeBuilder()
    for node in jh.getIds():
        rtb.addNode(node)

    for node in jh.getIds():
        outgoing_refs = jh.getOutgoingRefs(node)
        for ref in outgoing_refs:
            if ref in jh.getIds():
                rtb.addEdge(node, ref)

    # Validate usages
    for u, v, data in rtb.getEdges():
        weight = data.get("weight", -1)
        if weight == -1:
            fullText = jh.getFullText(u)
            refText = jh.getFullText(v)
            refTitle = jh.getTitle(v)
            weighter = UsageValidator.validate_usage(fullText, refText, refTitle)
            rtb.changeWeightOfEdge(u, v, weighter)

    rtb.plotTree()

def testRun():




if __name__ == "__main__":
    run()