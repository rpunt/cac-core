import logging
import pytest
import cac_core as cac


class TestLogger:
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
