"""
Position Reconciliation Engine

Compares local bot state with broker state and prevents trading if reconciliation
fails. This is critical to prevent:
- Trading on stale position data
- Opening duplicate positions after crash/restart
- Incorrect position sizing
- Unhedged exposure

Called on bot startup and periodically during trading.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass

log = logging.getLogger(__name__)

IST_OFFSET = 5.5  # IST is UTC+5:30


@dataclass
class LocalPosition:
    """Local state: what the bot thinks it's holding"""
    symbol: str
    direction: str  # LONG or SHORT
    quantity: int
    entry_price: float
    entry_time: datetime


@dataclass
class BrokerPosition:
    """Broker state: what the broker says we hold"""
    symbol: str
    direction: str
    quantity: int
    average_price: float
    last_updated: datetime


class PositionReconciliationEngine:
    """
    Reconciles local positions against broker positions.

    CRITICAL: If reconciliation fails, the bot MUST NOT place new orders
    until the state is manually verified.
    """

    def __init__(self, tolerance_pct: float = 0.5):
        """
        Args:
            tolerance_pct: Allow qty/price to differ by this % before flagging
        """
        self.tolerance_pct = tolerance_pct
        self.last_reconcile_time = None
        self.reconcile_failures = 0
        self.safe_to_trade = False

    def reconcile(
        self,
        local_positions: Dict[str, LocalPosition],
        broker_positions: Dict[str, BrokerPosition]
    ) -> Tuple[bool, List[str]]:
        """
        Compare local vs broker positions.

        Returns:
            (is_safe_to_trade, list_of_discrepancies)

        Safety rule:
        - If 0 local positions and 0 broker positions → SAFE ✓
        - If local and broker match (qty, symbol, direction) → SAFE ✓
        - If any mismatch → UNSAFE, log details, return False
        """
        discrepancies = []
        self.last_reconcile_time = datetime.now()

        # Get symbol sets
        local_symbols = set(local_positions.keys())
        broker_symbols = set(broker_positions.keys())

        # Check 1: Missing in broker (we think we own it, but broker disagrees)
        for symbol in local_symbols - broker_symbols:
            msg = f"RECONCILE FAIL: Local position {symbol} not found in broker"
            discrepancies.append(msg)
            log.error(msg)

        # Check 2: Unexpected in broker (broker has it, we don't know about it)
        for symbol in broker_symbols - local_symbols:
            msg = f"RECONCILE FAIL: Unexpected broker position {symbol} not in local state"
            discrepancies.append(msg)
            log.error(msg)

        # Check 3: Quantity mismatch
        for symbol in local_symbols & broker_symbols:
            local = local_positions[symbol]
            broker = broker_positions[symbol]

            if local.direction != broker.direction:
                msg = f"RECONCILE FAIL: {symbol} direction mismatch: local={local.direction}, broker={broker.direction}"
                discrepancies.append(msg)
                log.error(msg)

            qty_pct_diff = abs(local.quantity - broker.quantity) / max(1, local.quantity) * 100
            if qty_pct_diff > self.tolerance_pct:
                msg = f"RECONCILE FAIL: {symbol} qty mismatch: local={local.quantity}, broker={broker.quantity} ({qty_pct_diff:.1f}% diff)"
                discrepancies.append(msg)
                log.error(msg)

            # Price tolerance: 2% is reasonable for mid-price vs entry price
            price_pct_diff = abs(local.entry_price - broker.average_price) / local.entry_price * 100
            if price_pct_diff > 2.0:
                msg = f"RECONCILE WARN: {symbol} price mismatch: local={local.entry_price}, broker={broker.average_price} ({price_pct_diff:.1f}% diff)"
                log.warning(msg)  # Warning, not error, since price can diverge

        # Determine safety
        is_safe = len(discrepancies) == 0
        self.safe_to_trade = is_safe

        if is_safe:
            log.info(f"✓ RECONCILIATION OK: {len(local_positions)} local positions match broker state")
            self.reconcile_failures = 0
        else:
            self.reconcile_failures += 1
            log.error(f"✗ RECONCILIATION FAILED: {len(discrepancies)} discrepancies found")

        return is_safe, discrepancies

    def startup_check(self, mstock_client, local_positions: Dict) -> bool:
        """
        On bot startup, query broker for live positions and reconcile.

        Args:
            mstock_client: Connected MStockClient instance
            local_positions: Positions loaded from bot's trade log

        Returns:
            True if safe to start trading, False if manual intervention needed
        """
        try:
            log.info("Starting position reconciliation check...")

            # Query broker for all holdings
            broker_positions = self._query_broker_positions(mstock_client)

            # Reconcile
            is_safe, discrepancies = self.reconcile(local_positions, broker_positions)

            if not is_safe:
                log.error(f"Bot startup blocked: Reconciliation failed with {len(discrepancies)} discrepancies")
                log.error("Discrepancies:")
                for disc in discrepancies:
                    log.error(f"  - {disc}")
                log.error("ACTION REQUIRED: Manually verify positions in mStock and resolve discrepancies")
                return False

            log.info("✓ Position reconciliation passed — safe to start trading")
            return True

        except Exception as e:
            log.error(f"Reconciliation check failed with exception: {e}")
            log.error("Cannot verify positions — blocking bot startup for safety")
            return False

    def _query_broker_positions(self, mstock_client) -> Dict[str, BrokerPosition]:
        """
        Query broker for current holdings.

        NOTE: mStock SDK doesn't have a direct "get all open positions" call,
        so this needs to be implemented based on available API methods.
        For now, this is a placeholder that shows the structure.
        """
        positions = {}

        # TODO: Call mstock_client to get open holdings
        # Example (pseudo-code):
        # holdings = mstock_client.get_holdings()
        # for holding in holdings:
        #     positions[holding['symbol']] = BrokerPosition(...)

        # Until implemented, return empty (will cause all local positions to fail reconciliation)
        log.warning("Broker position query not yet implemented — reconciliation incomplete")
        return positions

    def require_safe_to_trade(self) -> bool:
        """Check that reconciliation passed before placing any order"""
        if not self.safe_to_trade:
            log.error("Order blocked: Position reconciliation has not passed")
            log.error("Run bot with --reconcile-only flag to diagnose")
            return False
        return True


def load_local_positions_from_tradebook(tradebook_csv_path: str) -> Dict[str, LocalPosition]:
    """
    Load current positions from the trade_book.csv.

    Returns a dict mapping symbol -> LocalPosition for all OPEN positions
    (i.e., trades with event='OPEN' and no subsequent event='CLOSE').
    """
    positions = {}

    try:
        import csv
        from datetime import datetime

        open_trades = {}  # symbol -> (direction, qty, price, timestamp)

        with open(tradebook_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = row['symbol']
                event = row['event']
                direction = row['direction']
                qty = int(row['qty'])
                price = float(row['price'])
                timestamp = datetime.fromisoformat(row['timestamp'])

                if event == 'OPEN':
                    open_trades[symbol] = (direction, qty, price, timestamp)
                elif event == 'CLOSE':
                    open_trades.pop(symbol, None)  # Position was closed

        # Convert to LocalPosition objects
        for symbol, (direction, qty, price, ts) in open_trades.items():
            positions[symbol] = LocalPosition(
                symbol=symbol,
                direction=direction,
                quantity=qty,
                entry_price=price,
                entry_time=ts
            )

        log.info(f"Loaded {len(positions)} open positions from trade book")
        return positions

    except Exception as e:
        log.error(f"Error loading positions from {tradebook_csv_path}: {e}")
        return {}
