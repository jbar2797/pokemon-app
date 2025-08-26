from __future__ import annotations

from datetime import date

import pandas as pd

from poke_pricer.analytics.backtest import backtest_momentum_topk


def test_backtest_handles_tiny_dataset() -> None:
    df = pd.DataFrame(
        {
            "card_id": [1, 1],
            "name": ["Bulbasaur", "Bulbasaur"],
            "set_code": ["BASE", "BASE"],
            "number": ["44/102", "44/102"],
            "date": [pd.to_datetime(date(2025, 1, 1)), pd.to_datetime(date(2025, 1, 2))],
            "source": ["csv", "csv"],
            "price": [5.10, 5.25],
        }
    )

    bt = backtest_momentum_topk(df, lookback=14, top_k=1)
    # Should not raise, and should return expected columns even if empty
    assert list(bt.columns) == ["date", "portfolio_return", "equity"]
