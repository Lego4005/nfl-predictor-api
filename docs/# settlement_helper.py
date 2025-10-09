# settlement_helper.py

from typing import Literal, Tuple

OddsType = Literal["american", "decimal", "fraction"]
Outcome  = Literal["win", "loss", "push", "void"]

def american_to_decimal(amer: int) -> float:
    if amer == 0:
        raise ValueError("American odds cannot be 0")
    return (1 + amer/100.0) if amer > 0 else (1 + 100.0/abs(amer))

def fraction_to_decimal(frac: str) -> float:
    # e.g., "10/11"
    num, den = frac.strip().split("/")
    return 1.0 + (float(num) / float(den))

def to_decimal(odds_type: OddsType, odds_value: str | float | int) -> float:
    if odds_type == "decimal":
        d = float(odds_value)
        if d <= 1.0:
            raise ValueError("Decimal odds must be > 1.0")
        return d
    if odds_type == "american":
        return american_to_decimal(int(odds_value))
    if odds_type == "fraction":
        return fraction_to_decimal(str(odds_value))
    raise ValueError(f"Unsupported odds_type: {odds_type}")

def implied_probability(odds_type: OddsType, odds_value: str | float | int) -> float:
    d = to_decimal(odds_type, odds_value)
    return 1.0 / d

def settle_ticket(
    stake_units: float,
    odds_type: OddsType,
    odds_value: str | float | int,
    outcome: Outcome
) -> Tuple[float, float]:
    """
    Returns: (pnl_units, payout_units)
    - pnl_units excludes returned stake (negative on loss, 0 push/void, positive on win)
    - payout_units is total returned to bankroll (stake + profit) on win, stake on push/void, 0 on loss
    """
    if stake_units < 0:
        raise ValueError("Stake must be non-negative")
    d = to_decimal(odds_type, odds_value)

    if outcome == "win":
        profit = stake_units * (d - 1.0)
        return profit, stake_units + profit
    if outcome == "loss":
        return -stake_units, 0.0
    if outcome in ("push", "void"):
        return 0.0, stake_units

    raise ValueError(f"Unsupported outcome: {outcome}")

# --- quick tests ---
if __name__ == "__main__":
    # Even money examples
    assert round(to_decimal("american", -100), 2) == 2.00
    assert round(to_decimal("american",  100), 2) == 2.00
    # Profit calc
    pnl, payout = settle_ticket(2.0, "american", -110, "win")  # stake 2u at -110
    # Profit should be ~1.818u, payout ~3.818u
    assert round(pnl, 3) == round(2 * (american_to_decimal(-110) - 1.0), 3)
    assert round(payout, 3) == round(2 + pnl, 3)
    # Push
    assert settle_ticket(1.5, "decimal", 1.95, "push") == (0.0, 1.5)
    # Loss
    assert settle_ticket(1.0, "fraction", "10/11", "loss") == (-1.0, 0.0)
