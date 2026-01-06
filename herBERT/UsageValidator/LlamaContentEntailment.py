from herBERT.FileHandler.JsonHandler import JsonHandler
import math
from typing import Dict
from llama_cpp import Llama


class LlamaContentEntailment:
    LABELS = ["SUPPORTS", "CONTRADICTS", "UNKNOWN"]

    def __init__(self):
        self.llm = Llama(
          model_path=r"C:\Users\User\Desktop\Julian\Uni\WS 25\AIR\herBERT\mistral-7b-instruct-v0.2.Q5_K_M.gguf",
          n_ctx=32768,  # The max sequence length to use - note that longer sequence lengths require much more resources
          n_threads=8,            # The number of CPU threads to use, tailor to your system and the resulting performance
          n_gpu_layers=35,         # The number of layers to offload to GPU, if you have GPU acceleration available
          logits_all=True
        )

    def validate(self, premise: str, argument: str) -> Dict:
        prompt = self._build_prompt(premise, argument)

        scores = self._score_labels(prompt)
        label, confidence = self._select_label(scores)

        #stress = self._contradiction_stress_test(premise, argument)

        return {
            "premise": premise,
            "argument": argument,
            "label": label,
            "confidence": confidence,
            "label_scores": scores,
            #"stress_test": stress
        }

    def _build_prompt(self, premise: str, argument: str) -> str:
        return f"""
            You are a scientific reasoning system.
            
            Determine whether the text SUPPORTS, CONTRADICTS,
            or does NOT provide enough information about the argument.

            Argument:
            "{argument}"
            
            Text:
            "{premise}"
            
            Answer with exactly one of:
            SUPPORTS
            CONTRADICTS
            UNKNOWN
            
            Answer:
            """.strip()

    def _score_labels(self, prompt: str) -> Dict[str, float]:
        scores = {}

        for label in self.LABELS:
            output = self.llm(
                prompt + " " + label,
                max_tokens=0,
                echo=True,
                logprobs=True
            )

            token_logprobs = output["choices"][0]["logprobs"]["token_logprobs"]
            scores[label] = sum(lp for lp in token_logprobs if lp is not None)

        return scores

    def _select_label(self, scores: Dict[str, float]):
        max_log = max(scores.values())
        exp_scores = {
            k: math.exp(v - max_log) for k, v in scores.items()
        }
        print(exp_scores)
        total = sum(exp_scores.values())

        probs = {k: v / total for k, v in exp_scores.items()}
       
        label = max(probs, key=probs.get)

        return label, probs[label]

    def _contradiction_stress_test(self, premise: str, argument: str) -> Dict:
        negated_argument = f"It is not true that {argument}"

        original = self._quick_label(premise, argument)
        negated = self._quick_label(premise, negated_argument)

        stable = not (original == "SUPPORTS" and negated == "SUPPORTS")

        return {
            "original_argument_label": original,
            "negated_argument_label": negated,
            "logically_stable": stable
        }

    def _quick_label(self, premise: str, argument: str) -> str:
        scores = self._score_labels(self._build_prompt(premise, argument))
        label, _ = self._select_label(scores)
        return label


if __name__ == "__main__":
    jh = JsonHandler()
    lce = LlamaContentEntailment()
    jh.loadEntailmentData()
    e_ids = jh.getIds()
    results = []

    for e_id in e_ids:
        premise = jh.getPremise(e_id)
        hypothesis = jh.getHypothesis(e_id)


        out = lce.validate(premise, hypothesis)
        print(out)