# File: app/utils/validators.py
from typing import Dict
from app.core.logger import logger

class ValidationError(Exception):
    """Custom exception for signal validation errors."""
    pass


def validate_signal(
    sig: Dict,
    last_price: float,
    tolerance: float = 0.05,
    min_confidence: float = 0.6
) -> None:
    """
    Validate trading signal fields and value ranges.

    Raises ValidationError if any check fails.
    """
    action = sig.get('action')
    if action not in ('BUY', 'SELL', 'HOLD'):
        raise ValidationError(f'Invalid action: {action}')

    for field in ('entry', 'target', 'stop_loss', 'confidence'):
        if field not in sig:
            raise ValidationError(f'Missing field: {field}')

    confidence = sig['confidence']
    if not isinstance(confidence, (float, int)) or not (0 <= confidence <= 1):
        raise ValidationError(f'Invalid confidence: {confidence}')
    if confidence < min_confidence:
        raise ValidationError(f'Confidence below threshold: {confidence}')

    for price_field in ('entry', 'target', 'stop_loss'):
        price_value = sig[price_field]
        if not isinstance(price_value, (float, int)):
            raise ValidationError(f'Invalid price type for {price_field}: {price_value}')
        low, high = last_price * (1 - tolerance), last_price * (1 + tolerance)
        if not (low <= price_value <= high):
            raise ValidationError(
                f'{price_field}={price_value} out of bounds ({low}-{high})'
            )

    logger.debug(f"Signal validated: {sig}")
