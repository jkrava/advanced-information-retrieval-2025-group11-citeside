import re

class ReferenceLinker:
    def extract_surnames(self, ref):
        if not ref:
            return []
        authors = ref["authors"]
        parts = re.split(r'\s+and\s+|;|\n', authors)
        seen = set()
        surnames = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if ',' in part:
                surname = part.split(',', 1)[0]
            else:
                surname = part.split()[-1]
            if surname and surname not in seen:
                seen.add(surname)
                surnames.append(surname)
        return surnames

    def find_surnames_in_text(self, snippet: str, author: str):
        pattern = r'\b' + re.escape(author) + r'\b'
        return bool(re.search(pattern, snippet, re.IGNORECASE))

    #TO-DO: this only works for singular names mentioned per snippet, maybe if there are multiple names we can somehow make multiple snippets out of it and feed all of them?
    def link_references(self, snippet, refs):
        for ref in refs:
            authors = self.extract_surnames(ref)
            for author in authors:
                if self.find_surnames_in_text(snippet, author):
                    return ref["paper_id"]
        return None

if __name__ == "__main__":
    rl = ReferenceLinker()
    snippet = "The SDP graph banks were originally released through the Linguistic Data Consortium (as catalogue entry LDC 2016T10); they comprise four distinct bi-lexical semantic dependency frameworks, from which the MRP 2019 shared task selects two (a) DELPH-IN MRS Bi-Lexical Dependencies (DM) and (b) Prague Semantic Dependencies (PSD). 1 1 Note, however, that the parsing problem for these frameworks is harder in the current shared task than in the ealier DELPH-IN MRS Bi-Lexical Dependencies The DM bi-lexical dependencies (Ivanova et al., 2012) originally derive from the underspecified logical forms computed by the English Resource Grammar (Flickinger et al., 2017; Copestake et al., 2005) . These logical forms are not in and of themselves semantic graphs (in the sense of §2 above) and are often refered to as English Resource Semantics (ERS; Bender et al., 2015) ."
    refs = [{'authors': 'Bender, Khoa  and\nNguyen, Dang', 'paper_id': 'S17-2156', 'year': '2015'}]
    linked_ref = rl.link_references(snippet, refs)
    print(f"Linked Reference: {linked_ref}")