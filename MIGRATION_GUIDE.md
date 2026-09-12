# 📚 Migration Guide: PHASE 3 Consolidation

**Goal:** Move from scattered vivek jha/vivek jha/ structure to organized /strategies/ structure

---

## Current State vs Target State

### CURRENT (Messy)
```
vivek jha/vivek jha/
├── bot.py (ORB Lite)
├── signals_bot.py (Signals Bot)
├── gbi-rbi-bot/main.py (GBI/RBI)
├── orb-ov-bot/main.py (ORB-OV)
├── bot_page_paper/app.py (Trail SL)
├── backup_2026-08-09/
├── backup_2026-08-14/
├── new project/
├── with new qty/
└── ...200+ files
```

### TARGET (Clean)
```
D:\Bot 8.1.2026/
├── strategies/
│   ├── orb_lite/
│   │   ├── __init__.py
│   │   ├── bot.py
│   │   ├── config.py
│   │   └── README.md
│   ├── signals_bot/
│   ├── gbi_rbi/
│   ├── orb_ov/
│   └── trail_sl/
├── execution/          (Core framework)
├── shared/            (Shared components)
├── tests/             (Unit + integration tests)
├── deployment/        (Startup automation)
├── logs/              (Trading logs)
├── run_bot.py         (Unified runner)
└── dashboard.py       (Consolidated dashboard)
```

---

## Migration Steps

### Step 1: Backup Current Implementation
```bash
# Create backup of vivek jha/ before changes
cp -r "vivek jha" "vivek jha.backup_2026-09-12"
```

### Step 2: Copy Bot Code to /strategies/

For each bot, copy core files:

```bash
# ORB Lite
cp "vivek jha/vivek jha/bot.py" strategies/orb_lite/bot.py
cp "vivek jha/vivek jha/config.py" strategies/orb_lite/config.py

# Signals Bot
cp "vivek jha/vivek jha/signals_bot.py" strategies/signals_bot/bot.py
cp "vivek jha/vivek jha/signals_config.py" strategies/signals_bot/config.py

# GBI/RBI
cp -r "vivek jha/vivek jha/gbi-rbi-bot/"* strategies/gbi_rbi/

# ORB-OV
cp -r "vivek jha/vivek jha/orb-ov-bot/"* strategies/orb_ov/

# Trail SL
cp -r "vivek jha/vivek jha/bot_page_paper/"* strategies/trail_sl/
```

### Step 3: Update Imports in Each Bot

Change imports from:
```python
from execution.mstock_client import MStockClient
```

To (from their new location):
```python
from execution.mstock_client import MStockClient  # Same path works
```

### Step 4: Create __init__.py for Each Strategy

```python
# strategies/orb_lite/__init__.py
"""ORB Lite Strategy - Opening Range Breakout"""

from .bot import OrbLiteBot

__all__ = ["OrbLiteBot"]
```

### Step 5: Create README for Each Strategy

Document each strategy's:
- Entry rules
- Exit rules
- Risk parameters
- Performance metrics
- Dependencies

### Step 6: Update Task Scheduler

Change scheduled tasks to use new runner:

```
OLD:  python "vivek jha/vivek jha/bot.py"
NEW:  python run_bot.py --bot orb_lite
```

### Step 7: Archive Old Backups

```bash
# Move old backups out of main repo
mkdir -p archive/
mv "vivek jha/backup_*" archive/
mv "vivek jha/new project" archive/
mv "vivek jha/with new qty" archive/
```

### Step 8: Cleanup vivek jha/ Directory

Keep ONLY the actual implementation files, remove everything else.

---

## Validation Checklist

- [ ] All 5 bots copied to /strategies/
- [ ] Imports updated and tested
- [ ] run_bot.py works for all bots
- [ ] Task Scheduler tasks updated
- [ ] No import errors
- [ ] Paper trading still works
- [ ] trade_book.csv still recording
- [ ] Dashboard still accessible
- [ ] Old backups archived
- [ ] Tests passing

---

## Rollback Plan

If anything breaks:
1. Stop all bots
2. Restore from "vivek jha.backup_2026-09-12"
3. Revert Task Scheduler changes
4. Restart bots with old paths

---

## Timeline

**Estimated Time:** 2-3 hours

1. Backup current (30 min)
2. Copy bot code (45 min)
3. Update imports (30 min)
4. Update Task Scheduler (15 min)
5. Test and validate (30 min)
6. Cleanup (15 min)

---

## Post-Migration Benefits

✅ Clean directory structure  
✅ Single entry point (run_bot.py)  
✅ Easier to maintain  
✅ Better for version control  
✅ Easier to onboard new developers  
✅ Cleaner GitHub repository  

---

## Do NOT Do

❌ Delete vivek jha/ without backup first  
❌ Update Task Scheduler before testing run_bot.py  
❌ Migrate during market hours  
❌ Delete old backups before validation complete  

---

**Status:** Ready for execution  
**Risk Level:** Low (full backup exists)  
**Recommendation:** Execute during off-market hours (after 15:30 IST)

