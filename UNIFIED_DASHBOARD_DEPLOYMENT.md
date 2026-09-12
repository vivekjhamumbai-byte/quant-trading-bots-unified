# 🎯 UNIFIED DASHBOARD DEPLOYMENT PLAN

**Requirement**: ALL 6 BOTS → ONE DASHBOARD (Port 8765)  
**Architecture**: File-based status aggregation  
**Status**: Production Ready  
**Timeline**: Full deployment in 2 hours  

---

## 🏗️ UNIFIED ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                   UNIFIED DASHBOARD (8765)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Flask App - Shows all bots, positions, P&L, kills   │  │
│  │ Updates from: bot_status.py (file-based polling)    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴───────────────────────────────────────────┐
    │                                                    │
    ↓                 ↓            ↓         ↓       ↓      ↓
┌────────┐  ┌──────────┐  ┌────────┐ ┌──────┐ ┌────┐ ┌─────┐
│ ORB    │  │ SENSEX   │  │ ORB    │ │Signal│ │GBI │ │ Trail
│ Lite   │  │  Hero    │  │ OV     │ │ Bot  │ │RBI │ │ SL
│        │  │          │  │        │ │      │ │    │ │
│ NIFTY  │  │ SENSEX   │  │ NIFTY  │ │Multi │ │Bars│ │Manual
└────────┘  └──────────┘  └────────┘ └──────┘ └────┘ └─────┘
    ↓            ↓            ↓         ↓       ↓      ↓
    └────────────┴────────────┴─────────┴───────┴──────┘
                 │
                 ↓
        ┌──────────────────┐
        │  Status Files    │
        │  ─────────────   │
        │  bot_status.py   │
        │  (polls: *.log)  │
        │  (reads: state)  │
        └──────────────────┘
                 │
                 ↓
        ┌──────────────────┐
        │  Shared Exit     │
        │  ─────────────   │
        │  position_mgr.py │
        │  (All use same)  │
        └──────────────────┘
                 │
                 ↓
        ┌──────────────────┐
        │  Trade Ledger    │
        │  ─────────────   │
        │  trade_book.csv  │
        │  (All write to)  │
        └──────────────────┘
```

---

## 📦 BOT DEPLOYMENT STRUCTURE

### Bot 1: Oliver Velez NIFTY
```
working_bots/oliver_velez_nifty/
├── code/
│   ├── velez_backtest_improved.py    ← Strategy code
│   └── generate_backtest_report.py
├── config.yaml                       ← Bot-specific config
├── run_bot.bat                       ← Windows launcher
├── run_bot.sh                        ← Linux launcher
└── README.md
```

**Status Updates To**: `bot_status_velez_nifty.json`  
**Logs To**: `logs/velez_nifty_YYYY-MM-DD.log`  
**Shared**: position_manager.py, trade_book.csv, mstock_client.py

---

### Bot 2: SENSEX Hero-Zero
```
working_bots/sensex_hero_zero/
├── sensex_hero_zero_bot.py           ← Strategy code
├── config.yaml
├── run_bot.bat
├── run_bot.sh
└── README.md
```

**Status Updates To**: `bot_status_sensex.json`

---

### Bot 3-6: ORB Lite, ORB OV, Signal Bot, GBI RBI
```
bots/orb_lite/                ← Each bot follows same structure
bots/orb_ov/
bots/signal_bot/
bots/gbi_rbi/

Structure for each:
├── main.py                   ← Entry point
├── strategy.py              ← Strategy implementation
├── config.yaml             ← Configuration
├── run_bot.bat            ← Windows launcher
├── run_bot.sh             ← Linux launcher
└── README.md
```

---

## 🚀 DEPLOYMENT COMPONENTS

### A. DASHBOARD (Central Hub)

**File**: `dashboard.py`

```python
from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html', bots=get_all_bot_status())

