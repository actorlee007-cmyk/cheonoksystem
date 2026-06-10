"""JOS MASTER - PAPER_CAPITAL_INTELLIGENCE single-source runtime.

Real-time market feed (yfinance) + news feed (RSS) + scoring + ranking +
PAPER portfolio + live report loop, integrated into one runnable file.

Run (continuous, local):
    cd C:\\JOS_OS
    python .\\JOS_MASTER.py

Run (single pass, cloud/CI):
    python JOS_MASTER.py --once

Reporting:
- Each report is also sent to Telegram via CHEONOK_TELEGRAM_BOT_TOKEN /
  CHEONOK_TELEGRAM_CHAT_ID (same secrets as CHEONOK Supreme Master OS).
  If the secrets are missing, sending is skipped (HOLD_TELEGRAM_SECRETS_MISSING).

Safety:
- PAPER_ONLY TRUE
- LIVE_TRADE BLOCKED
- CAPITAL_SCALE BLOCKED
- KIS_ORDER_GATE BLOCKED
- No order execution. No broker connection. PAPER_BUY signals only.
"""

import argparse
import os
import time
import json
import random
import urllib.parse
import urllib.request
import feedparser
import yfinance as yf

from datetime import datetime, timezone

# =====================================
# CONFIG
# =====================================

WATCHLIST = [
    "AAPL",
    "TSLA",
    "NVDA",
    "MSFT",
    "005930.KS"
]

RSS = [
    "https://rss.donga.com/total.xml",
    "https://www.khan.co.kr/rss/rssdata/total_news.xml"
]

# =====================================
# STATE
# =====================================

STATE = {
    "events": [],
    "signals": [],
    "paper_trades": [],
    "rankings": [],
    "portfolio": [],
    "reports": []
}

# =====================================
# MARKET
# =====================================

def market_feed():

    rows = []

    for ticker in WATCHLIST:

        try:

            data = yf.Ticker(ticker)

            hist = data.history(period="1d")

            if len(hist) == 0:
                continue

            last = hist.iloc[-1]

            rows.append({
                "ticker": ticker,
                "price": float(last["Close"]),
                "volume": float(last["Volume"])
            })

        except Exception:
            pass

    return rows

# =====================================
# NEWS
# =====================================

def news_feed():

    news = []

    for url in RSS:

        try:

            feed = feedparser.parse(url)

            for item in feed.entries[:5]:

                news.append(item.title)

        except Exception:
            pass

    return news

# =====================================
# SCORE
# =====================================

def score_market(row):

    score = 0

    volume = row["volume"]

    if volume > 100000:
        score += 30

    if volume > 500000:
        score += 30

    if volume > 1000000:
        score += 40

    return score

# =====================================
# RANK ENGINE
# =====================================

def rank_engine(market):

    ranking = []

    for row in market:

        ranking.append({
            "ticker": row["ticker"],
            "score": score_market(row),
            "price": row["price"],
            "volume": row["volume"]
        })

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return ranking

# =====================================
# PAPER ENGINE
# =====================================

def paper_engine(ranking):

    if len(ranking) == 0:
        return

    top = ranking[0]

    if top["score"] >= 60:

        trade = {
            "ticker": top["ticker"],
            "score": top["score"],
            "action": "PAPER_BUY",
            "ts": datetime.now(
                timezone.utc
            ).isoformat()
        }

        STATE["paper_trades"].append(trade)

# =====================================
# PORTFOLIO
# =====================================

def portfolio_engine():

    portfolio = {}

    for trade in STATE["paper_trades"]:

        t = trade["ticker"]

        portfolio[t] = portfolio.get(t, 0) + 1

    STATE["portfolio"] = portfolio

# =====================================
# TELEGRAM
# =====================================

def send_telegram(text):

    token = os.environ.get("CHEONOK_TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("CHEONOK_TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print("HOLD_TELEGRAM_SECRETS_MISSING")
        print(text)
        return False

    for i in range(0, len(text), 3500):

        chunk = text[i:i + 3500]

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": "true"
        }).encode("utf-8")

        req = urllib.request.Request(url, data=data, method="POST")

        with urllib.request.urlopen(req, timeout=30) as res:
            res.read()

    return True


def format_report_text(report_data):

    lines = [
        "JOS PAPER CAPITAL REPORT",
        "PAPER_ONLY TRUE / LIVE_TRADE BLOCKED",
        "ts: " + report_data["ts"],
        "events: " + str(report_data["events"]),
        "signals: " + str(report_data["signals"]),
        "paper_trades: " + str(report_data["paper_trades"])
    ]

    top = report_data["top_rank"]

    if top:
        lines.append(
            "top_rank: %s score=%s price=%s volume=%s" % (
                top["ticker"], top["score"], top["price"], top["volume"]
            )
        )

    if report_data["portfolio"]:
        lines.append(
            "portfolio: " + json.dumps(report_data["portfolio"], ensure_ascii=False)
        )

    return "\n".join(lines)

# =====================================
# REPORT
# =====================================

def report():

    report_data = {

        "events":
            len(STATE["events"]),

        "signals":
            len(STATE["signals"]),

        "paper_trades":
            len(STATE["paper_trades"]),

        "portfolio":
            STATE["portfolio"],

        "top_rank":

            STATE["rankings"][0]
            if len(STATE["rankings"]) > 0
            else None,

        "ts":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    STATE["reports"].append(
        report_data
    )

    print()
    print("=" * 50)
    print("JOS REPORT")
    print("=" * 50)

    print(
        json.dumps(
            report_data,
            indent=2,
            ensure_ascii=False
        )
    )

    send_telegram(
        format_report_text(report_data)
    )

# =====================================
# MAIN LOOP
# =====================================

def run_cycle():

    market = market_feed()

    news = news_feed()

    ranking = rank_engine(
        market
    )

    STATE["rankings"] = ranking

    for row in market:

        STATE["events"].append(row)

        if score_market(row) >= 60:
            STATE["signals"].append(
                row
            )

    for n in news:

        STATE["events"].append(
            {"news": n}
        )

    paper_engine(
        ranking
    )

    portfolio_engine()

    report()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    print("=== JOS MASTER START ===")

    if args.once:
        run_cycle()
        return

    while True:

        run_cycle()

        time.sleep(60)

# =====================================
# RUN
# =====================================

if __name__ == "__main__":
    main()
