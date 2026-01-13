from herBERT.FileHandler.JsonHandler import JsonHandler
import math
from typing import Dict
from llama_cpp import Llama
from pathlib import Path


class LlamaContentEntailment:
    LABELS = ["SUPPORTS", "CONTRADICTS", "UNKNOWN"]

    def __init__(self):
        base_dir = Path(__file__).resolve().parent
        model_path = base_dir / "mistral-7b-instruct-v0.2.Q5_K_M.gguf"

        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=32768,
            n_threads=8,
            n_gpu_layers=35,
            logits_all=True,
            verbose=False,
        )

    def validate(self, premise: str, argument: str) -> Dict:
        prompt = self.build_prompt(premise, argument)

        scores = self.score_labels(prompt)
        label, confidence = self.select_label(scores)

        #deactivated for performance reasons
        #stress = self._contradiction_stress_test(premise, argument)

        return {
            "premise": premise,
            "argument": argument,
            "label": label,
            "confidence": confidence,
            "label_scores": scores,
            #"stress_test": stress
        }

    def build_prompt(self, premise: str, argument: str) -> str:
        return f"""
            You are a scientific reasoning system performing natural language inference.
            Determine whether the ARGUMENT is supported or contradicted by the provided TEXT.
            Use SUPPORTS when the ARGUMENT is supported by the TEXT.
            Use CONTRADICTS when the ARGUMENT is contradicted by the TEXT.

            Rules that you MUST follow:
            - Use SUPPORTS if the TEXT provides clear and direct evidence that the ARGUMENT is true.

            - Use UNKNOWN ONLY if the TEXT is completely unrelated to the ARGUMENT, OR the TEXT lacks any information that could reasonably support or contradict the ARGUMENT.

            - If the TEXT provides partial, indirect, or probabilistic evidence, you MUST still choose SUPPORTS or CONTRADICTS based on the strongest reasonable interpretation.

            - If the TEXT provides statistical estimates (means, ranges, percentiles) that are consistent with the ARGUMENT’s claimed range, this counts as SUPPORTS.

            - If the TEXT reports values or ranges that fall entirely within the range stated in the ARGUMENT, treat this as SUPPORTS.

            UNKNOWN is only valid if no logical comparison is possible.

            ARGUMENT:
            "{argument}"

            TEXT:
            "{premise}"

            Answer with exactly one of:
            SUPPORTS
            CONTRADICTS
            UNKNOWN

            Answer:

            """.strip()

    def score_labels(self, prompt: str) -> Dict[str, float]:
        scores = {}

        for label in self.LABELS:
            output = self.llm(
                prompt + " " + label,
                max_tokens=0,
                echo=True,
                logprobs=True,
                temperature=0.0
            )

            token_logprobs = output["choices"][0]["logprobs"]["token_logprobs"]
            scores[label] = sum(lp for lp in token_logprobs if lp is not None)

        return scores

    def select_label(self, scores: Dict[str, float]):
        prob_threshold = 0.03
        max_log = max(scores.values())
        exp_scores = {
            k: math.exp(v - max_log) for k, v in scores.items()
        }
        total = sum(exp_scores.values())

        probs = {k: v / total for k, v in exp_scores.items()}

        label = max(probs, key=probs.get)
        p = probs[label]
        p2 = max(p for k, p in probs.items() if k != label)
        if(p - p2) < prob_threshold:
            label = "Could not determine: difference too small"
       
        return label, probs[label]

    def contradiction_stress_test(self, premise: str, argument: str) -> Dict:
        negated_argument = f"It is not true that {argument}"

        original = self.quick_label(premise, argument)
        negated = self.quick_label(premise, negated_argument)

        stable = not (original == "SUPPORTS" and negated == "SUPPORTS")

        return {
            "original_argument_label": original,
            "negated_argument_label": negated,
            "logically_stable": stable
        }

    def quick_label(self, premise: str, argument: str) -> str:
        scores = self.score_labels(self.build_prompt(premise, argument))
        label, _ = self.select_label(scores)
        return label


if __name__ == "__main__":
    jh = JsonHandler()
    lce = LlamaContentEntailment()
    jh.loadEntailmentData("EntailmentDatacopy2.json")
    e_ids = jh.getIds()
    results = []

    for e_id in e_ids:
        premise = jh.getPremise(e_id)
        hypothesis = jh.getHypothesis(e_id)


        out = lce.validate(premise, hypothesis)
        print(out)