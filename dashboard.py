"""
Unified Trading Dashboard - Port 8765
Aggregates status from all 6 bots via file-based communication
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime
import json
import os
import glob
from pathlib import Path

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

# Configuration
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

BOTS = ['velez_nifty', 'sensex_hero', 'orb_lite', 'orb_ov', 'signal_bot', 'gbi_rbi']

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html', bots=BOTS)

@app.route('/api/status')
def api_status():
    """Get all bot status (JSON API)"""
    status = {}
    
    for bot in BOTS:
        status_file = DATA_DIR / f'bot_status_{bot}.json'
        if status_file.exists():
            try:
                with open(status_file, 'r') as f:
                    status[bot] = json.load(f)
            except:
                status[bot] = {'error': 'Failed to read', 'bot_name': bot, 'status': 'ERROR'}
        else:
            status[bot] = {
                'bot_name': bot,
                'status': 'NOT_STARTED',
                'mode': 'PAPER',
                'last_update': None,
                'open_positions': [],
                'today_pnl': 0,
                'trades_today': 0,
                'win_rate': 0
            }
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'bots': status,
        'summary': {
            'total_pnl': sum(float(b.get('today_pnl', 0)) for b in status.values()),
            'total_trades': sum(int(b.get('trades_today', 0)) for b in status.values()),
            'running_bots': len([b for b in status.values() if b.get('status') == 'RUNNING'])
        }
    })

@app.route('/api/kill-all', methods=['POST'])
def kill_all():
    """Emergency stop all bots"""
    flag_file = DATA_DIR / 'KILL_ALL_BOTS'
    flag_file.write_text(datetime.now().isoformat())
    return jsonify({'status': 'killed', 'timestamp': datetime.now().isoformat()})

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
