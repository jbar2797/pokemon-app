from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd


@dataclass(frozen=True)
class SlackResult:
    ok: bool
    status: int
    body: str


def _fmt_pct(x: Any) -> str:
    try:
        return f"{float(x):.2%}"
    except Exception:
        return str(x)


def _fmt_price(x: Any) -> str:
    try:
        return f"{float(x):.2f}"
    except Exception:
        return str(x)


def build_alerts_text(df: pd.DataFrame, max_rows: int = 10) -> str:
    """
    Convert alerts DataFrame into a plain-text Slack message.
    Expects columns: name,set_code,number,source,price,return_1d,flag,date
    """
    if df.empty:
        return ":white_check_mark: No alerts for the selected day."

    rows = df.head(max_rows).to_dict(orient="records")
    lines: list[str] = []
    lines.append(f"*Top alerts* (showing up to {min(max_rows, len(rows))}):")
    for r in rows:
        name = r.get("name", "")
        set_code = r.get("set_code", "")
        number = r.get("number", "")
        src = r.get("source", "")
        price = _fmt_price(r.get("price", ""))
        ret = _fmt_pct(r.get("return_1d", ""))
        flag = r.get("flag", "")
        date = r.get("date", "")
        lines.append(f"• *{name}* [{set_code} #{number}] {src} ${price} Δ1d={ret} ({flag}) {date}")

    if len(df) > max_rows:
        lines.append(f"…and {len(df) - max_rows} more.")
    return "\n".join(lines)


def post_text(webhook_url: str, text: str) -> SlackResult:
    payload = json.dumps({"text": text}).encode("utf-8")
    req = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return SlackResult(ok=200 <= resp.status < 300, status=resp.status, body=body)
