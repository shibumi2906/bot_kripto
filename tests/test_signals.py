# File: tests/test_signals.py
import pytest
from app.utils.validators import validate_signal, ValidationError

@pytest.mark.parametrize("sig, last_price", [
    ({"action": "BUY", "entry": 100.0, "target": 102.0, "stop_loss": 98.0, "confidence": 0.7}, 100.0),
    ({"action": "SELL", "entry": 100.0, "target": 98.0, "stop_loss": 102.0, "confidence": 0.6}, 100.0)
])
def test_validate_signal_valid(sig, last_price):
    """Valid signals should pass without exception."""
    validate_signal(sig, last_price)

@pytest.mark.parametrize("sig, last_price", [
    ({"action": "HOLD", "entry": 200.0, "target": 200.0, "stop_loss": 200.0, "confidence": 0.5}, 100.0),  # confidence too low and out-of-bounds prices
    ({"action": "WRONG", "entry": 100.0, "target": 100.0, "stop_loss": 100.0, "confidence": 0.7}, 100.0),  # invalid action
    ({"action": "BUY", "target": 100.0, "stop_loss": 100.0, "confidence": 0.7}, 100.0)  # missing entry
])
def test_validate_signal_invalid(sig, last_price):
    """Invalid signals should raise ValidationError."""
    with pytest.raises(ValidationError):
        validate_signal(sig, last_price)
