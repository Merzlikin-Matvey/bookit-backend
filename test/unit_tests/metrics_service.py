import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import random

from server.services.metrics import simulate_day_and_metrics


class TestMetricsService:
    
    @pytest.mark.asyncio
    @patch("server.services.metrics.user_registrations_total")
    @patch("server.services.metrics.user_logins_total")
    @patch("server.services.metrics.active_users")
    @patch("server.services.metrics.session_duration_seconds")
    @patch("server.services.metrics.api_errors_total")
    @patch("server.services.metrics.bookings_total")
    @patch("server.services.metrics.average_booking_time_seconds")
    @patch("server.services.metrics.random")
    @patch("server.services.metrics.asyncio.sleep")
    async def test_simulate_day_and_metrics(
        self, 
        mock_sleep,
        mock_random,
        mock_average_booking_time,
        mock_bookings_total,
        mock_api_errors,
        mock_session_duration,
        mock_active_users,
        mock_logins,
        mock_registrations
    ):
        """Test that simulation function updates metrics correctly"""
        # Setup
        mock_sleep.side_effect = asyncio.CancelledError  # To exit the infinite loop
        
        # Setup random values
        mock_random.randint.side_effect = [3, 10, 150, 5, 2]  # registrations, logins, active users, bookings, api errors
        mock_random.uniform.side_effect = [1500, 1800]  # session duration, average booking time
        mock_random.random.return_value = 0.15  # 15% < 20%, so should trigger API error
        
        # Setup labels mock for api_errors
        mock_labels = MagicMock()
        mock_api_errors.labels.return_value = mock_labels
        
        # Execute
        try:
            await simulate_day_and_metrics()
        except asyncio.CancelledError:
            pass  # Expected to exit the loop
        
        # Assert - verify all metrics were updated with expected values
        mock_registrations.inc.assert_called_once_with(3)
        mock_logins.inc.assert_called_once_with(10)
        mock_active_users.set.assert_called_once_with(150)
        mock_session_duration.set.assert_called_once_with(1500)
        mock_bookings_total.inc.assert_called_once_with(5)
        mock_average_booking_time.set.assert_called_once_with(1800)
        
        # Check API errors with labels
        mock_api_errors.labels.assert_called_once_with(endpoint="default")
        mock_labels.inc.assert_called_once_with(2)
        
        # Verify sleep was called with 1 second
        mock_sleep.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    @patch("server.services.metrics.user_registrations_total")
    @patch("server.services.metrics.user_logins_total")
    @patch("server.services.metrics.active_users")
    @patch("server.services.metrics.session_duration_seconds")
    @patch("server.services.metrics.api_errors_total")
    @patch("server.services.metrics.bookings_total")
    @patch("server.services.metrics.average_booking_time_seconds")
    @patch("server.services.metrics.random")
    @patch("server.services.metrics.asyncio.sleep")
    async def test_simulate_day_and_metrics_no_errors(
        self, 
        mock_sleep,
        mock_random,
        mock_average_booking_time,
        mock_bookings_total,
        mock_api_errors,
        mock_session_duration,
        mock_active_users,
        mock_logins,
        mock_registrations
    ):
        """Test that simulation skips API error updates when random value is higher"""
        # Setup
        mock_sleep.side_effect = asyncio.CancelledError  # To exit the infinite loop
        
        # Setup random values - only difference is random() > 0.2
        mock_random.randint.side_effect = [3, 10, 150, 5]
        mock_random.uniform.side_effect = [1500, 1800]
        mock_random.random.return_value = 0.25  # 25% > 20%, so should NOT trigger API error
        
        # Execute
        try:
            await simulate_day_and_metrics()
        except asyncio.CancelledError:
            pass  # Expected to exit the loop
        
        # Assert - verify metrics were updated but API errors weren't
        mock_api_errors.labels.assert_not_called()
        mock_registrations.inc.assert_called_once()
        mock_active_users.set.assert_called_once()
