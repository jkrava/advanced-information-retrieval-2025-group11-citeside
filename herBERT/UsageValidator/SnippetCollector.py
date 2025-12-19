from herBERT.FileHandler.JsonHandler import JsonHandler
from sentence_transformers import SentenceTransformer, util
import nltk
from typing import List, Dict

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

class ArgumentSentenceMatcher:
    """
    Finds sentences in a text that most likely express
    a given argument using semantic similarity.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        chunk_size: int = 3,
        stride: int | None = None
    ):
        self.model = SentenceTransformer(model_name)
        self.chunk_size = max(1, chunk_size)
        # default stride creates overlap; set to 1 for strong overlap or equal to chunk_size for no overlap
        self.stride = stride if stride is not None else max(1, self.chunk_size - 1)

    def _chunk_sentences(self, text: str) -> List[Dict]:
        """
        Tokenize into sentences and build overlapping chunks.
        Returns a list of dicts: { 'text': chunk_text, 'sentences': [s1, s2, ...] }
        """
        sents = nltk.sent_tokenize(text)
        if not sents:
            return []

        chunks = []
        for i in range(0, len(sents), self.stride):
            chunk_sents = sents[i:i + self.chunk_size]
            if not chunk_sents:
                continue
            chunks.append({
                "text": " ".join(chunk_sents),
                "sentences": chunk_sents,
                "start_index": i,
                "end_index": i + len(chunk_sents) - 1
            })
            if i + self.chunk_size >= len(sents):
                break
        return chunks

    def match_argument(
        self,
        text: str,
        argument: str,
        top_k: int = 5,
        min_score: float = 0.45
    ) -> List[Dict]:
        """
        Returns the top-k chunks most semantically similar to the given argument.
        Each result contains the chunk text and the list of sentences inside it.
        """
        chunks = self._chunk_sentences(text)
        if not chunks:
            return []

        chunk_texts = [c["text"] for c in chunks]

        chunk_embeddings = self.model.encode(
            chunk_texts,
            convert_to_tensor=True,
            normalize_embeddings=True
        )

        argument_embedding = self.model.encode(
            argument,
            convert_to_tensor=True,
            normalize_embeddings=True
        )

        scores = util.cos_sim(argument_embedding, chunk_embeddings)[0]
        ranked_indices = scores.argsort(descending=True)

        results = []
        for idx in ranked_indices[:top_k]:
            score = scores[idx].item()
            if score >= min_score:
                c = chunks[idx]
                results.append({
                    "chunk": c["text"],
                    "sentences": c["sentences"],
                    "score": score,
                    "start_index": c["start_index"],
                    "end_index": c["end_index"]
                })

        return results


if __name__ == "__main__":
    extractor = ArgumentSentenceMatcher()
    jh = JsonHandler()
    jh.loadRefTrain()
    check_argument = "NLPs are easy to use."
    argument = "Due to NLPs ease and effectiveness, this paradigm has already been used to deploy large, fine-tuned models across a variety of real-world applications (Nayak (2019) ; Zhu (2019) ; Qadrud-Din (2019) inter alia)."
    paper_text = jh.getFullText("2020.wmt-1.91")

    matches = extractor.match_argument(paper_text, argument)
    for m in matches:
        print(f"{m['score']:.3f} | {m['chunk']}")

