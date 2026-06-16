from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.pricing.services.exchange_rates import convert_to_eur, get_eur_rate, get_eur_rates


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    },
    EXCHANGERATESAPI_API_KEY="test-key",
    EXCHANGERATESAPI_API_URL="https://api.exchangeratesapi.io/v1",
)
class ExchangeRatesServiceTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_eur_to_eur_is_identity(self):
        self.assertEqual(get_eur_rate("EUR"), Decimal("1"))
        self.assertEqual(convert_to_eur(Decimal("100"), "EUR"), Decimal("100"))

    @patch("apps.pricing.services.exchange_rates.requests.get")
    def test_get_eur_rate_parses_latest_response(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "success": True,
            "base": "EUR",
            "rates": {"USD": "1.161251"},
        }

        rate = get_eur_rate("USD")

        self.assertEqual(rate, Decimal("1.161251"))
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        self.assertTrue(called_url.endswith("/latest"))

    @patch("apps.pricing.services.exchange_rates.requests.get")
    def test_get_eur_rate_caches_result(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "success": True,
            "rates": {"USD": "1.16"},
        }

        first = get_eur_rate("USD")
        second = get_eur_rate("USD")

        self.assertEqual(first, second)
        mock_get.assert_called_once()

    @patch("apps.pricing.services.exchange_rates.requests.get")
    def test_convert_to_eur_divides_by_rate(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "success": True,
            "rates": {"USD": "2"},
        }

        eur_amount = convert_to_eur(Decimal("200"), "USD")

        self.assertEqual(eur_amount, Decimal("100"))

    @patch("apps.pricing.services.exchange_rates.requests.get")
    def test_failed_api_response_returns_none(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "success": False,
            "error": {"code": 101, "info": "invalid access key"},
        }

        self.assertIsNone(get_eur_rate("USD"))

    def test_missing_api_key_returns_none(self):
        with override_settings(EXCHANGERATESAPI_API_KEY=""):
            self.assertIsNone(get_eur_rate("USD"))

    @patch("apps.pricing.services.exchange_rates.requests.get")
    def test_request_exception_returns_none(self, mock_get):
        import requests

        mock_get.side_effect = requests.RequestException("boom")

        self.assertIsNone(get_eur_rate("GBP"))

    @patch("apps.pricing.services.exchange_rates.requests.get")
    def test_historical_rate_uses_date_path(self, mock_get):
        from datetime import date

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "success": True,
            "rates": {"USD": "1.1"},
        }

        get_eur_rate("USD", on_date=date(2026, 1, 1))

        called_url = mock_get.call_args[0][0]
        self.assertTrue(called_url.endswith("/2026-01-01"))

    @patch("apps.pricing.services.exchange_rates.requests.get")
    def test_get_eur_rates_batches_multiple_currencies_in_one_call(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "success": True,
            "rates": {"USD": "1.16", "GBP": "0.86"},
        }

        rates = get_eur_rates(["USD", "GBP", "EUR"])

        self.assertEqual(rates["USD"], Decimal("1.16"))
        self.assertEqual(rates["GBP"], Decimal("0.86"))
        self.assertEqual(rates["EUR"], Decimal("1"))
        mock_get.assert_called_once()
        called_params = mock_get.call_args.kwargs["params"]
        self.assertEqual(called_params["symbols"], "GBP,USD")

    @patch("apps.pricing.services.exchange_rates.requests.get")
    def test_get_eur_rates_only_fetches_uncached_currencies(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "success": True,
            "rates": {"USD": "1.16"},
        }

        get_eur_rates(["USD"])
        mock_get.assert_called_once()

        mock_get.reset_mock()
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "success": True,
            "rates": {"GBP": "0.86"},
        }

        rates = get_eur_rates(["USD", "GBP"])

        self.assertEqual(rates["USD"], Decimal("1.16"))
        self.assertEqual(rates["GBP"], Decimal("0.86"))
        mock_get.assert_called_once()
        called_params = mock_get.call_args.kwargs["params"]
        self.assertEqual(called_params["symbols"], "GBP")
