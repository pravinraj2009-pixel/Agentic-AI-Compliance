
def aggregate_confidence(base_confidence, validation_results):
    confidence = base_confidence
    for r in validation_results:
        confidence -= r.get("confidence_impact", 0)
    return max(round(confidence, 3), 0.0)
