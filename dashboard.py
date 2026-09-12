"""
Enhanced Trading Dashboard - Port 8765
Bot Status + Trade History + P&L Tracking + mStock API Integration
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json
import os
import csv
from pathlib import Path
from collections import defaultdict

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

# Configuration
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
TRADE_BOOK = Path(__file__).parent / 'trade_book.csv'

# FINAL 8 BOTS (removed duplicate GBI-RBI)
BOTS = [
    'O V NIFTY',
    'SENSEX Hero-Zero',
    'ORB Lite',
    'ORB-OV',
    'Signal Bot',
    'GBI-RBI',
    'bot_page_paper',
    'Scalper Bot'
]

# Instrument master with lot sizes (dynamic from NSE)
INSTRUMENTS = {
    'indices': [
        {'symbol': 'NIFTY', 'lot_size': 65, 'expiry': '2026-09-30'},
        {'symbol': 'BANKNIFTY', 'lot_size': 40, 'expiry': '2026-09-30'},
        {'symbol': 'SENSEX', 'lot_size': 10, 'expiry': '2026-09-30'},
        {'symbol': 'FINNIFTY', 'lot_size': 40, 'expiry': '2026-09-30'},
        {'symbol': 'MIDCAPNIFTY', 'lot_size': 75, 'expiry': '2026-09-30'},
        {'symbol': 'NIFTYNXT50', 'lot_size': 40, 'expiry': '2026-09-30'},
        {'symbol': 'NIFTYINFRA', 'lot_size': 50, 'expiry': '2026-09-30'},
        {'symbol': 'NIFTYIT', 'lot_size': 25, 'expiry': '2026-09-30'},
        {'symbol': 'NIFTYBANK', 'lot_size': 40, 'expiry': '2026-09-30'},
        {'symbol': 'NIFTYPHARMA', 'lot_size': 50, 'expiry': '2026-09-30'},
    ],
    'stocks': [
        {'symbol': 'RELIANCE', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'INFY', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'TCS', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'SBIN', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'ICICIBANK', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'AXISBANK', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'HDFC', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'WIPRO', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'LT', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'MARUTI', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'M&M', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'TATASTEEL', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'SUNPHARMA', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'ULTRACEMCO', 'lot_size': 1, 'expiry': '2026-09-30'},
        {'symbol': 'ASIANPAINT', 'lot_size': 1, 'expiry': '2026-09-30'},
    ]
}

def is_market_closed():
    """Check if market is closed (after 15:30 IST / 3:30 PM)"""
    now = datetime.now()
    market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return now >= market_close_time

def read_trade_book():
    """Read and parse trade_book.csv"""
    trades = []
    if TRADE_BOOK.exists():
        try:
            with open(TRADE_BOOK, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        trades.append({
                            'timestamp': row.get('timestamp', ''),
                            'bot_name': row.get('bot_name', ''),
                            'symbol': row.get('symbol', ''),
                            'direction': row.get('direction', ''),
                            'event': row.get('event', ''),
                            'price': float(row.get('price', 0)),
                            'qty': int(row.get('qty', 0)),
                            'pnl': float(row.get('pnl', 0)),
                            'stop_price': float(row.get('stop_price', 0)) if row.get('stop_price') else 0,
                            'status': row.get('status', ''),
                            'notes': row.get('notes', ''),
                            'position_id': row.get('position_id', '')
                        })
                    except:
                        continue
        except:
            pass
    return trades

def calculate_pnl_stats():
    """Calculate P&L statistics from trade_book.csv"""
    trades = read_trade_book()

    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    stats = {
        'today': 0,
        'this_week': 0,
        'this_month': 0,
        'all_time': 0,
        'open_positions': [],
        'closed_trades': []
    }

    open_positions = defaultdict(lambda: {'qty': 0, 'entry_price': 0, 'entry_pnl': 0, 'bot': '', 'symbol': '', 'direction': ''})

    for trade in trades:
        try:
            ts = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
            pnl = trade['pnl']

            # All time P&L
            stats['all_time'] += pnl

            # Monthly P&L
            if ts.replace(day=1) == month_start:
                stats['this_month'] += pnl

            # Weekly P&L
            if ts.date() >= week_start.date():
                stats['this_week'] += pnl

            # Daily P&L
            if ts.date() == today.date():
                stats['today'] += pnl

            # Track open/closed positions
            position_key = f"{trade['bot_name']}_{trade['symbol']}_{trade['direction']}"

            if trade['event'] == 'OPEN':
                open_positions[position_key]['qty'] = trade['qty']
                open_positions[position_key]['entry_price'] = trade['price']
                open_positions[position_key]['bot'] = trade['bot_name']
                open_positions[position_key]['symbol'] = trade['symbol']
                open_positions[position_key]['direction'] = trade['direction']
            elif trade['event'] == 'CLOSE':
                if position_key in open_positions:
                    stats['closed_trades'].append({
                        'bot': trade['bot_name'],
                        'symbol': trade['symbol'],
                        'pnl': pnl
                    })
                    del open_positions[position_key]
        except:
            continue

    stats['open_positions'] = [v for v in open_positions.values()]
    return stats

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html', bots=BOTS)

@app.route('/bot-info')
def bot_info():
    """Bot entry/exit configuration page"""
    return render_template('bot_info.html')

@app.route('/all-bots')
def all_bots():
    """All 9 bots detailed configuration"""
    return render_template('all_bots.html')

@app.route('/api/status')
def api_status():
    """Get all bot status"""
    status = {}

    for bot in BOTS:
        status_file = DATA_DIR / f'bot_status_{bot}.json'
        if status_file.exists():
            try:
                with open(status_file, 'r') as f:
                    status[bot] = json.load(f)
            except:
                status[bot] = {'status': 'ERROR', 'bot_name': bot}
        else:
            status[bot] = {'status': 'WAITING', 'bot_name': bot, 'mode': 'PAPER'}

    return jsonify({'timestamp': datetime.now().isoformat(), 'bots': status})

@app.route('/api/pnl')
def api_pnl():
    """Get P&L statistics"""
    stats = calculate_pnl_stats()
    market_closed = is_market_closed()

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'market_closed': market_closed,
        'today': round(stats['today'], 2),
        'this_week': round(stats['this_week'], 2),
        'this_month': round(stats['this_month'], 2),
        'all_time': round(stats['all_time'], 2),
        'open_positions': [] if market_closed else stats['open_positions'],
        'closed_trades': stats['closed_trades'] if market_closed else [],
        'closed_trades_count': len(stats['closed_trades'])
    })

@app.route('/api/trades')
def api_trades():
    """Get all trades from trade_book.csv"""
    trades = read_trade_book()

    # Apply filters
    status_filter = request.args.get('status', 'all')  # open, closed, all
    bot_filter = request.args.get('bot', 'all')
    symbol_filter = request.args.get('symbol', 'all')

    filtered = []
    for trade in trades:
        if bot_filter != 'all' and trade['bot_name'] != bot_filter:
            continue
        if symbol_filter != 'all' and trade['symbol'] != symbol_filter:
            continue
        if status_filter == 'open' and trade['event'] != 'OPEN':
            continue
        if status_filter == 'closed' and trade['event'] != 'CLOSE':
            continue
        filtered.append(trade)

    return jsonify({'trades': filtered, 'total': len(filtered)})

@app.route('/api/symbols')
def api_symbols():
    """Get unique symbols from trade book"""
    trades = read_trade_book()
    symbols = sorted(set(t['symbol'] for t in trades))
    return jsonify({'symbols': symbols})

@app.route('/api/instruments')
def api_instruments():
    """Get all tradable instruments with lot sizes"""
    all_instruments = []
    for instr in INSTRUMENTS['indices']:
        all_instruments.append({
            'symbol': instr['symbol'],
            'lot_size': instr['lot_size'],
            'type': 'INDEX',
            'expiry': instr['expiry']
        })
    for instr in INSTRUMENTS['stocks']:
        all_instruments.append({
            'symbol': instr['symbol'],
            'lot_size': instr['lot_size'],
            'type': 'STOCK',
            'expiry': instr['expiry']
        })
    return jsonify({'instruments': all_instruments})

@app.route('/api/lot-size/<instrument>')
def api_lot_size(instrument):
    """Get lot size for a specific instrument"""
    instrument = instrument.upper()
    for instr in INSTRUMENTS['indices'] + INSTRUMENTS['stocks']:
        if instr['symbol'] == instrument:
            return jsonify({
                'symbol': instrument,
                'lot_size': instr['lot_size'],
                'last_updated': datetime.now().isoformat()
            })
    return jsonify({'error': 'Instrument not found'}), 404

@app.route('/api/nifty-price')
def api_nifty_price():
    """Get NIFTY futures price (placeholder - integrate mStock API)"""
    # TODO: Integrate mStock API to fetch real NIFTY futures price
    return jsonify({
        'nifty': 23500.0,  # Placeholder
        'banknifty': 47800.0,
        'sensex': 76500.0,
        'midcapnifty': 18200.0,
        'finnifty': 22100.0,
        'india_vix': 15.5
    })

@app.route('/api/kill-all', methods=['POST'])
def kill_all():
    """Emergency stop all bots"""
    flag_file = DATA_DIR / 'KILL_ALL_BOTS'
    flag_file.write_text(datetime.now().isoformat())
    return jsonify({'status': 'killed'})

@app.route('/api/kill-bot/<bot_name>', methods=['POST'])
def kill_bot(bot_name):
    """Kill specific bot"""
    flag_file = DATA_DIR / f'KILL_{bot_name.upper()}'
    flag_file.write_text(datetime.now().isoformat())
    return jsonify({'status': 'killed', 'bot': bot_name})

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=False, use_reloader=False)
