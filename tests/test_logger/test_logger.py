"""
Test suite for the logger module in the cac_core package.
"""

import logging

import cac_core as cac


class TestLogger:
    """Test suite for the logger module."""

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

    def test_logger_debug_level(self):
        """Test logger creation with DEBUG level."""
        logger = cac.logger.new("test_debug_level", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_logger_debug_format(self):
        """Test that DEBUG level uses detailed format string."""
        logger = cac.logger.new("test_debug_format", level=logging.DEBUG)
        handler = logger.handlers[0]
        fmt = handler.formatter._fmt
        # DEBUG format includes process/thread/module info
        assert "%(processName)s" in fmt
        assert "%(module)s" in fmt

    def test_logger_info_format(self):
        """Test that INFO level uses simple format string."""
        logger = cac.logger.new("test_info_format", level=logging.INFO)
        handler = logger.handlers[0]
        fmt = handler.formatter._fmt
        # INFO format is simpler
        assert "%(levelname)s" in fmt
        assert "%(message)s" in fmt

    def test_logger_custom_format(self):
        """Test logger with custom format string."""
        custom_fmt = "%(name)s - %(message)s"
        logger = cac.logger.new("test_custom_format", format_string=custom_fmt)
        handler = logger.handlers[0]
        assert handler.formatter._fmt == custom_fmt

    def test_logger_level_updated_on_second_call(self):
        """Test that calling new() again with a different level updates the logger."""
        logger1 = cac.logger.new("test_level_update", level=logging.INFO)
        assert logger1.level == logging.INFO

        logger2 = cac.logger.new("test_level_update", level=logging.DEBUG)
        assert logger2.level == logging.DEBUG
        # Should still be the same logger instance with no duplicate handlers
        assert logger1 is logger2
        assert len(logger2.handlers) == 1
