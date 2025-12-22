from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

class ContentEntailment:
    _model_name = "roberta-large-mnli"
    _tokenizer = None
    _model = None
    _device = None

    @classmethod
    def _ensure_loaded(cls):
        if cls._model is not None:
            return
        cls._device = "cuda" if torch.cuda.is_available() else "cpu"
        cls._tokenizer = AutoTokenizer.from_pretrained(cls._model_name, use_fast=True)
        cls._model = AutoModelForSequenceClassification.from_pretrained(cls._model_name)
        cls._model.to(cls._device)
        cls._model.eval()

    @classmethod
    def validate(cls, hypothesis: str, premise: str, threshold: float = 0.75):
        cls._ensure_loaded()

        if (len(cls._tokenizer.encode(premise, hypothesis)) > 400):
            print("Warning: Input too long, truncating may affect results.")

        inputs = cls._tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(cls._device) for k, v in inputs.items()}

        with torch.inference_mode():
            outputs = cls._model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)[0]

        raw_id2label = getattr(cls._model.config, "id2label", {})
        id2label = {int(k): v for k, v in raw_id2label.items()} if raw_id2label else {0: "CONTRADICTION",
                                                                                      1: "NEUTRAL", 2: "ENTAILMENT"}

        entail_idx = next((i for i, lbl in id2label.items() if "entail" in lbl.lower()), 2)

        entailment_prob = float(probs[entail_idx].cpu().item())
        pred_idx = int(torch.argmax(probs).cpu().item())
        pred_label = id2label.get(pred_idx, str(pred_idx))

        is_equivalent = entailment_prob >= threshold
        return entailment_prob, is_equivalent
        #return pred_label, entailment_prob, is_equivalent

if __name__ == "__main__":
    premise = "We evaluate the proposed method on three benchmark datasets and observe consistent improvements over baseline models in terms of average F1 score. However, these gains are statistically significant only for the largest dataset, and performance on smaller datasets varies depending on the random seed. No improvements are observed when the model is evaluated without the auxiliary loss."
    hypothesis = "The paper demonstrates that the proposed method reliably outperform baseline approaches across multiple datasets."
    label, prob, eq = ContentEntailment.validate(premise, hypothesis, threshold=0.65)
    print("Label:", label, "Entailment prob:", prob, "Equivalent:", eq)