"""JOS MASTER - PAPER_CAPITAL_INTELLIGENCE single-source runtime.

Real-time market feed (yfinance) + news feed (RSS) + scoring + ranking +
sector strength analysis + market state classification + PAPER portfolio +
forward simulation (historical bootstrap) + adaptive learning stats +
ledger persistence + intraday/close report loop, integrated into one
runnable file.

Run (continuous, local):
    cd C:\\JOS_OS
    python .\\JOS_MASTER.py

Run (single intraday pass, cloud/CI):
    python JOS_MASTER.py --once

Run (end-of-day close / CEO report, cloud/CI):
    python JOS_MASTER.py --close

Ledger (persisted under ./ledger/, committed back to the repo by CI):
- signals_log.jsonl       : every PAPER_BUY signal (Signal DB)
- results_log.jsonl       : realized return per evaluated signal (Result DB)
- market_log.jsonl        : raw market snapshots (Market DB)
- news_log.jsonl          : raw news headlines (News DB)
- learning_stats.json      : rolling equity curve / win rate / drawdown
- tomorrow_watchlist.json  : next-session TOP candidates

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
from pathlib import Path

# =====================================
# CONFIG
# =====================================

WATCHLIST = {
    "NVDA": "AI_SEMI",
    "AMD": "AI_SEMI",
    "005930.KS": "AI_SEMI",
    "000660.KS": "AI_SEMI",

    "AAPL": "TECH_PLATFORM",
    "MSFT": "TECH_PLATFORM",
    "GOOGL": "TECH_PLATFORM",
    "META": "TECH_PLATFORM",

    "TSLA": "EV_BATTERY",
    "373220.KS": "EV_BATTERY",
    "006400.KS": "EV_BATTERY",

    "207940.KS": "BIO",
    "MRNA": "BIO",
    "PFE": "BIO",

    "LMT": "DEFENSE",
    "012450.KS": "DEFENSE",

    "JPM": "FINANCE",
    "105560.KS": "FINANCE",
}

RSS = [
    "https://rss.donga.com/total.xml",
    "https://www.khan.co.kr/rss/rssdata/total_news.xml"
]

# Forward simulation engine
FORWARD_SIM_TRIALS = 1000
FORWARD_SIM_HORIZON_DAYS = 5
FORWARD_SIM_CANDIDATES = 10

# Tomorrow watchlist
TOMORROW_WATCHLIST_SIZE = 5

# Learning engine
EQUITY_CURVE_MAX = 90

# Result evaluation: cap network calls per run
MAX_EVAL_PER_RUN = 20


def sector_of(ticker):
    return WATCHLIST.get(ticker, "UNKNOWN")

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
# LEDGER (Signal / News / Market / Result DB)
# =====================================

BASE_DIR = Path(__file__).resolve().parent
LEDGER_DIR = BASE_DIR / "ledger"

SIGNALS_LOG = LEDGER_DIR / "signals_log.jsonl"
RESULTS_LOG = LEDGER_DIR / "results_log.jsonl"
NEWS_LOG = LEDGER_DIR / "news_log.jsonl"
MARKET_LOG = LEDGER_DIR / "market_log.jsonl"
LEARNING_FILE = LEDGER_DIR / "learning_stats.json"
WATCHLIST_FILE = LEDGER_DIR / "tomorrow_watchlist.json"


def ensure_ledger_dir():
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)


def append_jsonl(path, record):

    ensure_ledger_dir()

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path):

    if not path.exists():
        return []

    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass

    return rows


def load_json(path, default):

    if not path.exists():
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):

    ensure_ledger_dir()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =====================================
# MARKET
# =====================================

def market_feed():

    rows = []

    for ticker, sector in WATCHLIST.items():

        try:

            data = yf.Ticker(ticker)

            hist = data.history(period="5d")

            if len(hist) == 0:
                continue

            last = hist.iloc[-1]

            price = float(last["Close"])
            volume = float(last["Volume"])

            if len(hist) >= 2:
                prev_close = float(hist.iloc[-2]["Close"])
                change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0.0
            else:
                change_pct = 0.0

            rows.append({
                "ticker": ticker,
                "sector": sector,
                "price": price,
                "volume": volume,
                "change_pct": change_pct
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
            "sector": row["sector"],
            "score": score_market(row),
            "price": row["price"],
            "volume": row["volume"],
            "change_pct": row.get("change_pct", 0.0)
        })

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return ranking

# =====================================
# MARKET STATE ENGINE
# =====================================

def market_state_engine(ranking):

    if not ranking:
        return "UNKNOWN"

    changes = [row["change_pct"] for row in ranking]

    avg_change = sum(changes) / len(changes)
    spread = max(changes) - min(changes)

    if spread >= 4.0:
        return "RISK_OFF"

    if avg_change >= 1.5:
        return "EUPHORIA"

    if avg_change >= 0.3:
        return "TREND_UP"

    if avg_change <= -1.5:
        return "PANIC"

    if avg_change <= -0.3:
        return "TREND_DOWN"

    return "SIDEWAYS"

# =====================================
# SECTOR STRENGTH ENGINE
# =====================================

def sector_strength_engine(ranking):

    sectors = {}

    for row in ranking:
        sectors.setdefault(row["sector"], []).append(row["change_pct"])

    strength = []

    for sector, changes in sectors.items():
        strength.append({
            "sector": sector,
            "avg_change_pct": sum(changes) / len(changes),
            "count": len(changes)
        })

    strength.sort(
        key=lambda x: x["avg_change_pct"],
        reverse=True
    )

    return strength

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
            "sector": top["sector"],
            "score": top["score"],
            "price": top["price"],
            "action": "PAPER_BUY",
            "ts": datetime.now(
                timezone.utc
            ).isoformat()
        }

        STATE["paper_trades"].append(trade)
        append_jsonl(SIGNALS_LOG, trade)

# =====================================
# PORTFOLIO
# =====================================

def portfolio_engine():

    portfolio = {}

    for trade in STATE["paper_trades"]:

        t = trade["ticker"]

        portfolio[t] = portfolio.get(t, 0) + 1

    STATE["portfolio"] = portfolio


def portfolio_from_ledger():

    portfolio = {}

    for row in read_jsonl(SIGNALS_LOG):

        t = row.get("ticker")

        if not t:
            continue

        portfolio[t] = portfolio.get(t, 0) + 1

    return portfolio

# =====================================
# FORWARD SIMULATION ENGINE (historical bootstrap)
# =====================================

def forward_simulation(ticker, trials=FORWARD_SIM_TRIALS, horizon_days=FORWARD_SIM_HORIZON_DAYS):

    try:

        hist = yf.Ticker(ticker).history(period="3mo")

        closes = hist["Close"].tolist()

        if len(closes) < 2:
            return None

        returns = []

        for i in range(1, len(closes)):
            prev = closes[i - 1]
            if prev:
                returns.append((closes[i] - prev) / prev)

        if not returns:
            return None

        outcomes = []

        for _ in range(trials):

            cum = 1.0

            for _ in range(horizon_days):
                cum *= (1 + random.choice(returns))

            outcomes.append(cum - 1)

        p_up = sum(1 for o in outcomes if o > 0) / len(outcomes)
        expected_return = sum(outcomes) / len(outcomes)

        return {
            "ticker": ticker,
            "p_up": p_up,
            "expected_return_pct": expected_return * 100,
            "trials": trials,
            "horizon_days": horizon_days
        }

    except Exception:
        return None

# =====================================
# LEARNING ENGINE (Result DB evaluation + rolling stats)
# =====================================

def evaluate_today_signals():

    signals = read_jsonl(SIGNALS_LOG)

    if not signals:
        return []

    evaluated_ts = {row.get("signal_ts") for row in read_jsonl(RESULTS_LOG)}

    results = []

    for sig in signals:

        if len(results) >= MAX_EVAL_PER_RUN:
            break

        ts = sig.get("ts")

        if ts in evaluated_ts:
            continue

        ticker = sig.get("ticker")
        entry_price = sig.get("price")

        if not ticker or not entry_price:
            continue

        try:
            hist = yf.Ticker(ticker).history(period="1d")
            if len(hist) == 0:
                continue
            current_price = float(hist.iloc[-1]["Close"])
        except Exception:
            continue

        return_pct = ((current_price - entry_price) / entry_price) * 100

        result = {
            "signal_ts": ts,
            "ticker": ticker,
            "sector": sig.get("sector"),
            "entry_price": entry_price,
            "exit_price": current_price,
            "return_pct": return_pct,
            "win": return_pct > 0,
            "ts": datetime.now(timezone.utc).isoformat()
        }

        append_jsonl(RESULTS_LOG, result)
        results.append(result)

    return results


def update_learning_stats(new_results):

    stats = load_json(LEARNING_FILE, {
        "equity_curve": [1.0],
        "cumulative_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "win_rate_pct": 0.0,
        "total_trades": 0,
        "wins": 0,
        "updated_ts": None
    })

    equity_curve = stats.get("equity_curve", [1.0])
    wins = stats.get("wins", 0)
    total_trades = stats.get("total_trades", 0)

    for r in new_results:
        equity_curve.append(equity_curve[-1] * (1 + r["return_pct"] / 100))
        total_trades += 1
        if r["win"]:
            wins += 1

    if len(equity_curve) > EQUITY_CURVE_MAX:
        equity_curve = equity_curve[-EQUITY_CURVE_MAX:]

    peak = equity_curve[0]
    max_drawdown = 0.0

    for e in equity_curve:
        if e > peak:
            peak = e
        drawdown = ((peak - e) / peak * 100) if peak else 0.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    cumulative_return = (equity_curve[-1] - 1.0) * 100
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0

    stats = {
        "equity_curve": equity_curve,
        "cumulative_return_pct": cumulative_return,
        "max_drawdown_pct": max_drawdown,
        "win_rate_pct": win_rate,
        "total_trades": total_trades,
        "wins": wins,
        "updated_ts": datetime.now(timezone.utc).isoformat()
    }

    save_json(LEARNING_FILE, stats)

    return stats

# =====================================
# TOMORROW WATCHLIST ENGINE
# =====================================

def build_tomorrow_watchlist(ranking, sector_strength, top_n=TOMORROW_WATCHLIST_SIZE):

    sector_avg = {row["sector"]: row["avg_change_pct"] for row in sector_strength}

    candidates = ranking[:FORWARD_SIM_CANDIDATES]

    composite = []

    for row in candidates:

        sim = forward_simulation(row["ticker"])
        p_up = sim["p_up"] if sim else 0.5

        sector_change = sector_avg.get(row["sector"], 0.0)

        composite_score = (
            row["score"] * 0.4
            + sector_change * 10 * 0.2
            + p_up * 100 * 0.4
        )

        composite.append({
            "ticker": row["ticker"],
            "sector": row["sector"],
            "score": row["score"],
            "sector_avg_change_pct": sector_change,
            "p_up": p_up,
            "composite_score": composite_score
        })

    composite.sort(
        key=lambda x: x["composite_score"],
        reverse=True
    )

    top = composite[:top_n]

    save_json(WATCHLIST_FILE, {
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "top": top
    })

    return top

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
        "market_state: " + report_data["market_state"],
        "events: " + str(report_data["events"]),
        "signals: " + str(report_data["signals"]),
        "paper_trades: " + str(report_data["paper_trades"])
    ]

    top5 = report_data["top5"]

    if top5:
        lines.append("")
        lines.append("[TOP%s RANKING]" % len(top5))
        for r in top5:
            lines.append(
                "  %s (%s) score=%s price=%s change=%.2f%%" % (
                    r["ticker"], r["sector"], r["score"], r["price"], r.get("change_pct", 0.0)
                )
            )

    if report_data["portfolio"]:
        lines.append("")
        lines.append(
            "portfolio: " + json.dumps(report_data["portfolio"], ensure_ascii=False)
        )

    return "\n".join(lines)


def format_close_report(close_data):

    lines = [
        "JOS PAPER CAPITAL - CLOSE REPORT (CEO)",
        "PAPER_ONLY TRUE / LIVE_TRADE BLOCKED / CAPITAL_SCALE BLOCKED / KIS_ORDER_GATE BLOCKED",
        "ts: " + close_data["ts"],
        "market_state: " + close_data["market_state"]
    ]

    lines.append("")
    lines.append("[TOP5 RANKING]")
    for r in close_data["top5"]:
        lines.append(
            "  %s (%s) score=%s change=%.2f%%" % (
                r["ticker"], r["sector"], r["score"], r["change_pct"]
            )
        )

    lines.append("")
    lines.append("[SECTOR STRENGTH]")
    for s in close_data["sector_strength"]:
        lines.append(
            "  %s avg_change=%.2f%% (n=%s)" % (
                s["sector"], s["avg_change_pct"], s["count"]
            )
        )

    lines.append("")
    lines.append("[TODAY RESULTS]")
    lines.append("  evaluated_signals: " + str(len(close_data["evaluated_results"])))
    for r in close_data["evaluated_results"]:
        lines.append(
            "  %s entry=%.2f exit=%.2f return=%.2f%% %s" % (
                r["ticker"], r["entry_price"], r["exit_price"],
                r["return_pct"], "WIN" if r["win"] else "LOSS"
            )
        )

    lines.append("")
    lines.append("[LEARNING STATS]")
    learn = close_data["learning_stats"]
    lines.append("  total_trades: " + str(learn["total_trades"]))
    lines.append("  win_rate: %.1f%%" % learn["win_rate_pct"])
    lines.append("  cumulative_return: %.2f%%" % learn["cumulative_return_pct"])
    lines.append("  max_drawdown: %.2f%%" % learn["max_drawdown_pct"])

    lines.append("")
    lines.append("[TOMORROW WATCHLIST TOP%s]" % len(close_data["tomorrow_watchlist"]))
    for w in close_data["tomorrow_watchlist"]:
        lines.append(
            "  %s (%s) composite=%.2f p_up=%.2f sector_change=%.2f%%" % (
                w["ticker"], w["sector"], w["composite_score"],
                w["p_up"], w["sector_avg_change_pct"]
            )
        )

    if close_data["news"]:
        lines.append("")
        lines.append("[NEWS HEADLINES]")
        for n in close_data["news"][:5]:
            lines.append("  - " + n)

    lines.append("")
    lines.append("portfolio_total_signals: " + str(close_data["portfolio_total"]))

    return "\n".join(lines)

# =====================================
# REPORT (intraday)
# =====================================

def report():

    ranking = STATE["rankings"]

    report_data = {

        "events":
            len(STATE["events"]),

        "signals":
            len(STATE["signals"]),

        "paper_trades":
            len(STATE["paper_trades"]),

        "portfolio":
            STATE["portfolio"],

        "market_state":
            market_state_engine(ranking),

        "top5":
            ranking[:5],

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

def collect_cycle_data():

    market = market_feed()

    news = news_feed()

    ranking = rank_engine(
        market
    )

    STATE["rankings"] = ranking

    for row in market:

        STATE["events"].append(row)

        append_jsonl(MARKET_LOG, row)

        if score_market(row) >= 60:
            STATE["signals"].append(
                row
            )

    for n in news:

        STATE["events"].append(
            {"news": n}
        )

        append_jsonl(NEWS_LOG, {
            "headline": n,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    return market, news, ranking


def run_cycle():

    market, news, ranking = collect_cycle_data()

    paper_engine(
        ranking
    )

    portfolio_engine()

    report()


def run_close():

    market, news, ranking = collect_cycle_data()

    market_state = market_state_engine(ranking)
    sector_strength = sector_strength_engine(ranking)

    evaluated_results = evaluate_today_signals()
    learning_stats = update_learning_stats(evaluated_results)

    paper_engine(ranking)
    portfolio_engine()

    tomorrow_watchlist = build_tomorrow_watchlist(ranking, sector_strength)

    portfolio_total = sum(portfolio_from_ledger().values())

    close_data = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "market_state": market_state,
        "top5": ranking[:5],
        "sector_strength": sector_strength,
        "evaluated_results": evaluated_results,
        "learning_stats": learning_stats,
        "tomorrow_watchlist": tomorrow_watchlist,
        "news": news,
        "portfolio_total": portfolio_total
    }

    print()
    print("=" * 50)
    print("JOS CLOSE REPORT")
    print("=" * 50)

    print(
        json.dumps(
            close_data,
            indent=2,
            ensure_ascii=False
        )
    )

    send_telegram(
        format_close_report(close_data)
    )


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--close", action="store_true")
    args = parser.parse_args()

    print("=== JOS MASTER START ===")

    if args.close:
        run_close()
        return

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
