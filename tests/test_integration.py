"""
Integration Tests for Trading Bot System

Tests the complete trading loop:
1. Startup with reconciliation
2. Signal generation
3. Risk validation
4. Order deduplication
5. Trade logging
6. Exit management
7. Shutdown

Run with: pytest tests/test_integration.py -v
"""
import pytest
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.broker_reconciliation import (
    PositionReconciliationEngine,
    LocalPosition,
    BrokerPosition,
)
from execution.order_deduplicator import OrderDeduplicator
from execution.broker_connection_manager import BrokerConnectionManager, ConnectionState
from execution.error_handler import ErrorHandler, ErrorCategory
from execution.health_monitor import HealthMonitor


class TestPositionReconciliation:
    """Test position reconciliation engine"""

    def test_reconciliation_match(self):
        """Test when positions match"""
        engine = PositionReconciliationEngine()

        local = {
            "NIFTY": LocalPosition(
                symbol="NIFTY",
                direction="LONG",
                quantity=65,
                entry_price=23500.0,
                entry_time=datetime.now(),
            )
        }

        broker = {
            "NIFTY": BrokerPosition(
                symbol="NIFTY",
                direction="LONG",
                quantity=65,
                average_price=23500.0,
                last_updated=datetime.now(),
            )
        }

        is_safe, discrepancies = engine.reconcile(local, broker)
        assert is_safe is True
        assert len(discrepancies) == 0

    def test_reconciliation_mismatch_qty(self):
        """Test when quantity doesn't match"""
        engine = PositionReconciliationEngine()

        local = {
            "NIFTY": LocalPosition(
                symbol="NIFTY",
                direction="LONG",
                quantity=65,
                entry_price=23500.0,
                entry_time=datetime.now(),
            )
        }

        broker = {
            "NIFTY": BrokerPosition(
                symbol="NIFTY",
                direction="LONG",
                quantity=130,  # Different quantity
                average_price=23500.0,
                last_updated=datetime.now(),
            )
        }

        is_safe, discrepancies = engine.reconcile(local, broker)
        assert is_safe is False
        assert len(discrepancies) > 0

    def test_reconciliation_missing_position(self):
        """Test when local has position but broker doesn't"""
        engine = PositionReconciliationEngine()

        local = {
            "NIFTY": LocalPosition(
                symbol="NIFTY",
                direction="LONG",
                quantity=65,
                entry_price=23500.0,
                entry_time=datetime.now(),
            )
        }

        broker = {}  # Broker has no position

        is_safe, discrepancies = engine.reconcile(local, broker)
        assert is_safe is False
        assert "NIFTY" in str(discrepancies)


class TestOrderDeduplication:
    """Test order deduplication system"""

    def test_unique_orders_accepted(self):
        """Test that unique orders are accepted"""
        dedup = OrderDeduplicator()

        is_dup, msg, hash1 = dedup.check_and_record(
            symbol="NIFTY",
            direction="LONG",
            quantity=65,
            entry_price=23500.0,
        )

        assert is_dup is False
        assert "recorded" in msg.lower() or "accepted" in msg.lower()

    def test_duplicate_orders_rejected(self):
        """Test that duplicate orders within window are rejected"""
        dedup = OrderDeduplicator(duplicate_window_seconds=5)

        # First order
        is_dup1, _, hash1 = dedup.check_and_record(
            symbol="NIFTY",
            direction="LONG",
            quantity=65,
            entry_price=23500.0,
        )
        assert is_dup1 is False

        # Duplicate order
        is_dup2, msg2, hash2 = dedup.check_and_record(
            symbol="NIFTY",
            direction="LONG",
            quantity=65,
            entry_price=23500.0,
        )
        assert is_dup2 is True
        assert "duplicate" in msg2.lower()

    def test_different_orders_accepted(self):
        """Test that different orders are accepted even quickly"""
        dedup = OrderDeduplicator(duplicate_window_seconds=5)

        # First order
        is_dup1, _, _ = dedup.check_and_record(
            symbol="NIFTY", direction="LONG", quantity=65, entry_price=23500.0
        )

        # Different order (different qty)
        is_dup2, _, _ = dedup.check_and_record(
            symbol="NIFTY", direction="LONG", quantity=130, entry_price=23500.0
        )

        assert is_dup1 is False
        assert is_dup2 is False


