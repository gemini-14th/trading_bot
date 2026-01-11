def calculate_confidence(
    structure_score: float,
    indicator_score: float,
    volume_score: float,
    volatility_score: float
) -> float:
    """
    Confidence scoring based on document weights:
    - Structure: 30%
    - Indicators: 30%
    - Volume: 20%
    - Volatility: 20%
    """

    confidence = (
        structure_score * 0.30 +
        indicator_score * 0.30 +
        volume_score * 0.20 +
        volatility_score * 0.20
    )

    return round(confidence * 100, 2)
