# Bot 8.1.2026 — trading fleet

An intraday options-buying fleet for Indian index/stock F&O, running against
the mStock (Type-B) API. Four strategy bots plus a trailing-SL manager and a
shared web dashboard, all sharing one risk/exit layer, one credential module,
and one trade ledger.

> This README replaced an unrelated file (the "Claude Counter" browser
> extension's README) that had been sitting here by accident — moved to
> `D:\Bot_Backups\bot_8.1.2026_cleanup_20260907\` on 2026-09-07.

---

## Status (2026-09-07)

All strategy bots and the dashboard run unattended via Windows Task
Scheduler, launching ~09:03–09:05 IST on trading days:

| Component | Scheduled task | Launcher | State |
|---|---|---|---|
| ORB-lite | `ORB Lite Bot` | `run_bot.bat` | Enabled |
| Signals Bot | `Signals Bot` | `run_signals_bot.bat` | Enabled |
| GBI/RBI | `GBI RBI Bot` | `gbi-rbi-bot\run_gbi_rbi.bat` | **Enabled** |
| ORB-OV | `ORB OV Bot` | `orb-ov-bot\run_orb_ov.bat` | Enabled |
| Trail SL | `Trail SL Bot` | `bot_page_paper\run_trail_sl.bat` | Enabled |
| Dashboard | `Trading Dashboard` | `run_dashboard.bat` | Enabled |

Support tasks: `GBI RBI Post-Start Health Check`, `Startup Trading Recovery`
(relaunches the fleet + dashboard after a reboot), `Stop All Bots 1520`
(square-off / shutdown at 15:20).

**GBI/RBI is re-enabled and live.** It was disabled for a period pending
four hardening blockers; those were completed and it was re-enabled on
2026-09-04, with its first live run on 2026-09-07. The scheduled task is
Enabled / Ready and executed today. (Ignore any older note calling it
"disabled pending blockers.")

Everything defaults to **paper mode** — see disclaimers.

---

## The four bots

| Bot | What it trades | Location |
|---|---|---|
| **ORB-lite** | Opening-range breakout on NIFTY / BANKNIFTY (underlying via near-month future), buys the ATM-ish CE/PE. | `vivek jha\vivek jha\bot.py`, `orb_strategy.py`, `config.py` |
| **Signals Bot** | Multi-indicator (VWAP reversion, RSI momentum, EMA crossover, Bollinger breakout) on indices + F&O stocks. Every entry needs manual approval on the dashboard popup. | `vivek jha\vivek jha\signals_bot.py`, `signals_config.py`, `indicators.py`, `bar_aggregator.py` |
| **GBI/RBI** | Green-Bar-Ignored / Red-Bar-Ignored price-action pattern, long CE/PE only, scanning indices + NSE F&O stocks. | `vivek jha\vivek jha\gbi-rbi-bot\` — `main.py`, `screener\scanner.py`, `strategies\`, `execution\` |
| **ORB-OV** | Opening-range + "elephant bar" / order-flow variant, trades the underlying/futures instrument's own bars. | `vivek jha\vivek jha\orb-ov-bot\` — `main.py`, `strategies\orb_ov_strategy.py`, `execution\` |

**Trail SL** (`vivek jha\vivek jha\bot_page_paper\` — `app.py`,
`position_manager.py`) manages trailing stops for positions entered
manually in mStock; it isn't a signal generator but shares the same exit
rule and dashboard.

---

## Shared exit rule

All four bots hand every position to the standardized exit in
`bot_page_paper\position_manager.py` (wrapped for the strategy bots by
`shared_exit_manager.py`, imported as `SharedPositionManagerAdapter`):

| Element | Value |
|---|---|
| Initial hard stop | **8%** below entry premium (`INITIAL_HARD_STOP_PCT = 0.08`) |
| Breakeven | stop moves to entry once premium is up **+5%** from entry (`BREAKEVEN_TRIGGER_PCT = 0.05`) |
| Trail | once premium is up **+10%** (`TRAIL_TRIGGER_PCT = 0.10`), stop trails **5% below the peak** (`TRAIL_DISTANCE_PCT = 0.05`) |
| Step-ladder profit-lock | starts at ₹1,000 peak profit, then ratchets in **₹500** steps (`SHARED_STEP_LADDER_INCREMENT_RUPEES = 500`) |
| Session force-close | all positions squared off at the configured cutoff / by `Stop All Bots 1520` |

**Documented exception:** Trail SL uses the base `Position` class directly
with a **₹300** step-ladder increment (`STEP_LADDER_INCREMENT_RUPEES = 300`),
not ₹500 — this is deliberate and explained in `shared_exit_manager.py`.
Every other element (8% / +5% / +10% / 5%) is identical across all five
components.

(The Scalper Bot in `D:\Scalper_Bot_Project\` is a separate project; its
`risk\position_manager.py` `StandardPosition` is a parity port of this same
rule.)

---

## Dashboard

`python dashboard.py` (or the `Trading Dashboard` task) serves a Flask app on
**http://127.0.0.1:8765** (binds `0.0.0.0`, so it's reachable on the LAN /
over Tailscale). It shows every bot that reports in — mode, running/stopped,
open positions, per-position P&L and stop level, total P&L — plus a master
kill switch, per-bot kill switches, and the Signals Bot approval popups.
Bots report via file-based status (`bot_status.py`); no bot knows about any
other.

---

## Shared infrastructure

| File | Purpose |
|---|---|
| `credentials.py` / `.env` | mStock credential prompt + local save (git-ignored) |
| `mstock_client.py` | mStock Type-B API wrapper — auth (`verify_totp`), quotes, option resolution, orders |
| `shared_exit_manager.py` | the ₹500-ladder exit adapter used by the four strategy bots |
| `trade_book.py` + `D:\Bot 8.1.2026\trade_book.csv` | shared cross-bot trade ledger (every OPEN/CLOSE row) |
| `D:\Bot 8.1.2026\bot_config.xlsx` | live-editable settings; the bots hot-reload it (`excel_config.py`) |
| `gate_and_relaunch.py` | trading-day gate + relaunch helper |
| `rotate_log.ps1` | daily `*_run.log` rotation (keeps 7 archives) |
| `force_close_position.py` | manual "close a stuck/carry-over paper position" tool (`--book {signals,gbi_rbi}`) |

---

## Disclaimers (read before running anything live)

- **This is not financial advice.** It is code that does what you configure
  it to do. Backtest / historical behaviour does not guarantee future
  results.
- **No strategy here is "low risk, high reward."** Option buying with these
  setups runs at a low win rate; any edge comes from win/loss size
  asymmetry, not hit rate, and is never guaranteed to persist.
- **Defaults to paper mode.** `MODE = "paper"` in each bot's config places
  no real orders. Do not set `MODE = "live"` until you have watched a bot
  run in paper for several sessions and are comfortable with exactly what it
  does.
- **SEBI compliance is not optional.** India's retail algo-trading framework
  has been mandatory since 1 April 2026 — broker-registered strategies /
  Algo-IDs above a small order-rate threshold, plus static IP whitelisting.
  mStock is legally the principal responsible for the algo; registration
  happens through them. Confirm your obligations with mStock
  (tradingapi@mstock.com) before switching any bot to live.
- **Never commit credentials.** API key / password / TOTP secret load from
  environment or a git-ignored `.env`, never hard-coded.

---

## See also

- `CLAUDE.md` — working rules for Claude Code in this repo (unchanged).
- Each bot folder has its own `README.md` with strategy-specific detail
  (`gbi-rbi-bot\README.md`, etc.).
- `WHILE_VIVEK_AWAY_*.md` — the ops runbook (what self-heals, what doesn't).
