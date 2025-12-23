from herBERT.FileHandler.JsonHandler import JsonHandler
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
"""
tested model:
model_name = "roberta-large-mnli" prob outputs ranged from 0.002 to 0.04
model_name = "cross-encoder/nli-deberta-v3-xsmall" prob outputs ranged from 0.001 to 0.007
model_name = "cross-encoder/nli-deberta-v3-base" prob outputs ranged from 0.0001 to 0.0013
model_name = "deepset/deberta-v3-large-squad2" prob outputs ranged from 0.49 to 0.55
model_name = "cross-encoder/nli-MiniLM2-L6-H768" prob outputs ranged from 0.001 to 0.019
model_name = "cross-encoder/nli-deberta-v3-large" extreme small outputs
model_name = "ynie/bart-large-snli_mnli_fever_anli_R1_R2_R3-nli" extreme small outputs

model_name = "tasksource/deberta-base-long-nli"
E_ID: E1 Label: neutral Entailment prob: 0.05932486429810524 Equivalent: False
E_ID: E2 Label: neutral Entailment prob: 0.38584259152412415 Equivalent: False
E_ID: E3 Label: entailment Entailment prob: 0.7412768006324768 Equivalent: True
E_ID: E4 Label: neutral Entailment prob: 0.4735947549343109 Equivalent: False
E_ID: E5 Label: entailment Entailment prob: 0.5292176008224487 Equivalent: False
E_ID: E6 Label: neutral Entailment prob: 0.4278987646102905 Equivalent: False
E_ID: E7 Label: neutral Entailment prob: 0.21247582137584686 Equivalent: False
E_ID: E8 Label: neutral Entailment prob: 0.17947818338871002 Equivalent: False
E_ID: E9 Label: neutral Entailment prob: 0.2224508672952652 Equivalent: False

model_name = "deepset/deberta-v3-large-squad2"
"""
class ContentEntailment:
    _model_name = "deepset/deberta-v3-large-squad2"
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
    #23.12. changed to 0.65
    def validate(cls, hypothesis: str, premise: str, threshold: float = 0.65):
        cls._ensure_loaded()

        if (len(cls._tokenizer.encode(premise, hypothesis)) > 400):
            print("Warning: Input too long, truncating may affect results.")

        inputs = cls._tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(cls._device) for k, v in inputs.items()}

        with torch.inference_mode():
            outputs = cls._model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)[0]
        
        
        n_labels = probs.shape[-1]
        raw_id2label = getattr(cls._model.config, "id2label", None) or {}
        if raw_id2label:
            id2label = {int(k): v for k, v in raw_id2label.items()}
        else:
            labels = {0: "CONTRADICTION", 1: "NEUTRAL", 2: "ENTAILMENT"}
            if n_labels <= len(labels):
                id2label = {i: labels[i] for i in range(n_labels)}
            else:
                id2label = {i: str(i) for i in range(n_labels)}

        pred_idx = int(torch.argmax(probs).cpu().item())
        pred_label = id2label.get(pred_idx, str(pred_idx))

        #entail_idx = next((i for i, lbl in id2label.items() if "entail" in lbl.lower()), 2)

        entail_idx = None
        for i, label in id2label.items():
            if "entail" in label.lower():
                entail_idx = i
                break
        
        if entail_idx is not None:
            entailment_prob = float(probs[entail_idx].cpu().item())
            is_equivalent = entailment_prob >= threshold
        elif n_labels == 2:
            entailment_prob = float(probs[1].cpu().item())
            is_equivalent = entailment_prob >= threshold
        else:
            entailment_prob = None
            is_equivalent = False
        #return entailment_prob, is_equivalent
        return pred_label, entailment_prob, is_equivalent

if __name__ == "__main__":
    jh = JsonHandler()
    jh.loadEntailmentData()
    e_ids = jh.getIds()
    results = []

    for e_id in e_ids:
        premise = jh.getPremise(e_id)
        hypothesis = jh.getHypothesis(e_id)


        out = ContentEntailment.validate(premise, hypothesis, threshold=0.65)
        
        if len(out) == 3:
            label, prob, eq = out
        elif len(out) == 2:
            prob, eq = out
            label = "None"
        
        results.append((e_id, label, prob, eq))

    for e_id, label, prob, eq in results:
        print("E_ID:", e_id, "Label:", label, "Entailment prob:", prob, "Equivalent:", eq)

    #premise = "The study provides empirical evidence to back reports on a familial cluster where five family members developed symptoms of COVID-19 7 to 14 days after exposure (Chan et al., 2020), and fits within the range for the incubation period of 7 to 14 days assumed by the WHO and of 8 to 12 days assumed by the ECDC (Anon, 2020)."
    #hypothesis = "COVID-19 has an incubation period of approximately 7-14 days"
    #label, prob, eq = ContentEntailment.validate(premise, hypothesis, threshold=0.65)
    #print("Label:", label, "Entailment prob:", prob, "Equivalent:", eq)