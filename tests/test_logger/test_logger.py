"""
Tests for the logger module of the CAC Core package.

This module contains test cases for the logger functionality, ensuring that:
1. Loggers are created with the correct configuration
2. Logger instances are properly cached and reused
3. Log handlers are not duplicated when retrieving existing loggers
4. Formatters are correctly applied to log output

The logger module is a critical component of the CAC framework as it provides
consistent logging behavior across all applications that use the framework.
"""

import logging
import cac_core as cac

class TestLogger:
    """
    Test suite for the logger module.

    This test class verifies the functionality of the logging system,
    ensuring that loggers are properly created, configured, and don't
    duplicate handlers when requested multiple times with the same name.

    Test cases:
    - Logger creation with proper name and level
    - Handler configuration with formatters
    - Prevention of duplicate handlers
    """

    def test_logger_creation(self):
        """Test logger creation and configuration."""
        logger = cac.logger.new("test_module")

        assert logger.name == "test_module"
        assert logger.level <= logging.INFO
        assert len(logger.handlers) > 0

        # Test that handler has formatter
        handler = logger.handlers[0]
        assert handler.formatter is not None

    def test_logger_duplicate_handlers(self):
        """Test that multiple calls to new() don't add duplicate handlers."""
        logger1 = cac.logger.new("test_duplicate")
        handlers_count = len(logger1.handlers)

        # Get logger again with same name
        logger2 = cac.logger.new("test_duplicate")

        # Should be same logger instance
        assert logger1 is logger2
        # Should not have added more handlers
        assert len(logger2.handlers) == handlers_count
