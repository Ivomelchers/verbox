from django.test import TestCase

from apps.pricing.isin import looks_like_isin
from apps.pricing.instrument_resolver import (
    list_unmapped_isins,
    resolve_marketstack_ticker,
    resolve_yahoo_ticker,
)
from apps.pricing.models import InstrumentMapping, MappingSource
from apps.pricing.services.instrument_service import sync_seed_mappings


class InstrumentResolverTests(TestCase):
    def setUp(self):
        sync_seed_mappings()

    def test_isin_from_db(self):
        self.assertEqual(resolve_yahoo_ticker("IE00B4L5Y983"), "IWDA.AS")
        self.assertEqual(resolve_yahoo_ticker("IE00BFMXXD54"), "VUAA.AS")

    def test_unknown_isin(self):
        self.assertEqual(resolve_yahoo_ticker("XX0000000000"), "XX0000000000")

    def test_list_unmapped(self):
        InstrumentMapping.objects.filter(isin="IE00B4L5Y983").delete()
        unmapped = list_unmapped_isins(["XX0000000000", "IE00B4L5Y983"])
        self.assertIn("XX0000000000", unmapped)
        self.assertNotIn("IE00B4L5Y983", unmapped)

    def test_looks_like_isin(self):
        self.assertTrue(looks_like_isin("IE00B4L5Y983"))
        self.assertFalse(looks_like_isin("BTC"))

    def test_seed_overrides_openfigi_wrong_exchange(self):
        row = InstrumentMapping.objects.get(isin="IE00BFMXXD54")
        row.yahoo_ticker = "VUAA.L"
        row.source = MappingSource.OPENFIGI
        row.save(update_fields=["yahoo_ticker", "source", "updated_at"])
        self.assertEqual(resolve_yahoo_ticker("IE00BFMXXD54"), "VUAA.AS")

    def test_marketstack_isin_from_db_uses_mic_suffix(self):
        self.assertEqual(resolve_marketstack_ticker("IE00B4L5Y983"), "IWDA.XAMS")
        self.assertEqual(resolve_marketstack_ticker("IE00BFMXXD54"), "VUAA.XAMS")

    def test_marketstack_unknown_isin_falls_back_to_upper(self):
        self.assertEqual(resolve_marketstack_ticker("XX0000000000"), "XX0000000000")

    def test_marketstack_prefers_db_mic_field_over_yahoo_suffix(self):
        row = InstrumentMapping.objects.get(isin="IE00B4L5Y983")
        row.mic = "XLON"
        row.save(update_fields=["mic", "updated_at"])
        self.assertEqual(resolve_marketstack_ticker("IE00B4L5Y983"), "IWDA.XLON")

    def test_marketstack_alias_no_suffix_assumes_us_ticker(self):
        self.assertEqual(resolve_marketstack_ticker("AAPL"), "AAPL")

    def test_marketstack_alias_with_yahoo_suffix(self):
        self.assertEqual(resolve_marketstack_ticker("ASML"), "ASML.XAMS")
