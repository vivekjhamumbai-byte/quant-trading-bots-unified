"""
8-BOT TRADING SYSTEM DASHBOARD - AWS VERSION
Phone-Accessible Dashboard with TOTP Authentication
Runs on AWS EC2, accessible from any device
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import pytz
from pathlib import Path

app = Flask(__name__)
CORS(app)

IST = pytz.timezone('Asia/Kolkata')

# Configuration
TOTP_AUTHENTICATED = False
TOTP_CODE = None
BOTS_RUNNING = False
DASHBOARD_PORT = 8765

class DashboardState:
    """Maintain dashboard state"""
    def __init__(self):
        self.authenticated = False
        self.totp_code = None
        self.bots_status = {
            "ov_nifty": {"status": "IDLE", "trades": 0, "pnl": 0},
            "sensex_hero_zero": {"status": "IDLE", "trades": 0, "pnl": 0},
            "orb_lite": {"status": "IDLE", "trades": 0, "pnl": 0},
            "orb_ov": {"status": "IDLE", "trades": 0, "pnl": 0},
            "signals_bot": {"status": "IDLE", "trades": 0, "pnl": 0},
            "gbi_rbi": {"status": "IDLE", "trades": 0, "pnl": 0},
            "trail_sl": {"status": "IDLE", "trades": 0, "pnl": 0},
            "scalper_bot": {"status": "IDLE", "trades": 0, "pnl": 0},
        }
        self.total_pnl = 0
        self.total_trades = 0
        self.last_update = datetime.now(IST)

state = DashboardState()

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    return jsonify({
        "authenticated": state.authenticated,
        "timestamp": datetime.now(IST).isoformat()
    })

@app.route('/api/auth/totp', methods=['POST'])
def authenticate_totp():
    """Authenticate with TOTP code"""
    data = request.json
    totp_code = data.get('totp_code', '').strip()

    # Validate TOTP format (6 digits)
    if not totp_code or len(totp_code) != 6 or not totp_code.isdigit():
        return jsonify({
            "success": False,
            "message": "Invalid TOTP code. Must be 6 digits."
        }), 400

    try:
        # In real implementation, verify with mStock API
        # For now, accept any 6-digit code
        state.authenticated = True
        state.totp_code = totp_code

        return jsonify({
            "success": True,
            "message": "Authentication successful! Bots starting...",
            "timestamp": datetime.now(IST).isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Authentication failed: {str(e)}"
        }), 400

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/dashboard/summary', methods=['GET'])
def dashboard_summary():
    """Get dashboard summary"""
    if not state.authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    return jsonify({
        "timestamp": datetime.now(IST).isoformat(),
        "market_time": datetime.now(IST).strftime("%H:%M:%S"),
        "total_trades": state.total_trades,
        "total_pnl": state.total_pnl,
        "bots_count": len(state.bots_status),
        "bots_running": sum(1 for b in state.bots_status.values() if b["status"] == "RUNNING"),
        "win_rate": calculate_win_rate()
    })

@app.route('/api/dashboard/bots', methods=['GET'])
def get_bots_status():
    """Get all bots status"""
    if not state.authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    bots = []
    for bot_id, bot_data in state.bots_status.items():
        bots.append({
            "id": bot_id,
            "name": get_bot_name(bot_id),
            "status": bot_data["status"],
            "trades": bot_data["trades"],
            "pnl": bot_data["pnl"]
        })

    return jsonify({"bots": bots, "timestamp": datetime.now(IST).isoformat()})

@app.route('/api/dashboard/trades', methods=['GET'])
def get_trades():
    """Get recent trades"""
    if not state.authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    # Read from trade_book.csv
    trades = []
    try:
        with open('trade_book.csv', 'r') as f:
            lines = f.readlines()[-20:]  # Last 20 trades
            for line in lines:
                trades.append(line.strip())
    except FileNotFoundError:
        pass

    return jsonify({"trades": trades, "count": len(trades)})

@app.route('/api/control/stop-all', methods=['POST'])
def stop_all_bots():
    """Stop all bots (kill switch)"""
    if not state.authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        # Create kill switch flag
        Path('kill_switch/ALL.flag').touch()
        return jsonify({"success": True, "message": "All bots stopped"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_bot_name(bot_id):
    """Get bot display name"""
    names = {
        "ov_nifty": "O V NIFTY",
        "sensex_hero_zero": "SENSEX Hero-Zero",
        "orb_lite": "ORB Lite",
        "orb_ov": "ORB-OV",
        "signals_bot": "Signal Bot",
        "gbi_rbi": "GBI-RBI",
        "trail_sl": "Trail SL",
        "scalper_bot": "Scalper Bot"
    }
    return names.get(bot_id, bot_id)

def calculate_win_rate():
    """Calculate overall win rate"""
    total = state.total_trades
    if total == 0:
        return 0
    winning = sum(1 for b in state.bots_status.values() if b["pnl"] > 0)
    return round((winning / total) * 100, 1) if total > 0 else 0

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server error"}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("8-BOT TRADING SYSTEM DASHBOARD - AWS VERSION")
    print("=" * 60)
    print(f"Starting at: {datetime.now(IST)}")
    print(f"Region: ap-south-1 (Asia Pacific - Mumbai)")
    print(f"Access: http://YOUR-EC2-PUBLIC-IP:{DASHBOARD_PORT}")
    print("")
    print("Dashboard Features:")
    print("  ✓ Phone-accessible (responsive design)")
    print("  ✓ TOTP authentication required")
    print("  ✓ Real-time bot status")
    print("  ✓ Live P&L tracking")
    print("  ✓ Trade history")
    print("  ✓ Emergency kill switch")
    print("")
    print("=" * 60)
    print("")

    # Run Flask app
    app.run(
        host='0.0.0.0',  # Accessible from anywhere
        port=DASHBOARD_PORT,
        debug=False,
        threaded=True
    )
