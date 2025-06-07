"""
Unit tests for MEP-006: The Feedback Loop (provide_feedback Tool)

Tests the provide_feedback tool functionality including:
- Basic feedback submission with required parameters
- Optional missing_capability parameter handling
- Proper logging to stderr 
- JSON response format validation
- Error handling for edge cases
"""

import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from mcp_server.server.tools import provide_feedback


class TestProvideFeedbackTool:
    """Test MEP-006 provide_feedback tool functionality."""

    @pytest.mark.asyncio
    async def test_basic_successful_feedback(self):
        """Test basic feedback submission for successful task."""
        # Capture stderr
        captured_stderr = StringIO()

        with patch.object(sys, 'stderr', captured_stderr):
            result = await provide_feedback(
                feedback_text="Task completed successfully",
                is_success=True
            )

        # Verify JSON response
        response = json.loads(result)
        assert response["status"] == "Feedback received. Thank you."

        # Verify stderr logging
        stderr_output = captured_stderr.getvalue().strip()
        expected_log = '[AGENT_FEEDBACK] | SUCCESS: True | MISSING: None | TEXT: "Task completed successfully"'
        assert stderr_output == expected_log

    @pytest.mark.asyncio
    async def test_basic_failed_feedback(self):
        """Test basic feedback submission for failed task."""
        captured_stderr = StringIO()

        with patch.object(sys, 'stderr', captured_stderr):
            result = await provide_feedback(
                feedback_text="Task failed due to missing permissions",
                is_success=False
            )

        # Verify JSON response
        response = json.loads(result)
        assert response["status"] == "Feedback received. Thank you."

        # Verify stderr logging
        stderr_output = captured_stderr.getvalue().strip()
        expected_log = '[AGENT_FEEDBACK] | SUCCESS: False | MISSING: None | TEXT: "Task failed due to missing permissions"'
        assert stderr_output == expected_log

    @pytest.mark.asyncio
    async def test_feedback_with_missing_capability(self):
        """Test feedback submission with missing_capability parameter."""
        captured_stderr = StringIO()

        with patch.object(sys, 'stderr', captured_stderr):
            result = await provide_feedback(
                feedback_text="Could not apply animations to shapes",
                is_success=False,
                missing_capability="Shape animation API"
            )

        # Verify JSON response
        response = json.loads(result)
        assert response["status"] == "Feedback received. Thank you."

        # Verify stderr logging with missing capability
        stderr_output = captured_stderr.getvalue().strip()
        expected_log = '[AGENT_FEEDBACK] | SUCCESS: False | MISSING: Shape animation API | TEXT: "Could not apply animations to shapes"'
        assert stderr_output == expected_log

    @pytest.mark.asyncio
    async def test_feedback_with_empty_missing_capability(self):
        """Test feedback submission with empty string for missing_capability."""
        captured_stderr = StringIO()

        with patch.object(sys, 'stderr', captured_stderr):
            result = await provide_feedback(
                feedback_text="Task worked but was complex",
                is_success=True,
                missing_capability=""
            )

        # Verify JSON response
        response = json.loads(result)
        assert response["status"] == "Feedback received. Thank you."

        # Verify stderr logging - empty string should be treated as provided value
        stderr_output = captured_stderr.getvalue().strip()
        expected_log = '[AGENT_FEEDBACK] | SUCCESS: True | MISSING:  | TEXT: "Task worked but was complex"'
        assert stderr_output == expected_log

    @pytest.mark.asyncio
    async def test_feedback_text_with_quotes(self):
        """Test feedback text containing quotes is properly escaped in log."""
        captured_stderr = StringIO()

        with patch.object(sys, 'stderr', captured_stderr):
            result = await provide_feedback(
                feedback_text='Used prs.slides[0].shapes["title"] successfully',
                is_success=True
            )

        # Verify JSON response
        response = json.loads(result)
        assert response["status"] == "Feedback received. Thank you."

        # Verify stderr logging handles quotes in text
        stderr_output = captured_stderr.getvalue().strip()
        expected_log = '[AGENT_FEEDBACK] | SUCCESS: True | MISSING: None | TEXT: "Used prs.slides[0].shapes["title"] successfully"'
        assert stderr_output == expected_log

    @pytest.mark.asyncio
    async def test_feedback_text_multiline(self):
        """Test feedback with multiline text."""
        captured_stderr = StringIO()
        multiline_text = "Task completed.\nHowever, encountered some challenges.\nOverall successful."

        with patch.object(sys, 'stderr', captured_stderr):
            result = await provide_feedback(
                feedback_text=multiline_text,
                is_success=True
            )

        # Verify JSON response
        response = json.loads(result)
        assert response["status"] == "Feedback received. Thank you."

        # Verify stderr logging
        stderr_output = captured_stderr.getvalue().strip()
        expected_log = f'[AGENT_FEEDBACK] | SUCCESS: True | MISSING: None | TEXT: "{multiline_text}"'
        assert stderr_output == expected_log

    @pytest.mark.asyncio
    async def test_feedback_long_text(self):
        """Test feedback with very long text."""
        captured_stderr = StringIO()
        long_text = "A" * 1000  # 1000 character text

        with patch.object(sys, 'stderr', captured_stderr):
            result = await provide_feedback(
                feedback_text=long_text,
                is_success=True
            )

        # Verify JSON response
        response = json.loads(result)
        assert response["status"] == "Feedback received. Thank you."

        # Verify stderr logging handles long text
        stderr_output = captured_stderr.getvalue().strip()
        expected_log = f'[AGENT_FEEDBACK] | SUCCESS: True | MISSING: None | TEXT: "{long_text}"'
        assert stderr_output == expected_log

    @pytest.mark.asyncio
    async def test_feedback_special_characters(self):
        """Test feedback with special characters and unicode."""
        captured_stderr = StringIO()
        special_text = "Task with special chars: àáâãäå æç èéêë ìíîï ñ òóôõö ùúûü ýÿ"

        with patch.object(sys, 'stderr', captured_stderr):
            result = await provide_feedback(
                feedback_text=special_text,
                is_success=True
            )

        # Verify JSON response
        response = json.loads(result)
        assert response["status"] == "Feedback received. Thank you."

        # Verify stderr logging handles special characters
        stderr_output = captured_stderr.getvalue().strip()
        expected_log = f'[AGENT_FEEDBACK] | SUCCESS: True | MISSING: None | TEXT: "{special_text}"'
        assert stderr_output == expected_log

    @pytest.mark.asyncio
    async def test_missing_capability_with_special_chars(self):
        """Test missing_capability parameter with special characters."""
        captured_stderr = StringIO()

        with patch.object(sys, 'stderr', captured_stderr):
            result = await provide_feedback(
                feedback_text="Need better API support",
                is_success=False,
                missing_capability="Unicode text & formatting API"
            )

        # Verify JSON response
        response = json.loads(result)
        assert response["status"] == "Feedback received. Thank you."

        # Verify stderr logging
        stderr_output = captured_stderr.getvalue().strip()
        expected_log = '[AGENT_FEEDBACK] | SUCCESS: False | MISSING: Unicode text & formatting API | TEXT: "Need better API support"'
        assert stderr_output == expected_log

    @pytest.mark.asyncio
    async def test_stderr_flushing(self):
        """Test that stderr output is properly flushed."""
        captured_stderr = StringIO()

        # Mock print to verify flush=True is called
        with patch('builtins.print') as mock_print, \
             patch.object(sys, 'stderr', captured_stderr):

            await provide_feedback(
                feedback_text="Test flushing",
                is_success=True
            )

            # Verify print was called with flush=True
            mock_print.assert_called_once()
            call_args, call_kwargs = mock_print.call_args
            assert call_kwargs.get('flush') is True
            assert call_kwargs.get('file') is captured_stderr

    @pytest.mark.asyncio
    async def test_return_value_structure(self):
        """Test that return value is properly structured JSON."""
        result = await provide_feedback(
            feedback_text="Test return structure",
            is_success=True
        )

        # Verify result is valid JSON
        response = json.loads(result)

        # Verify structure
        assert isinstance(response, dict)
        assert len(response) == 1
        assert "status" in response
        assert response["status"] == "Feedback received. Thank you."

        # Verify no extra fields
        assert list(response.keys()) == ["status"]
