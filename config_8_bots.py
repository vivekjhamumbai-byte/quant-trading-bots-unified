"""
8-BOT UNIFIED CONFIGURATION

All 8 Trading Bots with Paper Mode Settings
Real Prices + Simulated Orders (Zero Capital Risk)

Bots:
1. O V NIFTY (Oliver Velez NIFTY)
2. SENSEX Hero-Zero (Daily strangle)
3. ORB Lite (Quick range breakout)
4. ORB-OV (Opening range / Power bar)
5. Signal Bot (Multi-indicator signals)
6. GBI-RBI (Momentum-based)
7. Trail SL (Trailing stop strategy)
8. Scalper Bot (High-frequency scalping)

Mode: PAPER (Real prices, simulated fills, zero risk)
Capital per Bot: ₹500,000
Total Paper Capital: ₹4,000,000 (across all 8 bots)
"""

import os

# =========================================================================
# MODE SETTINGS (PAPER MODE - ZERO RISK)
# =========================================================================
MODE = "paper"  # "backtest" | "paper" | "live"
LIVE_MODE_ENABLED = False  # Paper fills only
PAPER_TRADING = True
REAL_PRICES = True  # Real prices from mStock, simulated fills

# =========================================================================
# CAPITAL ALLOCATION (8 BOTS)
# =========================================================================
CAPITAL_PER_BOT = 500_000  # ₹500,000 per bot
TOTAL_PAPER_CAPITAL = 4_000_000  # ₹40 lakh across 8 bots

# =========================================================================
# RISK SETTINGS (ALL BOTS)
# =========================================================================
MAX_INVESTED_PER_TRADE = 35_000  # ₹35,000 max deployed
HARD_STOP_PCT = 0.08  # 8% hard stop = ₹2,800 max risk
DAILY_LOSS_LIMIT_PCT = 0.0  # No daily limit (test freely)
MAX_CONCURRENT_POSITIONS = 3  # Max 3 simultaneous positions

# =========================================================================
# BOT CONFIGURATION (ALL 8 BOTS)
# =========================================================================
BOTS_CONFIG = {
    "ov_nifty": {
        "name": "O V NIFTY",
        "path": "strategies/ov_nifty",
        "main_file": "ov_nifty_bot.py",
        "symbol": "NIFTY",
        "timeframe": 2,  # 2-minute bars
        "enabled": True,
        "capital": 500_000,
    },
    "sensex_hero_zero": {
        "name": "SENSEX Hero-Zero",
        "path": "strategies/sensex_hero_zero",
        "main_file": "sensex_hero_zero_bot.py",
        "symbol": "SENSEX",
        "timeframe": 1440,  # 1-day (single trade at 3:10 PM)
        "enabled": True,
        "capital": 500_000,
    },
    "orb_lite": {
        "name": "ORB Lite",
        "path": "strategies/orb_lite",
        "main_file": "orb_lite_bot.py",
        "symbol": "NIFTY",
        "timeframe": 2,  # 2-minute bars
        "enabled": True,
        "capital": 500_000,
    },
    "orb_ov": {
        "name": "ORB-OV",
        "path": "strategies/orb_ov",
        "main_file": "orb_ov_bot.py",
        "symbol": "NIFTY",
        "timeframe": 2,  # 2-minute bars
        "enabled": True,
        "capital": 500_000,
    },
    "signals_bot": {
        "name": "Signal Bot",
        "path": "strategies/signals_bot",
        "main_file": "signals_bot.py",
        "symbol": "NIFTY",
        "timeframe": 2,  # 2-minute bars
        "enabled": True,
        "capital": 500_000,
    },
    "gbi_rbi": {
        "name": "GBI-RBI",
        "path": "strategies/gbi_rbi",
        "main_file": "gbi_rbi_bot.py",
        "symbol": "NIFTY",
        "timeframe": 2,  # 2-minute bars
        "enabled": True,
        "capital": 500_000,
    },
    "trail_sl": {
        "name": "Trail SL",
        "path": "strategies/trail_sl",
        "main_file": "trail_sl_bot.py",
        "symbol": "NIFTY",
        "timeframe": 2,  # 2-minute bars
        "enabled": True,
        "capital": 500_000,
    },
    "scalper_bot": {
        "name": "Scalper Bot",
        "path": "strategies/scalper_bot",
        "main_file": "scalper_bot.py",
        "symbol": "NIFTY",
        "timeframe": 1,  # 1-minute bars
        "enabled": True,
        "capital": 500_000,
    },
}

