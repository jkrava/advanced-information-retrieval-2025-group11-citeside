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

#TODO: High Score is good, low score is bad!!!!!!
def run(argument: str, paper_id: str):
    # Loading the Data
    jh = JsonHandler()
    #jh.loadRefTrain()
    jh.load("herBERT/Data/Input/acl_merged_dataset.jsonl")

    full_tree = ReferenceTreeBuilder()
    for node in jh.getIds():
        full_tree.addNode(node)

    for node in jh.getIds():
        outgoing_refs = jh.getOutgoingRefs(node)
        for ref in outgoing_refs:
            if ref in jh.getIds():
                full_tree.addEdge(node, ref)

    # Validate usages
    uv = UsageValidator()
    searched_tree = ReferenceTreeBuilder()
    search_queue = deque()
    search_queue.append((argument, paper_id, None))
    visited = set()
    while search_queue:
        argument, paper_id, pre_paper_id = search_queue.popleft()
        if paper_id in visited:
            continue
        visited.add(paper_id)
        searched_tree.addNode(paper_id)
        uv_reply = uv.run(argument, jh.getFullText(paper_id), getSuccessorAuthorAndYear(full_tree, jh, paper_id))
        for reply in uv_reply:
            argument_reply = reply["argument"]
            paper_id_reply = reply["paper_id"]
            crit_index = reply["crit_index"]
            search_queue.append((argument_reply, paper_id_reply, paper_id))
            if pre_paper_id is not None:
                searched_tree.addEdge(pre_paper_id, paper_id)
                searched_tree.changeWeightOfEdge(pre_paper_id, paper_id, crit_index)

    searched_tree.plotTree()


if __name__ == "__main__":
    #TODO @Julian: set a good starting point here with nice argument which is traceable across multiple papers
    argument = "Since Bert based models can degenerate it is a practice to report the median of indepent runs. Niven and Kao (2019)"
    paper_id = "2020.acl-main.398"
    run(argument, paper_id)