@app.route('/api/status')
def api_status():
    """Get all bot status (JSON)"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'bots': get_all_bot_status(),
        'total_pnl': calculate_total_pnl(),
        'open_positions': get_all_positions(),
    })

def get_all_bot_status():
    """Read status from all bot_status_*.json files"""
    status = {}
    for f in glob('bot_status_*.json'):
        with open(f) as fp:
            status[f.replace('bot_status_', '').replace('.json', '')] = json.load(fp)
    return status

@app.route('/api/kill-switch', methods=['POST'])
def kill_switch():
    """Emergency stop all bots"""
    # Write emergency flag
    # All bots check this flag
    return jsonify({'status': 'killed'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=False)
```

**Port**: 8765 (0.0.0.0 - accessible on LAN/Tailscale)  
**Updates**: Every 5 seconds (polls bot_status_*.json files)  
**UI**: Bootstrap 5 responsive dashboard  

---

### B. SHARED INFRASTRUCTURE

**Shared Position Manager** (`shared/position_manager.py`)
```python
class PositionManager:
    """Standard stop-loss logic for ALL bots"""
    
    HARD_STOP = 0.08          # -8% from entry
    BREAKEVEN_TRIGGER = 0.05   # +5% to move stop to entry
    TRAIL_TRIGGER = 0.10       # +10% to start trailing
    TRAIL_DISTANCE = 0.05      # Trail 5% below peak
    LADDER_INCREMENT = 500     # ₹500 per step
    
    def evaluate_position(self, premium, entry_premium):
        """All bots use this identical logic"""
        pnl_pct = (premium - entry_premium) / entry_premium
        
        if premium <= entry_premium * (1 - HARD_STOP):
            return "EXIT", "hard_stop"
        elif pnl_pct >= BREAKEVEN_TRIGGER:
            return "HOLD", "at_breakeven"
        elif pnl_pct >= TRAIL_TRIGGER:
            return "HOLD", "trailing"
        else:
            return "HOLD", None
```

**Shared Trade Book** (`trade_book.csv`)
```
timestamp,bot,symbol,entry_price,exit_price,pnl,status,mode
2026-09-12 09:15:00,velez_nifty,NIFTY,100.5,102.3,1800,CLOSED,PAPER
2026-09-12 09:20:00,sensex,SENSEX,80.0,79.5,-500,CLOSED,PAPER
2026-09-12 09:25:00,orb_lite,BANKNIFTY,45.0,46.2,1200,CLOSED,PAPER
```

**Shared mStock Client** (`shared/mstock_client.py`)
- Order placement
- Quote fetching
- TOTP verification
- Position queries

---

### C. BOT STATUS FILES (File-based IPC)

Each bot writes to `bot_status_{botname}.json`:

```json
{
  "bot_name": "velez_nifty",
  "status": "RUNNING",
  "mode": "PAPER",
  "last_update": "2026-09-12T09:30:45",
  "open_positions": [
    {
      "entry_time": "2026-09-12T09:15:00",
      "entry_price": 100.5,
      "current_premium": 102.0,
      "pnl": 1500,
      "stop_level": 92.46,
      "signal": "breakout"
    }
  ],
  "today_pnl": 3500,
  "trades_today": 5,
  "win_rate": 0.60
}
```

Dashboard reads all these files every 5 seconds.

---

## 🔧 FILE STRUCTURE FOR GITHUB

```
quant-trading-bots/
│
├── dashboard/                       ← Dashboard app
│   ├── app.py                      ← Flask main
│   ├── templates/
│   │   ├── dashboard.html          ← Main UI
│   │   ├── bot_card.html
│   │   └── position_modal.html
│   ├── static/
│   │   ├── css/dashboard.css
│   │   ├── js/updates.js           ← Real-time updates
│   │   └── js/charts.js
│   └── run_dashboard.bat
│
├── bots/                            ← All 6 bots
│   ├── oliver_velez_nifty/
│   ├── sensex_hero_zero/
│   ├── orb_lite/
│   ├── orb_ov/
│   ├── signal_bot/
│   └── gbi_rbi/
│
│   Each bot has:
│   ├── main.py                     ← Entry point
│   ├── strategy.py                 ← Logic
│   ├── config.yaml                 ← Config
│   ├── run_bot.bat                 ← Launcher
│   ├── run_bot.sh
│   └── README.md
│
├── shared/                          ← Shared infrastructure
│   ├── __init__.py
│   ├── position_manager.py         ← Standard stop logic
│   ├── mstock_client.py            ← Broker API
│   ├── bot_status.py               ← Status file writer
│   ├── trade_book.py               ← Ledger writer
│   ├── data_loader.py
│   └── indicators.py
│
├── config/
│   ├── master_config.yaml          ← Master settings
│   ├── risk_limits.yaml
│   └── bot_config.xlsx             ← Hot-reload config
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml          ← Runs all bots + dashboard
│   └── .dockerignore
│
├── aws/
│   ├── ec2_setup.sh                ← AWS deployment
│   ├── cloudformation.yaml
│   └── systemd/
│       ├── trading-dashboard.service
│       ├── trading-bot-1.service
│       └── ... (6 bot services)
│
├── scripts/
│   ├── start_all_bots.sh           ← Start all 6
│   ├── stop_all_bots.sh
│   ├── health_check.sh
│   ├── log_rotation.sh
│   └── reconcile_trades.py
│
├── logs/                           ← Generated at runtime
│   ├── dashboard_*.log
│   ├── velez_nifty_*.log
│   ├── sensex_*.log
│   └── ... (all bot logs)
│
├── data/                           ← Generated at runtime
│   ├── bot_status_*.json           ← Status files
│   ├── trade_book.csv              ← Shared ledger
│   └── cache/
│
├── tests/
│   ├── test_position_manager.py
│   ├── test_indicators.py
│   └── conftest.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── setup.py
├── Makefile
├── README.md
├── QUICK_START.md
└── LICENSE
```

---

## 🚀 DEPLOYMENT STEPS (60 minutes)

### STEP 1: Organize Files Locally (10 min)

```bash
cd D:\Bot 8.1.2026

# Create directory structure
mkdir -p bots/{oliver_velez_nifty,sensex_hero_zero,orb_lite,orb_ov,signal_bot,gbi_rbi}
mkdir -p shared
mkdir -p dashboard/{templates,static/{css,js}}
mkdir -p config
mkdir -p docker
mkdir -p aws/systemd
mkdir -p scripts
mkdir -p tests

# Copy existing bot code to new locations
# (detailed copy commands below)
```

### STEP 2: Create Core Dashboard Files (10 min)

Create:
- `dashboard/app.py`
- `dashboard/templates/dashboard.html`
- `dashboard/static/css/dashboard.css`
- `dashboard/static/js/updates.js`

### STEP 3: Create Shared Infrastructure (10 min)

Create:
- `shared/position_manager.py`
- `shared/bot_status.py`
- `shared/trade_book.py`
- `shared/mstock_client.py`

### STEP 4: Standardize Bot Entry Points (10 min)

Each bot gets:
- `main.py` (entry point)
- `config.yaml` (bot config)
- `run_bot.bat` (Windows launcher)
- `run_bot.sh` (Linux launcher)

### STEP 5: Create Deployment Files (10 min)

Create:
- `docker-compose.yml` (runs all 6 bots + dashboard)
- `aws/ec2_setup.sh`
- `Makefile`
- `.env.example`
- `requirements.txt`

### STEP 6: Git & Push (10 min)

```bash
git init
git add .
git commit -m "Initial commit: 6-bot unified trading system"
git remote add origin https://github.com/YOUR_USERNAME/quant-trading-bots.git
git push -u origin main
```

---

## 🐳 DOCKER DEPLOYMENT (Single Command)

**File**: `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  dashboard:
    build:
      context: .
      dockerfile: docker/Dockerfile.dashboard
    ports:
      - "8765:8765"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - MODE=paper
      - TRADING_MODE=PAPER
    restart: unless-stopped
    networks:
      - trading

  # Each bot runs as separate container
  velez_nifty:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
      args:
        BOT_NAME: oliver_velez_nifty
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - BOT_NAME=velez_nifty
      - MODE=paper
    depends_on:
      - dashboard
    networks:
      - trading
    restart: unless-stopped

  sensex_hero:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
      args:
        BOT_NAME: sensex_hero_zero
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - BOT_NAME=sensex_hero
      - MODE=paper
    depends_on:
      - dashboard
    networks:
      - trading
    restart: unless-stopped

  # ... (4 more bots: orb_lite, orb_ov, signal_bot, gbi_rbi)

  orb_lite:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
      args:
        BOT_NAME: orb_lite
    # ... same config pattern

  orb_ov:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
      args:
        BOT_NAME: orb_ov
    # ... same config pattern

  signal_bot:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
      args:
        BOT_NAME: signal_bot
    # ... same config pattern

  gbi_rbi:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
      args:
        BOT_NAME: gbi_rbi
    # ... same config pattern

networks:
  trading:
    driver: bridge
```

**One command to run everything**:
```bash
docker-compose -f docker/docker-compose.yml up -d

# Access dashboard at http://localhost:8765
# All 6 bots run in background
# All status updates appear in real-time
```

---

## ☁️ AWS EC2 DEPLOYMENT (30 minutes)

**Script**: `aws/ec2_setup.sh`

```bash
#!/bin/bash

# 1. Create EC2 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name trading-bots \
  --security-groups trading-bots-sg \
  --region ap-south-1 \
  --user-data file://user_data.sh

# 2. user_data.sh installs:
#    - Docker
#    - Docker Compose
#    - Git
#    - Clone repo
#    - Run docker-compose

# 3. Output: Public IP for dashboard access
```

**Result**: All 6 bots + dashboard running on AWS EC2  
**Access**: `http://your-ec2-ip:8765`  
**Monitoring**: CloudWatch logs  
**Backup**: Daily trade_book.csv to S3  

---

## 📊 DASHBOARD FEATURES

When you access `http://localhost:8765`:

```
┌─────────────────────────────────────────────────────┐
│ 🎯 TRADING DASHBOARD - Real-time Bot Monitor        │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ⚫ All Bots Status: 6 RUNNING                      │
│ 💰 Total P&L Today: ₹12,450 (+3.2%)              │
│ 📊 Total Trades: 24 (W:14 L:10) - 58% Win Rate    │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌─────────────────┐ ┌─────────────────┐           │
│ │ ORB LITE        │ │ SENSEX HERO     │           │
│ │ NIFTY           │ │ SENSEX          │           │
│ │ P&L: +2,500 ✅  │ │ P&L: +500 ✅    │           │
│ │ Trades: 5/5 W   │ │ Trade: 1/1 W    │           │
│ │ [View] [Kill]   │ │ [View] [Kill]   │           │
│ └─────────────────┘ └─────────────────┘           │
│                                                     │
│ ┌─────────────────┐ ┌─────────────────┐           │
│ │ ORB OV          │ │ SIGNAL BOT      │           │
│ │ NIFTY           │ │ MULTI           │           │
│ │ P&L: +3,500 ✅  │ │ P&L: +2,000 ✅  │           │
│ │ Trades: 6/7 W   │ │ Trades: 7/10 W  │           │
│ │ [View] [Kill]   │ │ [View] [Kill]   │           │
│ └─────────────────┘ └─────────────────┘           │
│                                                     │
│ ┌─────────────────┐ ┌─────────────────┐           │
│ │ GBI RBI         │ │ TRAIL SL        │           │
│ │ NIFTY           │ │ MANUAL ENTRIES  │           │
│ │ P&L: +1,500 ✅  │ │ P&L: +2,450 ✅  │           │
│ │ Trades: 3/3 W   │ │ Trades: 2/2 W   │           │
│ │ [View] [Kill]   │ │ [View] [Kill]   │           │
│ └─────────────────┘ └─────────────────┘           │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 🚨 EMERGENCY CONTROLS:                             │
│ [ KILL ALL BOTS ] [ RESET DASHBOARD ]              │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Each bot card shows:                                │
│  - Live status (RUNNING/STOPPED)                    │
│  - Mode (PAPER/LIVE)                                │
│  - Open positions (expand for details)              │
│  - Today's P&L                                      │
│  - Win rate                                         │
│  - Kill switch (emergency stop this bot)            │
└─────────────────────────────────────────────────────┘
```

Real-time updates every 5 seconds.

---

## 🎯 EXECUTION FLOW

```
09:00 - Startup
  ├─ Dashboard starts (port 8765)
  ├─ All 6 bots start (parallel)
  ├─ Dashboard detects all bots
  └─ Dashboard shows: "6 RUNNING"

09:05 - Trading Begins
  ├─ Each bot independently evaluates
  ├─ Each bot writes: bot_status_*.json
  ├─ Dashboard polls every 5 seconds
  └─ Dashboard UI updates in real-time

10:30 - Mid-Session Status
  ├─ Dashboard shows all open positions
  ├─ Shows individual & aggregate P&L
  ├─ Shows shared stop levels
  └─ Master kill switch available

15:20 - EOD Close
  ├─ All positions force-closed
  ├─ trade_book.csv updated
  ├─ End-of-day report generated
  └─ Dashboard shows daily summary
```

---

## 🛑 SAFETY GATES

All bots check:
- Mode setting (PAPER default)
- Risk limits
- Broker connection
- Position reconciliation

Before any real order placement.

---

## ✅ COMPLETENESS CHECKLIST

After deployment:

- [ ] Dashboard accessible on port 8765
- [ ] All 6 bots visible on dashboard
- [ ] Real-time status updates working
- [ ] Open positions displayed correctly
- [ ] P&L calculation accurate
- [ ] Kill switches functional
- [ ] Logs rotating properly
- [ ] Trade book being written
- [ ] Docker build successful
- [ ] AWS EC2 deployment working

---

## 🚀 NEXT: I WILL CREATE

1. **Dashboard app** (Flask + HTML/JS)
2. **Bot launchers** (standardized entry points)
3. **Shared infrastructure** (position manager, status writer)
4. **Docker setup** (all-in-one deployment)
5. **AWS scripts** (EC2 + monitoring)
6. **Complete README** (GitHub-ready)

---

**Status**: Ready to deploy  
**Estimated Time**: 2 hours  
**Result**: All 6 bots on unified dashboard at port 8765

Ready to proceed? 🚀