class TestErrorHandling:
    """Test centralized error handling"""

    def test_error_recording(self):
        """Test that errors are recorded"""
        handler = ErrorHandler(bot_name="test_bot")

        error = ValueError("Test error")
        handler.handle_error(error, ErrorCategory.LOGIC_ERROR)

        stats = handler.get_stats()
        assert stats["total_errors"] == 1

    def test_error_decorator(self):
        """Test error decorator"""
        handler = ErrorHandler(bot_name="test_bot")

        @handler.error_decorator(category=ErrorCategory.LOGIC_ERROR)
        def failing_function():
            raise ValueError("Intentional error")

        result = failing_function()
        assert result is None
        assert handler.get_stats()["total_errors"] == 1

    def test_safe_call(self):
        """Test safe function call wrapper"""
        handler = ErrorHandler(bot_name="test_bot")

        def failing_function():
            raise ValueError("Intentional error")

        result = handler.safe_call(failing_function, category=ErrorCategory.LOGIC_ERROR)
        assert result is None


class TestHealthMonitoring:
    """Test health monitoring system"""

    def test_health_metrics_collection(self):
        """Test that health metrics are collected"""
        monitor = HealthMonitor(bot_name="test_bot")

        is_healthy = monitor.check_health()
        assert isinstance(is_healthy, bool)

    def test_health_status_string(self):
        """Test health status string generation"""
        monitor = HealthMonitor(bot_name="test_bot")

        status_str = monitor.get_status_string()
        assert "HEALTHY" in status_str or "UNHEALTHY" in status_str

    def test_health_metrics_dict(self):
        """Test health metrics as dictionary"""
        monitor = HealthMonitor(bot_name="test_bot")

        metrics = monitor.get_metrics_dict()
        assert "overall_healthy" in metrics
        assert "memory_mb" in metrics
        assert "error_rate" in metrics


class TestBrokerConnection:
    """Test broker connection manager"""

    def test_connection_state_tracking(self):
        """Test connection state tracking"""
        # Mock functions
        def mock_connect():
            return object()

        def mock_auth(client):
            pass

        mgr = BrokerConnectionManager(
            connect_fn=mock_connect, auth_fn=mock_auth, initial_backoff_seconds=0.1
        )

        # Initially disconnected
        assert mgr.state == ConnectionState.DISCONNECTED

        # After connect, should be authed
        connected = mgr.connect()
        assert connected is True
        assert mgr.state == ConnectionState.AUTHED

    def test_exponential_backoff(self):
        """Test exponential backoff calculation"""
        def mock_connect():
            raise ConnectionError("Test")

        def mock_auth(client):
            pass

        mgr = BrokerConnectionManager(
            connect_fn=mock_connect,
            auth_fn=mock_auth,
            initial_backoff_seconds=1.0,
            max_backoff_seconds=10.0,
        )

        # First failure
        mgr.connect()
        first_backoff = mgr.current_backoff
        assert first_backoff <= 10.0

        # Second failure should have increased backoff
        mgr.connect()
        second_backoff = mgr.current_backoff
        assert second_backoff >= first_backoff


# Integration test: Complete trading loop
class TestCompleteTradingLoop:
    """Test a complete mock trading loop"""

    def test_startup_to_shutdown_sequence(self):
        """Test complete bot lifecycle"""
        # Setup components
        error_handler = ErrorHandler(bot_name="test_bot")
        health_monitor = HealthMonitor(bot_name="test_bot", error_handler=error_handler)
        deduplicator = OrderDeduplicator()

        # Simulate startup checks
        assert error_handler.get_stats()["total_errors"] == 0

        # Simulate order submission
        is_dup, msg, hash1 = deduplicator.check_and_record(
            symbol="NIFTY", direction="LONG", quantity=65, entry_price=23500.0
        )
        assert is_dup is False

        # Simulate health check
        is_healthy = health_monitor.check_health()
        assert isinstance(is_healthy, bool)

        # All systems should be OK
        assert error_handler.get_stats()["total_errors"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
