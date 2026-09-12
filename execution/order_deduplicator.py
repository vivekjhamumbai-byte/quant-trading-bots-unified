"""
Order Deduplication Engine

Prevents the same order from being placed twice. This is critical in paper trading
and especially important in live trading where duplicate orders could:
- Double position exposure
- Break risk management limits
- Cause unintended fills

Implementation:
1. Track all submitted orders by deterministic hash
2. Reject duplicate submission within N seconds
3. Log all attempts (successful and rejected)
4. Clean up old entries periodically
"""
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class OrderRecord:
    """Record of a submitted order"""
    order_hash: str  # Deterministic hash of order parameters
    symbol: str
    direction: str  # LONG or SHORT
    quantity: int
    entry_price: float
    submitted_time: datetime
    broker_order_id: Optional[str] = None
    status: str = "PENDING"  # PENDING, SUBMITTED, FILLED, CANCELLED, REJECTED


class OrderDeduplicator:
    """
    Maintains a ledger of submitted orders and prevents duplicates.

    Usage:
        dedup = OrderDeduplicator()
        is_dup, message = dedup.check_and_record(symbol="NIFTY", ...)
        if not is_dup:
            broker_id = place_order(...)
            dedup.mark_submitted(order_hash, broker_id)
    """

    def __init__(self, duplicate_window_seconds: int = 5):
        """
        Args:
            duplicate_window_seconds: Consider orders duplicate if submitted
                                     within this many seconds of previous order
                                     with same parameters. 5s is conservative.
        """
        self.duplicate_window_seconds = duplicate_window_seconds
        self.order_ledger: Dict[str, OrderRecord] = {}
        self.duplicate_attempts = 0
        self.successful_orders = 0

    def _compute_order_hash(
        self,
        symbol: str,
        direction: str,
        quantity: int,
        entry_price: float
    ) -> str:
        """
        Compute a deterministic hash of order parameters.

        Same order placed twice = same hash.
        """
        order_str = f"{symbol}|{direction}|{quantity}|{entry_price:.6f}"
        return hashlib.sha256(order_str.encode()).hexdigest()[:16]

    def check_and_record(
        self,
        symbol: str,
        direction: str,
        quantity: int,
        entry_price: float
    ) -> Tuple[bool, str, str]:
        """
        Check if this order is a duplicate, and record it if not.

        Args:
            symbol: Instrument symbol (e.g., "NIFTY")
            direction: "LONG" or "SHORT"
            quantity: Number of units
            entry_price: Entry price

        Returns:
            (is_duplicate: bool, message: str, order_hash: str)

        If is_duplicate=False: Order is safe to submit, return order_hash to use later
        If is_duplicate=True: This is a duplicate, REJECT it
        """
        order_hash = self._compute_order_hash(symbol, direction, quantity, entry_price)
        now = datetime.now()

        # Check if we've seen this exact order recently
        if order_hash in self.order_ledger:
            prev_order = self.order_ledger[order_hash]
            time_since_prev = (now - prev_order.submitted_time).total_seconds()

            if time_since_prev < self.duplicate_window_seconds:
                self.duplicate_attempts += 1
                msg = (
                    f"DUPLICATE ORDER REJECTED: "
                    f"{symbol} {direction} qty={quantity} @ {entry_price:.2f} "
                    f"(submitted {time_since_prev:.1f}s ago, within {self.duplicate_window_seconds}s window)"
                )
                log.warning(msg)
                return True, msg, order_hash

        # Not a duplicate — record this order
        self.order_ledger[order_hash] = OrderRecord(
            order_hash=order_hash,
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            entry_price=entry_price,
            submitted_time=now,
            status="PENDING"
        )

        msg = f"Order recorded: {symbol} {direction} qty={quantity} @ {entry_price:.2f}"
        log.info(msg)
        return False, msg, order_hash

    def mark_submitted(self, order_hash: str, broker_order_id: str):
        """
        After broker confirms submission, mark the order as submitted.

        Args:
            order_hash: Hash returned by check_and_record()
            broker_order_id: Order ID from broker response
        """
        if order_hash in self.order_ledger:
            self.order_ledger[order_hash].broker_order_id = broker_order_id
            self.order_ledger[order_hash].status = "SUBMITTED"
            log.info(f"Order {order_hash[:8]}... submitted to broker as {broker_order_id}")
            self.successful_orders += 1
        else:
            log.warning(f"mark_submitted() called for unknown order hash {order_hash}")

    def mark_filled(self, order_hash: str, filled_quantity: int, fill_price: float):
        """Mark an order as filled (partially or fully)"""
        if order_hash in self.order_ledger:
            self.order_ledger[order_hash].status = "FILLED"
            log.info(f"Order {order_hash[:8]}... filled: {filled_quantity} @ {fill_price:.2f}")

    def mark_rejected(self, order_hash: str, reason: str):
        """Mark an order as rejected by broker"""
        if order_hash in self.order_ledger:
            self.order_ledger[order_hash].status = "REJECTED"
            log.warning(f"Order {order_hash[:8]}... rejected: {reason}")

    def cleanup_old_records(self, older_than_seconds: int = 3600):
        """
        Remove old order records to keep ledger size reasonable.

        Args:
            older_than_seconds: Remove records older than this many seconds.
                              3600 = 1 hour (keep all same-day orders)
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=older_than_seconds)

        removed = 0
        for order_hash, record in list(self.order_ledger.items()):
            if record.submitted_time < cutoff:
                del self.order_ledger[order_hash]
                removed += 1

        if removed > 0:
            log.info(f"Cleaned up {removed} old order records")

    def get_stats(self) -> Dict:
        """Return deduplication statistics"""
        return {
            "total_orders_recorded": len(self.order_ledger),
            "successful_submissions": self.successful_orders,
            "duplicate_attempts_blocked": self.duplicate_attempts,
            "pending_orders": sum(1 for r in self.order_ledger.values() if r.status == "PENDING"),
            "submitted_orders": sum(1 for r in self.order_ledger.values() if r.status == "SUBMITTED"),
            "filled_orders": sum(1 for r in self.order_ledger.values() if r.status == "FILLED"),
        }

    def log_stats(self):
        """Log deduplication statistics"""
        stats = self.get_stats()
        log.info(
            f"Order Dedup Stats: "
            f"{stats['successful_submissions']} submitted, "
            f"{stats['duplicate_attempts_blocked']} duplicates blocked, "
            f"{stats['filled_orders']} filled, "
            f"{stats['pending_orders']} pending"
        )
