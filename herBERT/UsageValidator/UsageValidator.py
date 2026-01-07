from herBERT.UsageValidator.LlamaContentEntailment import LlamaContentEntailment
from herBERT.UsageValidator.SnippetCollector import SnippetCollector
from herBERT.UsageValidator.ReferenceLinker import ReferenceLinker
from herBERT.ReferenceTreeTools.ScoreCombiner import ScoreCombiner

class UsageValidator:
    def __init__(self):
        self.snippet_collector = SnippetCollector()
        self.content_entailment = LlamaContentEntailment()
        self.reference_linker = ReferenceLinker()

    def run(self, argument: str, paper_text: str, paper_refs, print_logs: bool = False):
        if paper_refs is None:
            return None

        #Collect Snippets
        snippets = self.snippet_collector.match_argument(
            paper_text,
            argument,
            top_k=5,
            min_score=0.55
        )

        if not snippets:
            return None

        # Extract Links
        for s in snippets:
            linked_ref = self.reference_linker.link_references(s["chunk"], paper_refs)
            s["linked_ref"] = linked_ref


        snippets = [s for s in snippets if s["linked_ref"] is not None]

        #Validate Snippet Usage
        for s in snippets:
            out = self.content_entailment.validate(argument, s["chunk"])
            s['valid'] = out['label']
            entailment_prob = out['confidence']
            combined_prob = out['confidence'] * s["snippet_score"]
            if out['label'] == "SUPPORTS":
                pass
            elif out['label'] == "CONTRADICTS":
                entailment_prob = 1.0 - out['confidence']
                combined_prob = 1.0 - combined_prob
            elif out['label'] == "UNKNOWN":
                entailment_prob = -1.0
                combined_prob = entailment_prob * -1.0

            s["entailment_prob"] = entailment_prob
            s["overall_score"] = combined_prob

        reply = []
        for s in snippets:
            if s["linked_ref"]:
                reply.append({
                    "argument": s["chunk"],
                    "paper_id": s["linked_ref"],
                    "crit_index": s["overall_score"]
            })

        if print_logs:
            for s in snippets:
                print(s)

        return reply

