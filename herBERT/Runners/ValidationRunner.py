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
    jh.loadRefTrain()

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
        if paper_id in visited: #TODO: run the check anyways to set the edge weight to this paper_id
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
    argument = "Due to NLPs ease and effectiveness, this paradigm has already been used to deploy large, fine-tuned models across a variety of real-world applications (Nayak (2019) ; Zhu (2019) ; Qadrud-Din (2019) inter alia)."
    paper_id = "2020.wmt-1.91"
    argument_with_refs = "Note, however, that the parsing problem for these frameworks is harder in the current shared task than in the ealier DELPH-IN MRS Bi-Lexical Dependencies The DM bi-lexical dependencies (Ivanova et al., 2012) originally derive from the underspecified logical forms computed by the English Resource Grammar (Flickinger et al., 2017; Copestake et al., 2005) ."
    paper_id_with_refs = "K19-2001"
    run(argument_with_refs, paper_id_with_refs)