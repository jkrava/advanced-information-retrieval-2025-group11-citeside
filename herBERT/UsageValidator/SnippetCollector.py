from herBERT.FileHandler.JsonHandler import JsonHandler
from sentence_transformers import SentenceTransformer, util
import nltk
from typing import List, Dict

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

class SnippetCollector:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        chunk_size: int = 1,
        stride: int | None = None
    ):
        self.model = SentenceTransformer(model_name)
        self.chunk_size = max(1, chunk_size)
        # default stride creates overlap; set to 1 for strong overlap or equal to chunk_size for no overlap
        self.stride = stride if stride is not None else max(1, self.chunk_size - 1)

    def chunk_sentences(self, text: str):
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
        chunks = self.chunk_sentences(text)
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

        '''
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
        '''

        results = []
        for idx in ranked_indices[:top_k]:
            score = scores[idx].item()
            if score >= min_score:
                c = chunks[idx]
                results.append({
                    "chunk": c["text"],
                    "snippet_score": score
                })

        return results


if __name__ == "__main__":
    extractor = SnippetCollector()
    jh = JsonHandler()
    jh.loadCovid()
    argument = "Covid-19 came from dogs"
    paper_text = jh.getFullText("0001")

    matches = extractor.match_argument(paper_text, argument)
    for m in matches:
        print(f"{m['snippet_score']:.3f} | {m['chunk']}")

