"""
Bot Health Monitoring System

Periodically checks bot health and reports status:
- Broker connection health
- Data feed freshness
- Position reconciliation status
- Error rates
- Memory usage
- Performance metrics

Enables proactive issue detection before they become critical.
"""
import logging
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class HealthMetrics:
    """Health check results"""
    timestamp: datetime
    broker_connected: bool
    data_fresh: bool
    memory_mb: float
    error_rate: float
    last_error_age_seconds: float
    positions_reconciled: bool
    overall_healthy: bool


class HealthMonitor:
    """
    Continuously monitors bot health and alerts on degradation.

    Usage:
        monitor = HealthMonitor(
            bot_name="orb_lite",
            connection_mgr=connection_manager,
            error_handler=error_handler
        )

        is_healthy = monitor.check_health()
        if not is_healthy:
            log.warning("Bot health degraded")
    """

    def __init__(
        self,
        bot_name: str,
        connection_mgr=None,
        error_handler=None,
        check_interval_seconds: float = 60.0,
    ):
        self.bot_name = bot_name
        self.connection_mgr = connection_mgr
        self.error_handler = error_handler
        self.check_interval = check_interval_seconds
        self.last_check_time = None
        self.last_healthy = True
        self.health_degradation_count = 0
        self.process = psutil.Process(os.getpid())

    def check_health(self) -> bool:
        """
        Run full health check.

        Returns:
            True if all systems healthy, False if any issue detected
        """
        now = datetime.now()

        # Check interval
        if self.last_check_time and (now - self.last_check_time).total_seconds() < self.check_interval:
            return self.last_healthy

        self.last_check_time = now
        metrics = self._collect_metrics()

        # Determine overall health
        overall_healthy = (
            metrics.broker_connected
            and metrics.data_fresh
            and metrics.error_rate < 0.1  # Less than 10% error rate
            and metrics.memory_mb < 500  # Less than 500 MB
            and metrics.positions_reconciled
        )

        if not overall_healthy:
            self.health_degradation_count += 1
            if self.health_degradation_count >= 3:  # 3 consecutive unhealthy checks
                log.critical(f"[{self.bot_name}] Health CRITICAL - {self.health_degradation_count} consecutive unhealthy checks")
        else:
            self.health_degradation_count = 0

        # Log if health changed
        if overall_healthy != self.last_healthy:
            status = "✓ HEALTHY" if overall_healthy else "✗ UNHEALTHY"
            log.warning(f"[{self.bot_name}] Health status: {status}")
            self.last_healthy = overall_healthy

        return overall_healthy

    def _collect_metrics(self) -> HealthMetrics:
        """Collect all health metrics"""
        broker_connected = self._check_broker_connection()
        data_fresh = self._check_data_freshness()
        memory_mb = self._check_memory()
        error_rate = self._check_error_rate()
        last_error_age = self._check_last_error_age()
        reconciled = self._check_reconciliation()

        return HealthMetrics(
            timestamp=datetime.now(),
            broker_connected=broker_connected,
            data_fresh=data_fresh,
            memory_mb=memory_mb,
            error_rate=error_rate,
            last_error_age_seconds=last_error_age,
            positions_reconciled=reconciled,
            overall_healthy=all([
                broker_connected,
                data_fresh,
                error_rate < 0.1,
                memory_mb < 500,
                reconciled,
            ]),
        )

    def _check_broker_connection(self) -> bool:
        """Check if broker connection is healthy"""
        if not self.connection_mgr:
            return True  # Assume OK if no connection manager
        return self.connection_mgr.is_healthy()

    def _check_data_freshness(self) -> bool:
        """Check if data is recent (not stale)"""
        # This would be populated by the actual bot
        # For now, assume fresh if we're running
        return True

    def _check_memory(self) -> float:
        """Check memory usage in MB"""
        try:
            mem_info = self.process.memory_info()
            return mem_info.rss / (1024 * 1024)  # Convert to MB
        except Exception as e:
            log.warning(f"Could not get memory info: {e}")
            return 0.0

    def _check_error_rate(self) -> float:
        """Check error rate"""
        if not self.error_handler:
            return 0.0

        stats = self.error_handler.get_stats()
        if stats.get("total_errors", 0) == 0:
            return 0.0

        # Simple heuristic: recent errors as ratio
        # Better: track errors in last N minutes
        recent_errors = sum(
            1 for e in self.error_handler.error_history[-50:]
            if (datetime.now() - datetime.fromisoformat(e["timestamp"])).total_seconds() < 300
        )
        return recent_errors / 50.0 if recent_errors > 0 else 0.0

    def _check_last_error_age(self) -> float:
        """Age of the last error in seconds"""
        if not self.error_handler or not self.error_handler.error_history:
            return float("inf")

        last_error_time = datetime.fromisoformat(self.error_handler.error_history[-1]["timestamp"])
        return (datetime.now() - last_error_time).total_seconds()

    def _check_reconciliation(self) -> bool:
        """Check if positions are reconciled"""
        # This would be set by the bot's reconciliation logic
        # For now, assume OK
        return True

    def get_status_string(self) -> str:
        """Get human-readable health status"""
        metrics = self._collect_metrics()
        status = "✓ HEALTHY" if metrics.overall_healthy else "✗ UNHEALTHY"

        return (
            f"{status}\n"
            f"  Broker: {'✓' if metrics.broker_connected else '✗'}\n"
            f"  Data: {'✓' if metrics.data_fresh else '✗'}\n"
            f"  Memory: {metrics.memory_mb:.0f}MB\n"
            f"  Error Rate: {metrics.error_rate*100:.1f}%\n"
            f"  Last Error: {metrics.last_error_age_seconds:.0f}s ago\n"
            f"  Reconciled: {'✓' if metrics.positions_reconciled else '✗'}"
        )

    def get_metrics_dict(self) -> Dict:
        """Get metrics as dictionary"""
        metrics = self._collect_metrics()
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "overall_healthy": metrics.overall_healthy,
            "broker_connected": metrics.broker_connected,
            "data_fresh": metrics.data_fresh,
            "memory_mb": round(metrics.memory_mb, 1),
            "error_rate": round(metrics.error_rate, 3),
            "last_error_age_seconds": round(metrics.last_error_age_seconds, 1),
            "positions_reconciled": metrics.positions_reconciled,
        }

    def log_status(self):
        """Log health status"""
        log.info(f"[{self.bot_name}] Health:\n{self.get_status_string()}")
