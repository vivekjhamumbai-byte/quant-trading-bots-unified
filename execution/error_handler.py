"""
Centralized Error Handling for All Bots

Ensures consistent error logging, recovery procedures, and notifications
across all trading bots. Handles:
- API errors (broker unavailable, timeout, invalid response)
- Data errors (missing quotes, invalid instruments)
- Logic errors (signal generation, risk calculation)
- System errors (file I/O, database)
- Network errors (connection loss, reconnect)
"""
import logging
import traceback
import sys
from datetime import datetime
from typing import Callable, Optional, Any, Dict
from functools import wraps
from enum import Enum

log = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error classification for appropriate response"""
    DEBUG = "DEBUG"      # Informational, no action
    WARNING = "WARNING"  # Worth logging but not blocking
    ERROR = "ERROR"      # Trading action blocked
    CRITICAL = "CRITICAL"  # Bot should stop


class ErrorCategory(Enum):
    """Error type classification"""
    BROKER_API = "BROKER_API"          # Broker API error
    DATA_QUALITY = "DATA_QUALITY"      # Missing/invalid data
    RISK_VIOLATION = "RISK_VIOLATION"  # Risk limit exceeded
    LOGIC_ERROR = "LOGIC_ERROR"        # Signal/calculation error
    NETWORK_ERROR = "NETWORK_ERROR"    # Network/connection issue
    SYSTEM_ERROR = "SYSTEM_ERROR"      # System/file/DB error
    UNKNOWN = "UNKNOWN"                # Unknown error


class BotError(Exception):
    """Base exception for all bot-related errors"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict] = None,
        original_exception: Optional[Exception] = None,
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now()
        super().__init__(message)


class ErrorHandler:
    """
    Central error handling and recovery coordinator.

    Usage:
        handler = ErrorHandler(bot_name="orb_lite")

        try:
            # trading logic
        except Exception as e:
            handler.handle_error(e, ErrorCategory.BROKER_API)
    """

    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.error_count = 0
        self.error_history = []
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10
        self.recovery_strategies = {}
        self._setup_recovery_strategies()

    def _setup_recovery_strategies(self):
        """Register recovery strategies for each error type"""
        self.recovery_strategies = {
            ErrorCategory.BROKER_API: self._recover_broker_api,
            ErrorCategory.NETWORK_ERROR: self._recover_network,
            ErrorCategory.DATA_QUALITY: self._recover_data_quality,
            ErrorCategory.RISK_VIOLATION: self._recover_risk_violation,
            ErrorCategory.LOGIC_ERROR: self._recover_logic_error,
            ErrorCategory.SYSTEM_ERROR: self._recover_system_error,
        }

    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: Optional[Dict] = None,
        should_stop: bool = False,
    ) -> bool:
        """
        Handle an error with appropriate logging and recovery.

        Args:
            error: The exception that occurred
            category: Error classification
            context: Additional context about the error
            should_stop: If True, bot should stop trading

        Returns:
            True if error was handled and bot can continue,
            False if bot should stop
        """
        self.error_count += 1
        self.consecutive_errors += 1

        # Create error record
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "bot": self.bot_name,
            "category": category.value,
            "message": str(error),
            "context": context or {},
            "traceback": traceback.format_exc(),
        }
        self.error_history.append(error_record)

        # Log error
        log.error(
            f"[{self.bot_name}] {category.value}: {error}\n"
            f"Context: {context}\n"
            f"Traceback: {traceback.format_exc()}"
        )

        # Check if we're in error spiral
        if self.consecutive_errors >= self.max_consecutive_errors:
            log.critical(
                f"[{self.bot_name}] Too many consecutive errors ({self.consecutive_errors}). "
                f"Bot will stop to prevent damage."
            )
            return False  # STOP

        # Attempt recovery
        recovery_fn = self.recovery_strategies.get(category)
        if recovery_fn:
            if recovery_fn(error, context):
                self.consecutive_errors = 0  # Reset on successful recovery
                log.info(f"[{self.bot_name}] Recovered from {category.value}")
                return True  # CONTINUE

        # If no recovery strategy or recovery failed
        if should_stop:
            log.warning(f"[{self.bot_name}] Stopping bot due to error")
            return False  # STOP

        return True  # CONTINUE (with caution)

    def _recover_broker_api(self, error: Exception, context: Optional[Dict]) -> bool:
        """Recover from broker API errors"""
        if "timeout" in str(error).lower() or "connection" in str(error).lower():
            log.warning("Broker API timeout/connection error. Will retry on next poll.")
            return True
        if "502" in str(error) or "503" in str(error):
            log.warning("Broker temporarily unavailable (502/503). Waiting for recovery...")
            return True
        return False

    def _recover_network(self, error: Exception, context: Optional[Dict]) -> bool:
        """Recover from network errors"""
        log.warning("Network error detected. Attempting reconnection...")
        return True  # Connection manager will handle actual reconnection

    def _recover_data_quality(self, error: Exception, context: Optional[Dict]) -> bool:
        """Recover from data quality errors"""
        log.warning("Data quality issue. Will skip this signal and continue.")
        return True

    def _recover_risk_violation(self, error: Exception, context: Optional[Dict]) -> bool:
        """Handle risk violations"""
        log.warning(f"Risk limit violated: {error}. Order blocked (by design).")
        return True  # Blocking the order is the correct recovery

    def _recover_logic_error(self, error: Exception, context: Optional[Dict]) -> bool:
        """Recover from strategy logic errors"""
        log.error(f"Strategy logic error: {error}. Will continue monitoring.")
        return True

    def _recover_system_error(self, error: Exception, context: Optional[Dict]) -> bool:
        """Recover from system errors"""
        log.error(f"System error: {error}. Will retry next cycle.")
        return True

    def safe_call(
        self,
        fn: Callable,
        *args,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        should_stop: bool = False,
        **kwargs,
    ) -> Any:
        """
        Safely call a function with automatic error handling.

        Usage:
            result = handler.safe_call(
                get_market_quote,
                "NIFTY",
                category=ErrorCategory.BROKER_API
            )
        """
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, category, context={"function": fn.__name__}, should_stop=should_stop)
            return None

    def error_decorator(
        self,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        should_stop: bool = False,
    ):
        """
        Decorator for automatic error handling on functions.

        Usage:
            @handler.error_decorator(category=ErrorCategory.BROKER_API)
            def get_quotes():
                ...
        """

        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    self.handle_error(
                        e,
                        category,
                        context={"function": fn.__name__, "args": str(args)[:100]},
                        should_stop=should_stop,
                    )
                    return None

            return wrapper

        return decorator

    def get_stats(self) -> Dict:
        """Return error statistics"""
        return {
            "total_errors": self.error_count,
            "consecutive_errors": self.consecutive_errors,
            "error_history_size": len(self.error_history),
            "last_error_time": self.error_history[-1]["timestamp"] if self.error_history else None,
        }

    def log_stats(self):
        """Log error statistics"""
        stats = self.get_stats()
        log.info(
            f"[{self.bot_name}] Error Stats: "
            f"total={stats['total_errors']}, "
            f"consecutive={stats['consecutive_errors']}, "
            f"last={stats['last_error_time']}"
        )

    def clear_history(self):
        """Clear error history to save memory"""
        self.error_history = []
        log.debug(f"[{self.bot_name}] Error history cleared")
