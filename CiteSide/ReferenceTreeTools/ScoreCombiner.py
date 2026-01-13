class ScoreCombiner:
    MULTIPLICATION = "multiplication"
    MIN = "min"

    @staticmethod
    def combineCrits(weight_1: float, weight_2: float, mode: str = MULTIPLICATION):
        if weight_1 == -1:
            # case that we have the root nodes who reference nothing anymore (would need a specific model to check them or manual setting)
            return weight_2
        weight_1 = 1.0 - weight_1
        weight_2 = 1.0 - weight_2
        combined = 0.0
        match mode:
            case ScoreCombiner.MULTIPLICATION:
                combined = weight_1 * weight_2
                if combined < 0.001:
                    combined = 0.001
            case ScoreCombiner.MIN:
                combined = min(weight_1, weight_2)
            case _:
                raise ValueError(f"Unknown mode: {mode}")
        return 1.0 - combined