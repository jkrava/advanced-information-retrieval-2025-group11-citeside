import random

class UsageValidator:
    @staticmethod
    def validate_usage(fullText: str, refText: str, refTitle: str, snippet: str = None):
        #TODO: Implement actual validation logic
        # Problems:
        # - how can we rank the root files critical score where we have no prior data
        # - how do we check for information roots, we somehow need to check where some information is first mentioned and how
        # valid this is
        # - how can we forward this information search through our reference tree as it might be that the root splits to multiple sources
        # maybe we just need a check that the information is present in the referenced file and then go deeper
        # with this we could possibly backtrack to the root of each information and rank those roots by hand (for poc) and with this validate everything in between
        return random.random() ** 7