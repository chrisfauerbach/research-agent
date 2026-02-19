"""Tests for the logging setup utility."""

from __future__ import annotations

import logging
from unittest.mock import patch

from research_agent.util.logging import setup_logging


def test_setup_logging_with_run_id():
    with patch("research_agent.util.logging.settings") as mock_settings:
        mock_settings.log_level = "DEBUG"
        logger = setup_logging(run_id="abc123")

    assert logger.name == "research_agent"
    assert logger.level == logging.DEBUG


def test_setup_logging_without_run_id():
    with patch("research_agent.util.logging.settings") as mock_settings:
        mock_settings.log_level = "INFO"
        logger = setup_logging()

    assert logger.name == "research_agent"
    assert logger.level == logging.INFO


def test_setup_logging_level():
    with patch("research_agent.util.logging.settings") as mock_settings:
        mock_settings.log_level = "WARNING"
        logger = setup_logging(run_id="x")

    assert logger.level == logging.WARNING
