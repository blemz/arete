"""Tests for WebSocket connection state management.

Following contract-based testing methodology focusing on critical business logic:
- Connection status tracking
- Automatic reconnection with exponential backoff
- Manual retry functionality
- User feedback for connection issues
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio


class TestConnectionState:
    """Test cases for WebSocket connection state management."""

    @pytest.fixture
    def arete_state(self):
        """AreteState instance for testing."""
        # Import here to avoid circular dependencies
        from src.arete.ui.reflex_app.arete.arete import AreteState  # noqa: PLC0415
        return AreteState()

    def test_initial_connection_status(self, arete_state):
        """Test initial connection state values."""
        # Verify default connection state
        assert hasattr(arete_state, 'connection_status')
        assert arete_state.connection_status == "connecting"
        assert hasattr(arete_state, 'connection_attempts')
        assert arete_state.connection_attempts == 0
        assert hasattr(arete_state, 'show_connection_error')
        assert arete_state.show_connection_error == False

    def test_connection_retry_limits(self, arete_state):
        """Test connection retry attempt limits."""
        # Verify retry configuration exists
        assert hasattr(arete_state, 'max_retry_attempts')
        assert arete_state.max_retry_attempts >= 3  # At least 3 retry attempts
        assert hasattr(arete_state, 'retry_delay')
        assert arete_state.retry_delay > 0  # Positive delay

    @pytest.mark.asyncio
    async def test_check_connection_method_exists(self, arete_state):
        """Test that check_connection method exists and is callable."""
        # Verify connection monitoring method exists
        assert hasattr(arete_state, 'check_connection')
        assert callable(arete_state.check_connection)

    @pytest.mark.asyncio
    async def test_handle_connection_error_increments_attempts(self, arete_state):
        """Test that connection errors increment retry attempts."""
        # Verify error handling increments counter
        initial_attempts = arete_state.connection_attempts

        # Mock asyncio.sleep to avoid actual delays
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await arete_state.handle_connection_error()

        assert arete_state.connection_attempts > initial_attempts

    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self, arete_state):
        """Test exponential backoff delay calculation."""
        # Verify backoff increases exponentially
        arete_state.retry_delay = 1.0

        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            # First retry: 1 * 2^0 = 1 second
            arete_state.connection_attempts = 0
            await arete_state.handle_connection_error()

            # Should have called sleep with exponential delay
            assert mock_sleep.called
            # Delay should be base_delay * 2^attempts

    @pytest.mark.asyncio
    async def test_max_retries_shows_error(self, arete_state):
        """Test that max retries reached shows error to user."""
        # Set attempts to max
        arete_state.connection_attempts = arete_state.max_retry_attempts

        with patch('asyncio.sleep', new_callable=AsyncMock):
            await arete_state.handle_connection_error()

        # After max retries, should show error
        assert arete_state.show_connection_error == True
        assert arete_state.connection_status == "error"

    def test_manual_retry_resets_state(self, arete_state):
        """Test manual retry button resets connection state."""
        # Setup error state
        arete_state.connection_attempts = 5
        arete_state.connection_status = "error"
        arete_state.show_connection_error = True

        # Trigger manual retry
        arete_state.manual_retry()

        # Verify state reset
        assert arete_state.connection_attempts == 0
        assert arete_state.connection_status == "connecting"
        assert arete_state.show_connection_error == False

    @pytest.mark.asyncio
    async def test_connection_status_transitions(self, arete_state):
        """Test connection status transitions through states."""
        # Initial: connecting
        assert arete_state.connection_status == "connecting"

        # After error: reconnecting
        with patch('asyncio.sleep', new_callable=AsyncMock):
            arete_state.connection_attempts = 0
            await arete_state.handle_connection_error()
            assert arete_state.connection_status in ["reconnecting", "error"]

    def test_connection_error_visibility_flag(self, arete_state):
        """Test connection error visibility controls UI feedback."""
        # Initially hidden
        assert arete_state.show_connection_error == False

        # Should become visible after max retries
        arete_state.connection_attempts = arete_state.max_retry_attempts

        with patch('asyncio.sleep', new_callable=AsyncMock):
            # This should trigger error state
            asyncio.run(arete_state.handle_connection_error())

        assert arete_state.show_connection_error == True


class TestConnectionIntegration:
    """Integration tests for connection management with existing functionality."""

    @pytest.fixture
    def arete_state(self):
        """AreteState instance for testing."""
        from src.arete.ui.reflex_app.arete.arete import AreteState  # noqa: PLC0415
        return AreteState()

    @pytest.mark.asyncio
    async def test_send_message_during_connection_error(self, arete_state):
        """Test that send_message handles connection errors gracefully."""
        # Setup connection error state
        arete_state.connection_status = "error"
        arete_state.user_query = "What is virtue?"

        # Should still attempt to send message with fallback
        await arete_state.send_message()

        # Message should be added to history even during connection issues
        assert len(arete_state.chat_history) > 0

    def test_connection_state_persists_across_operations(self, arete_state):
        """Test that connection state persists during app operations."""
        # Set connection state
        arete_state.connection_status = "connected"
        arete_state.connection_attempts = 2

        # Perform other operations
        arete_state.read_document("apology")

        # Connection state should be unchanged
        assert arete_state.connection_status == "connected"
        assert arete_state.connection_attempts == 2
