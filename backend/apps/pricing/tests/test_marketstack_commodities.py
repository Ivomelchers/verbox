"""
Tests voor MarketstackCommodityProvider.

LET OP: gebaseerd op het Swagger-schema uit de Marketstack-docs (CommodityResponse),
niet op een echte response — het gratis plan geeft `function_access_restricted` voor
deze endpoint (bevestigd 16 jun 2026, live getest). Pas deze tests + de provider aan
zodra een betaald plan de werkelijke response-vorm onthult.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.pricing.exceptions import PriceFetchError
from apps.pricing.providers.marketstack_commodities import MarketstackCommodityProvider


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
class MarketstackCommodityProviderTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.pricing.providers.marketstack_commodities.requests.get")
    def test_gold_symbol_mapped_to_xau_and_converted_to_eur(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "data": [
                {"symbol": "XAU", "price": 2400, "currency": "USD"},
            ]
        }

        with patch(
            "apps.pricing.services.exchange_rates.get_eur_rates",
            return_value={"USD": Decimal("2")},
        ):
            quotes = MarketstackCommodityProvider().fetch_live_prices(["GOLD"])

        self.assertEqual(quotes["GOLD"].price_eur, Decimal("1200"))
        self.assertEqual(quotes["GOLD"].source, "marketstack")
        called_params = mock_get.call_args.kwargs["params"]
        self.assertEqual(called_params["symbols"], "XAU")

    @patch("apps.pricing.providers.marketstack_commodities.requests.get")
    def test_eur_denominated_commodity_skips_fx_call(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "data": [
                {"symbol": "XAG", "price": 30, "currency": "EUR"},
            ]
        }

        quotes = MarketstackCommodityProvider().fetch_live_prices(["SILVER"])

        self.assertEqual(quotes["SILVER"].price_eur, Decimal("30"))

    def test_access_restricted_on_free_plan_raises_price_fetch_error(self):
        with patch(
            "apps.pricing.providers.marketstack_commodities.requests.get"
        ) as mock_get:
            mock_get.return_value.raise_for_status = MagicMock()
            mock_get.return_value.json.return_value = {
                "error": {
                    "code": "function_access_restricted",
                    "message": "Your current subscription plan does not support this API function",
                }
            }

            with self.assertRaises(PriceFetchError):
                MarketstackCommodityProvider().fetch_live_prices(["GOLD"])

    def test_missing_api_key_raises_price_fetch_error(self):
        with override_settings(MARKETSTACK_API_KEY=""):
            with self.assertRaises(PriceFetchError):
                MarketstackCommodityProvider().fetch_live_prices(["GOLD"])

    def test_empty_symbols_returns_empty_dict(self):
        self.assertEqual(MarketstackCommodityProvider().fetch_live_prices([]), {})

    @patch("apps.pricing.providers.marketstack_commodities.requests.get")
    def test_unmapped_symbol_passed_through_unchanged(self, mock_get):
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {
            "data": [
                {"symbol": "WTI", "price": 80, "currency": "EUR"},
            ]
        }

        quotes = MarketstackCommodityProvider().fetch_live_prices(["WTI"])

        self.assertEqual(quotes["WTI"].price_eur, Decimal("80"))
