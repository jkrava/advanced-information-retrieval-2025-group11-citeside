from herBERT.UsageValidator.ContentEntailment import ContentEntailment

class UsageValidator:
    def run(self, premise: str, hypothesis: str, threshold: float = 0.75):
        return ContentEntailment.validate(premise, hypothesis, threshold)

if __name__ == "__main__":
    premise = "We evaluate the proposed method on three benchmark datasets and observe consistent improvements over baseline models in terms of average F1 score. However, these gains are statistically significant only for the largest dataset, and performance on smaller datasets varies depending on the random seed. No improvements are observed when the model is evaluated without the auxiliary loss."
    hypothesis = "The paper demonstrates that the proposed method does not reliably outperform baseline approaches across multiple datasets."
    label, prob, eq = UsageValidator.runIndexing(premise, hypothesis)
    print("Label:", label, "Entailment prob:", prob, "Equivalent:", eq)