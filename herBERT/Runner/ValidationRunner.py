from herBERT.FileHandler.JsonHandler import JsonHandler
from herBERT.ReferenceTreeTools.ReferenceTreeBuilder import ReferenceTreeBuilder
from herBERT.UsageValidator.UsageValidator import UsageValidator
from collections import deque

def getSuccessorAuthorAndYear(tree: ReferenceTreeBuilder, data: JsonHandler, paper_id: str):
    successors = tree.getReferences(paper_id)
    if not successors:
        return None

    refs = []
    for s in successors:
        refs.append({
            "paper_id": s,
            "authors": data.getAuthors(s),
            "year": data.getYear(s)
        })

    return refs

def printFindings(replys):
    def fg_escape(r: int, g: int, b: int):
        return f"\x1b[38;2;{r};{g};{b}m"
    reset = "\x1b[0m"
    rtb = ReferenceTreeBuilder()

    current_source = None
    for reply in replys:
        source_paper_id = reply["source_paper_id"]
        if source_paper_id != current_source:
            current_source = source_paper_id
            print(f"\nFound within Paper: {source_paper_id}")
        weight = reply["crit_index"]
        r, g, b = rtb.rgbForWeight(weight)
        color = fg_escape(r, g, b)

        print(f"{color}{reply}{reset}")

def run(argument: str, paper_id: str):
    # Loading the Data
    jh = JsonHandler()
    
    jh.loadCovid()
    #jh.loadRefTrain()
    full_tree = ReferenceTreeBuilder()
    for node in jh.getIds():
        full_tree.addNode(node)

    for node in jh.getIds():
        outgoing_refs = jh.getOutgoingRefs(node)
        for ref in outgoing_refs:
            if ref in jh.getIds():
                full_tree.addEdge(node, ref)

    #full_tree.plotTree()

    # Validate usages
    uv = UsageValidator()
    searched_tree = ReferenceTreeBuilder()
    searched_tree.addNode(paper_id)
    search_queue = deque()
    search_queue.append((argument, paper_id))
    visited = set()
    replys = []

    while search_queue:
        argument, paper_id = search_queue.popleft()

        uv_reply = uv.run(argument, jh.getFullText(paper_id), getSuccessorAuthorAndYear(full_tree, jh, paper_id))
        if not uv_reply:
            continue
        for reply in uv_reply:
            reply["source_paper_id"] = paper_id
            replys.append(reply)
            if (not reply["paper_id"]):
                continue
            argument_reply = argument
            paper_id_reply = reply["paper_id"]
            crit_index = reply["crit_index"]
            if paper_id_reply not in visited:
                visited.add(paper_id_reply)
                search_queue.append((argument_reply, paper_id_reply))
            searched_tree.addNode(paper_id_reply)
            searched_tree.addEdge(paper_id, paper_id_reply)
            searched_tree.changeWeightOfEdge(paper_id, paper_id_reply, crit_index)
    

    print("Found Snippets")
    for reply in replys:
        print(reply)

    printFindings(replys)

    searched_tree.plotTree()


if __name__ == "__main__":
    argument_with_refs = "COVID-19 has a mean incubation period between 5 and 14 days."
    paper_id_with_refs = "0001"
    run(argument_with_refs, paper_id_with_refs)