# =========================================================================
# INSTRUMENTS
# =========================================================================
INDEX_INSTRUMENTS = ["NIFTY", "BANKNIFTY", "SENSEX"]
STOCK_INSTRUMENTS = []

# =========================================================================
# EXECUTION SETTINGS
# =========================================================================
TRADE_VIA = "options"  # "options" | "futures_or_equity"
OPTION_TYPE_FOR_DIRECTION = {"LONG": "CE", "SHORT": "PE"}
OPTION_EXPIRY_TYPE = "current_week"

STRIKE_INTERVAL = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "SENSEX": 100,
}

# =========================================================================
# STRATEGY PARAMETERS
# =========================================================================
BAR_INTERVAL_MINUTES = 2
TICK_POLL_SECONDS = 5
MA_SHORT_PERIOD = 20
MA_LONG_PERIOD = 200
WARMUP_HISTORY_DAYS = 5

# =========================================================================
# MARKET HOURS
# =========================================================================
MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"
TRADING_START = "09:00"  # Allow 15 min buffer
POSITION_CLOSE_TIME = "15:10"  # Force close all positions at 15:10

# =========================================================================
# CREDENTIALS (FROM ENVIRONMENT)
# =========================================================================
MSTOCK_USER_ID = os.environ.get("MSTOCK_USER_ID", "")
MSTOCK_PASSWORD = os.environ.get("MSTOCK_PASSWORD", "")
MSTOCK_API_KEY = os.environ.get("MSTOCK_API_KEY", "")
MSTOCK_TOTP_CODE = os.environ.get("MSTOCK_TOTP_CODE", "")

# =========================================================================
# LOGGING & MONITORING
# =========================================================================
DASHBOARD_LOG_DIR = "logs/dashboard"
ENABLE_HEALTH_MONITORING = True
ENABLE_POSITION_RECONCILIATION = True
ENABLE_DUPLICATE_ORDER_CHECK = True
ENABLE_AUTO_RECONNECTION = True

# =========================================================================
# PAPER MODE SETTINGS
# =========================================================================
PAPER_SLIPPAGE_PCT = 0.01  # 1% slippage simulation
PAPER_FEE_PCT = 0.001  # 0.1% fee simulation
SIMULATE_REALISTIC_FILLS = True  # Realistic fill simulation

# =========================================================================
# KILL SWITCH & SAFETY
# =========================================================================
KILL_SWITCH_CHECK_INTERVAL = 5  # Check every 5 seconds
KILL_SWITCH_DIR = "kill_switch"
POSITION_RECONCILIATION_CHECK = True

# =========================================================================
# SUMMARY
# =========================================================================
"""
PAPER MODE TESTING - 8 BOTS

Active Bots:
1. O V NIFTY - NIFTY pattern trading
2. SENSEX Hero-Zero - Daily strangle
3. ORB Lite - Quick breakout
4. ORB-OV - Power bar trading
5. Signal Bot - Multi-signal
6. GBI-RBI - Momentum
7. Trail SL - Trailing stops
8. Scalper Bot - High-frequency

Capital:
- Per Bot: ₹500,000 (paper only)
- Total: ₹4,000,000 (paper only)
- Risk: ₹0 (ZERO - completely safe)

Mode: PAPER
Prices: REAL (mStock API)
Orders: SIMULATED (paper fills)
P&L: ACCURATE (shows true profitability)

Test Duration: As long as needed
Target: 20-40 trading days
Success Metric: Win rate > 55% + consistent profit

When ready: Say "Go Live" to switch to real trading
"""
