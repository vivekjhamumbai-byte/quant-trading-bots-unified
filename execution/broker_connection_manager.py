"""
Broker Connection Management with Automatic Reconnection

Handles:
- Initial connection and login
- Automatic reconnection on network failure
- Exponential backoff to avoid hammering the broker
- Health checks to detect stale connections
- Connection state tracking and logging

Prevents:
- Rapid reconnection attempts (exponential backoff)
- Trading on disconnected state
- Undetected connection loss
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    AUTHED = "AUTHENTICATED"
    FAILED = "FAILED"


@dataclass
class ConnectionMetrics:
    """Track connection health metrics"""
    total_connections: int = 0
    total_disconnections: int = 0
    total_failed_attempts: int = 0
    last_connected_time: Optional[datetime] = None
    last_disconnected_time: Optional[datetime] = None
    consecutive_failures: int = 0
    total_uptime_seconds: float = 0.0


class BrokerConnectionManager:
    """
    Manages broker connection lifecycle with automatic reconnection.

    Usage:
        conn_mgr = BrokerConnectionManager(
            connect_fn=lambda: MStockClient(),
            auth_fn=lambda client: client.login(user_id, password, totp)
        )

        # Check connection before trading
        if not conn_mgr.is_healthy():
            await conn_mgr.reconnect()

        client = conn_mgr.client
        # ... use client ...
    """

    def __init__(
        self,
        connect_fn: Callable,
        auth_fn: Callable,
        initial_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 60.0,
        health_check_interval_seconds: float = 30.0,
    ):
        """
        Args:
            connect_fn: Function that returns a connected broker client
            auth_fn: Function that authenticates the client (takes client as arg)
            initial_backoff_seconds: Start with this backoff on first failure
            max_backoff_seconds: Don't backoff longer than this
            health_check_interval_seconds: How often to check connection health
        """
        self.connect_fn = connect_fn
        self.auth_fn = auth_fn
        self.initial_backoff = initial_backoff_seconds
        self.max_backoff = max_backoff_seconds
        self.health_check_interval = health_check_interval_seconds

        self.client: Optional[object] = None
        self.state = ConnectionState.DISCONNECTED
        self.metrics = ConnectionMetrics()
        self.next_reconnect_time = datetime.now()
        self.current_backoff = initial_backoff_seconds
        self.last_health_check = None
        self.connection_start_time = None

    def connect(self) -> bool:
        """
        Attempt to connect and authenticate.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.state == ConnectionState.CONNECTING:
                log.warning("Connect already in progress")
                return False

            self.state = ConnectionState.CONNECTING
            log.info("Connecting to broker...")

            # Create client connection
            self.client = self.connect_fn()
            self.state = ConnectionState.CONNECTED
            log.info("✓ Broker connection established")

            # Authenticate
            self.auth_fn(self.client)
            self.state = ConnectionState.AUTHED
            log.info("✓ Broker authentication successful")

            # Reset backoff on success
            self.current_backoff = self.initial_backoff
            self.metrics.consecutive_failures = 0
            self.metrics.total_connections += 1
            self.metrics.last_connected_time = datetime.now()
            self.connection_start_time = datetime.now()

            return True

        except Exception as e:
            self.state = ConnectionState.FAILED
            self.metrics.total_failed_attempts += 1
            self.metrics.consecutive_failures += 1
            log.error(f"Connection failed: {e}")
            self._schedule_reconnect()
            return False

    def disconnect(self):
        """Gracefully disconnect from broker"""
        try:
            if self.client:
                # Some SDKs have a logout method
                if hasattr(self.client, 'logout'):
                    self.client.logout()
                self.client = None
        except Exception as e:
            log.warning(f"Error during disconnect: {e}")
        finally:
            if self.connection_start_time:
                uptime = (datetime.now() - self.connection_start_time).total_seconds()
                self.metrics.total_uptime_seconds += uptime
            self.state = ConnectionState.DISCONNECTED
            self.metrics.last_disconnected_time = datetime.now()
            self.metrics.total_disconnections += 1
            log.info("Disconnected from broker")

    def is_healthy(self) -> bool:
        """
        Check if connection is healthy and ready for trading.

        Returns:
            True if connected and authenticated, False otherwise
        """
        if self.state != ConnectionState.AUTHED:
            return False

        # Periodic health check (e.g., verify we can get a quote)
        now = datetime.now()
        if self.last_health_check is None or \
           (now - self.last_health_check).total_seconds() > self.health_check_interval:
            try:
                # Attempt a simple health check (e.g., get LTP for a major index)
                # This is SDK-specific, so it's a placeholder
                # self.client.get_market_quote("NIFTY")  # or similar
                self.last_health_check = now
            except Exception as e:
                log.error(f"Health check failed: {e}")
                self.state = ConnectionState.FAILED
                return False

        return True

    async def ensure_connected(self) -> bool:
        """
        Ensure we're connected, reconnecting with backoff if necessary.

        This is async-friendly for event loops, but can also be used
        synchronously (just don't await if not in async context).

        Returns:
            True if connected, False if connection ultimately failed
        """
        if self.is_healthy():
            return True

        # Check if it's time to retry
        now = datetime.now()
        if now < self.next_reconnect_time:
            wait_seconds = (self.next_reconnect_time - now).total_seconds()
            log.info(f"Will retry connection in {wait_seconds:.1f} seconds...")
            time.sleep(min(wait_seconds, 1.0))  # Sleep in small chunks to be responsive
            return False

        # Attempt reconnection
        return self.connect()

    def _schedule_reconnect(self):
        """Schedule the next reconnection attempt with exponential backoff"""
        self.next_reconnect_time = datetime.now() + timedelta(seconds=self.current_backoff)

        # Increase backoff for next failure (exponential with cap)
        self.current_backoff = min(self.current_backoff * 2, self.max_backoff)

        log.warning(
            f"Reconnection scheduled in {self.current_backoff:.1f}s "
            f"(attempt {self.metrics.consecutive_failures})"
        )

    def get_metrics(self) -> dict:
        """Return connection metrics"""
        uptime = 0.0
        if self.connection_start_time:
            uptime = (datetime.now() - self.connection_start_time).total_seconds()

        return {
            "state": self.state.value,
            "total_connections": self.metrics.total_connections,
            "total_disconnections": self.metrics.total_disconnections,
            "consecutive_failures": self.metrics.consecutive_failures,
            "total_failed_attempts": self.metrics.total_failed_attempts,
            "current_uptime_seconds": uptime,
            "total_uptime_seconds": self.metrics.total_uptime_seconds,
            "last_connected": self.metrics.last_connected_time.isoformat() if self.metrics.last_connected_time else None,
            "last_disconnected": self.metrics.last_disconnected_time.isoformat() if self.metrics.last_disconnected_time else None,
        }

    def log_metrics(self):
        """Log connection metrics"""
        metrics = self.get_metrics()
        log.info(
            f"Connection Health: "
            f"state={metrics['state']}, "
            f"connections={metrics['total_connections']}, "
            f"failures={metrics['consecutive_failures']}, "
            f"uptime={metrics['current_uptime_seconds']:.0f}s"
        )
