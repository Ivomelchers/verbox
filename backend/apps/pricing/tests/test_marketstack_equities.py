from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.pricing.exceptions import PriceFetchError
from apps.pricing.providers.marketstack_equities import MarketstackEquitiesProvider


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    },
    MARKETSTACK_API_KEY="test-key",
    MARKETSTACK_API_URL="https://api.marketstack.com/v2",
    EXCHANGERATESAPI_API_KEY="fx-test-key",
    EXCHANGERATESAPI_API_URL="https://api.exchangeratesapi.io/v1",
)
class MarketstackEquitiesProviderTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.pricing.providers.marketstack_equities.requests.get")
    def test_eur_quote_returned_without_conversion(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "data": [
                {
                    "symbol": "ASML.XAMS",
                    "close": 1622.2,
                    "price_currency": "EUR",
                }
            ]
        }

        quotes = MarketstackEquitiesProvider().fetch_live_prices(["ASML"])

        self.assertEqual(quotes["ASML"].price_eur, Decimal("1622.2"))
        self.assertEqual(quotes["ASML"].source, "marketstack")

    @patch("apps.pricing.providers.marketstack_equities.requests.get")
    def test_picks_most_recent_bar_in_date_range(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "data": [
                {"symbol": "ASML.XAMS", "date": "2026-06-12T00:00:00+0000", "close": 1863.55, "price_currency": "EUR"},
                {"symbol": "ASML.XAMS", "date": "2026-06-15T00:00:00+0000", "close": 1622.2, "price_currency": "EUR"},
                {"symbol": "ASML.XAMS", "date": "2026-06-10T00:00:00+0000", "close": None, "price_currency": "EUR"},
            ]
        }

        quotes = MarketstackEquitiesProvider().fetch_live_prices(["ASML"])

        self.assertEqual(quotes["ASML"].price_eur, Decimal("1622.2"))
        called_url = mock_get.call_args[0][0]
        self.assertTrue(called_url.endswith("/eod"))

    @patch("requests.get")
    def test_usd_quote_converted_to_eur(self, mock_get):
        def fake_get(url, params=None, timeout=None):
            response = MagicMock()
            response.raise_for_status = MagicMock()
            if "marketstack" in url:
                response.json.return_value = {
                    "data": [
                        {
                            "symbol": "AAPL",
                            "close": 232.5,
                            "price_currency": "USD",
                        }
                    ]
                }
            else:
                response.json.return_value = {"success": True, "rates": {"USD": "2"}}
            return response

        mock_get.side_effect = fake_get

        quotes = MarketstackEquitiesProvider().fetch_live_prices(["AAPL"])

        self.assertEqual(quotes["AAPL"].price_eur, Decimal("116.25"))

    def test_missing_api_key_raises_price_fetch_error(self):
        with override_settings(MARKETSTACK_API_KEY=""):
            with self.assertRaises(PriceFetchError):
                MarketstackEquitiesProvider().fetch_live_prices(["AAPL"])

    @patch("apps.pricing.providers.marketstack_equities.requests.get")
    def test_falls_back_to_adj_close_when_close_is_null(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "data": [
                {
                    "symbol": "AAPL",
                    "close": None,
                    "adj_close": 300,
                    "price_currency": "USD",
                }
            ]
        }

        with patch(
            "apps.pricing.services.exchange_rates.get_eur_rates",
            return_value={"USD": Decimal("2")},
        ):
            quotes = MarketstackEquitiesProvider().fetch_live_prices(["AAPL"])

        self.assertEqual(quotes["AAPL"].price_eur, Decimal("150"))

    @patch("apps.pricing.providers.marketstack_equities.requests.get")
    def test_marketstack_error_payload_raises(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "error": {"code": "invalid_access_key", "message": "Invalid key"}
        }

        with self.assertRaises(PriceFetchError):
            MarketstackEquitiesProvider().fetch_live_prices(["AAPL"])

    def test_empty_symbols_returns_empty_dict(self):
        self.assertEqual(MarketstackEquitiesProvider().fetch_live_prices([]), {})
