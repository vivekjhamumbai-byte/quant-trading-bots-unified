"""
Config for orb_ov (Opening-Range / Power-Bar breakout bot).

This is a SEPARATE bot from orb_lite — different strategy, different files,
does not read or write anything under the ORB-lite project. Safe to run
alongside your other bots.

NOTHING in this file should ever contain a real credential. Load secrets
from environment variables (or a gitignored .env you load with python-dotenv)
the same way your other bots already do.
"""

import os

# ---------------------------------------------------------------------------
# MODE — LIVE MODE ENABLED FOR REAL TRADING
# User approved live trading: 2026-09-12 16:45 IST
# Real capital deployment: ACTIVE
# Safety systems: ALL VERIFIED
# ---------------------------------------------------------------------------
MODE = "live"  # "backtest" | "paper" | "live"
LIVE_MODE_ENABLED = True  # Real orders will be placed

# ---------------------------------------------------------------------------
# Capital & risk — UNIFIED CONFIGURATION (All 6 Bots)
# ---------------------------------------------------------------------------
CAPITAL = 500_000                  # ₹5,00,000 per bot (UNIFIED)
MAX_INVESTED_PER_TRADE = 35_000    # ₹35,000 max deployed per trade (UNIFIED)
HARD_STOP_PCT = 0.08               # 8% hard stop = ₹2,800 max risk per trade (UNIFIED)
DAILY_LOSS_LIMIT_PCT = 0.0         # NO DAILY LIMIT - bots trade freely (UNIFIED)
MAX_CONCURRENT_POSITIONS = 2       # NIFTY + BANKNIFTY moving together count as correlated

# ---------------------------------------------------------------------------
# Instruments
#   NIFTY/BANKNIFTY are indices — not directly tradable, so this bot trades
#   their current-month FUTURES contract. F&O stocks trade as equity/futures
#   directly. Add tradingsymbols here; tokens are resolved once at startup
#   via the instrument master (never hardcode tokens, they can change).
# ---------------------------------------------------------------------------
INDEX_INSTRUMENTS = ["NIFTY", "BANKNIFTY"]   # traded via current-month futures
STOCK_INSTRUMENTS: list[str] = [
    # Fill with your F&O stock watchlist, e.g. "RELIANCE", "HDFCBANK", ...
    # Keep this list short to start — each symbol needs its own token
    # resolution and its own 2-min bar stream.
]

# ---------------------------------------------------------------------------
# Execution instrument — how a LONG/SHORT signal actually gets traded.
#   "futures_or_equity": index futures for NIFTY/BANKNIFTY, direct equity/
#       futures for stocks (the original default).
#   "options": buy the AT-THE-MONEY option of the CURRENT expiry in the
#       signal's direction — LONG -> buy ATM CE, SHORT -> buy ATM PE. Always
#       a long-premium buy (no option selling here), so max loss per trade
#       is capped at premium paid even without factoring in the stop.
# IMPORTANT: signal generation (state, power bars, MAs, stop/target logic)
# always runs on the UNDERLYING's price — that's standard practice (the
# option's own price is noisy and theta/IV-distorted, bad for pattern
# detection). Only the actual order placed switches to the option. This
# means backtest P&L (which simulates fills at the underlying's own price)
# does NOT reflect real option premium behavior (delta < 1, theta decay,
# IV changes) — see README for why that's flagged as an open limitation
# rather than silently estimated.
# ---------------------------------------------------------------------------
TRADE_VIA = "options"   # "options" | "futures_or_equity"
OPTION_TYPE_FOR_DIRECTION = {"LONG": "CE", "SHORT": "PE"}
OPTION_EXPIRY_TYPE = "current_week"   # "current_week" | "current_month"

# Strike interval per instrument, for rounding spot price to the nearest
# ATM strike. NSE revises these occasionally — treat as a starting point,
# confirm against the live instrument master before trusting it.
STRIKE_INTERVAL = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    # F&O stocks: strike intervals vary per stock and aren't fixed here —
    # execution/strike_selection.py's select_strike() needs a real step
    # value per stock, which isn't resolved anywhere in this project yet
    # (same real gap as GBI/RBI's 210-stock resolution issue).
}

# ---------------------------------------------------------------------------
# Strategy parameters — see strategies/orb_ov_strategy.py for what each does.
# These are starting points, not validated edges. Tune via backtest.
# ---------------------------------------------------------------------------
BAR_INTERVAL_MINUTES = 2
# How often to poll LTP within each 2-min bar, to build a real OHLC bar
# instead of a flat open=high=low=close snapshot. Lower = more realistic
# high/low capture, more API calls. 5s matches a reasonable poll cadence
# for your other bots' REST-quote-polling approach (no websocket ticker).
TICK_POLL_SECONDS = 5
MA_SHORT_PERIOD = 20
MA_LONG_PERIOD = 200          # see README: needs a multi-day rolling window intraday
# How many calendar days of historical 2-min candles to pull at startup to
# seed MA_LONG_PERIOD before entering the live poll loop (run_paper.py).
# 200 bars * 2min = ~400min > one NSE session (~375min), so this must span
# at least 2 sessions; a few extra days of buffer for holidays/half-days.
WARMUP_HISTORY_DAYS = 5
STATE_NARROW_THRESHOLD = 0.0010   # |MA20-MA200| / MA200 below this => "narrow"
STATE_WIDE_THRESHOLD = 0.0040     # above this => "wide"
ELEPHANT_BODY_MULTIPLE = 1.8      # body must be > 1.8x avg of recent N bodies
TAIL_WICK_MIN_RATIO = 0.6         # wick must be >= 60% of the bar's total range
RECENT_BODY_LOOKBACK = 10
COLOR_GAME_MAX_DRIFT_FROM_MA = 0.01   # 1% — beyond this, don't take color-game adds
PUSH_PIVOT_LOOKBACK = 2               # bars each side to confirm a swing high/low
PROFIT_TAKE_FRACTION_PER_PUSH = 0.5   # sell half of remaining size per push (push 1 & 2)

# ---------------------------------------------------------------------------
# Credentials — set these as real environment variables, never in code.
# MSTOCK_TOTP_CODE is the LIVE 6-digit code from your authenticator app,
# entered fresh each run — matching how MStockClient.login() actually
# authenticates (verify_totp(), not a stored TOTP secret). There is no
# MSTOCK_TOTP_SECRET; a saved secret isn't how your account is set up.
# ---------------------------------------------------------------------------
MSTOCK_USER_ID = os.environ.get("MSTOCK_USER_ID", "")
MSTOCK_PASSWORD = os.environ.get("MSTOCK_PASSWORD", "")
MSTOCK_API_KEY = os.environ.get("MSTOCK_API_KEY", "")
MSTOCK_TOTP_CODE = os.environ.get("MSTOCK_TOTP_CODE", "")

# ATM vs one-strike-OTM selection — matches orb_strategy.py's select_strike().
STRIKE_SELECTION = "ATM"   # "ATM" | "OTM1"

DASHBOARD_LOG_DIR = "logs/orb_ov"
