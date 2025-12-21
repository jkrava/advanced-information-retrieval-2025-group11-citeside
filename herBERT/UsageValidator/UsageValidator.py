from herBERT.UsageValidator.ContentEntailment import ContentEntailment
from herBERT.UsageValidator.SnippetCollector import SnippetCollector
from herBERT.UsageValidator.ReferenceLinker import ReferenceLinker
from herBERT.ReferenceTreeTools.ScoreCombiner import ScoreCombiner

class UsageValidator:
    def __init__(self):
        self.snippet_collector = SnippetCollector()
        self.content_entailment = ContentEntailment()
        self.reference_linker = ReferenceLinker()

    def run(self, argument: str, paper_text: str, paper_refs: str, print_logs: bool = False):

        #Collect Snippets
        snippets = self.snippet_collector.match_argument(
            paper_text,
            argument,
            top_k=1,
            min_score=0.55
        )

        if not snippets:
            return (None, None), -1.0

        #Validate Snippet Usage
        for s in snippets:
            entailment_prob, is_equivalent = self.content_entailment.validate(argument, s["chunk"], 0.75)
            s["valid"] = is_equivalent
            s["entailment_prob"] = entailment_prob
            # TODO: check this method as this might be a weakness in the logic:
            s["overall_score"] = ScoreCombiner.combineCrits(entailment_prob, s["snippet_score"], ScoreCombiner.MULTIPLICATION)

        #Extract Links
        for s in snippets:
            if s["valid"]:
                linked_ref = self.reference_linker.link_reference(s["chunk"], paper_refs)
                s["linked_ref"] = linked_ref
                if not linked_ref:
                    s["valid"] = False

        reply = []
        for s in snippets:
            if s["valid"]:
                reply.append({
                    "argument": s["chunk"],
                    "paper_id": s["linked_ref"],
                    "crit_index": s["overall_score"]
                })

        if print_logs:
            for s in snippets:
                print(s)

        return reply

