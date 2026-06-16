from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.integrations.bybit.import_service import import_bybit_csv_for_user
from apps.integrations.bybit.parser import parse_bybit_csv
from apps.integrations.csv.detection import detect_csv_platform, validate_csv_for_platform
from apps.integrations.testing.fixtures import load_text_fixture
from apps.portfolio.models import AssetType, Transaction, TransactionType

User = get_user_model()


class BybitParserTests(TestCase):
    def test_parse_sample_fixture(self):
        content = load_text_fixture("bybit", "sample-trades.csv")
        result = parse_bybit_csv(content)
        self.assertEqual(len(result.rows), 3)
        self.assertEqual(result.rows[0].symbol, "BTC")
        self.assertEqual(result.rows[0].transaction_type, TransactionType.BUY)
        self.assertEqual(result.rows[1].transaction_type, TransactionType.SELL)

    def test_fingerprint_detects_bybit_export(self):
        content = load_text_fixture("bybit", "sample-trades.csv")
        match = validate_csv_for_platform(content, "bybit")
        self.assertGreaterEqual(match.confidence, 0.85)

    def test_parse_execqty_variant_headers(self):
        content = (
            "Symbol,Side,execQty,execPrice,fee,orderId,execTime\n"
            "ETHUSDT,Buy,1,3000,0.01,ord-1,1705312200000\n"
        )
        row = parse_bybit_csv(content).rows[0]
        self.assertEqual(row.symbol, "ETH")
        self.assertEqual(row.quantity, Decimal("1"))

    def test_parse_asset_history_format(self):
        """Test parsing Bybit asset change/transfer history."""
        content = load_text_fixture("bybit", "asset-history.csv")
        result = parse_bybit_csv(content)
        # Should have transfers and withdrawals (skip zero qty rows)
        self.assertGreater(len(result.rows), 0)
        # Check that coins are correctly mapped to symbols
        symbols = {row.symbol for row in result.rows}
        self.assertIn("USDT", symbols)
        self.assertIn("LINK", symbols)
        self.assertIn("BTC", symbols)

    def test_asset_history_transfer_in_mapping(self):
        """Test that 'Transfer in' maps to BUY."""
        content = (
            "UID,Date & Time(UTC),Coin,QTY,Type,Account Balance,Description\n"
            "123,2025-09-30 18:23:12,BTC,0.1,Transfer in,0.1,Deposit\n"
        )
        result = parse_bybit_csv(content)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].symbol, "BTC")
        self.assertEqual(result.rows[0].transaction_type, TransactionType.BUY)
        self.assertEqual(result.rows[0].quantity, Decimal("0.1"))

    def test_asset_history_withdraw_mapping(self):
        """Test that 'Withdraw' maps to SELL."""
        content = (
            "UID,Date & Time(UTC),Coin,QTY,Type,Account Balance,Description\n"
            "123,2025-09-30 19:04:50,USDC,-100,Withdraw,0,Withdrawal\n"
        )
        result = parse_bybit_csv(content)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].symbol, "USDC")
        self.assertEqual(result.rows[0].transaction_type, TransactionType.SELL)
        self.assertEqual(result.rows[0].quantity, Decimal("100"))  # abs()

    def test_parse_with_metadata_header(self):
        """Test parsing Bybit CSV with metadata header line."""
        content = (
            "UID: 507999707,Company Name: ,Country: \n"
            "UID,Date & Time(UTC),Coin,QTY,Type,Account Balance,Description\n"
            "507999707,2025-09-30 18:23:12,BTC,0.1,Transfer in,0.1,\n"
        )
        result = parse_bybit_csv(content)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].symbol, "BTC")
        self.assertEqual(result.rows[0].quantity, Decimal("0.1"))

    def test_detects_metadata_header_export_without_explicit_platform(self):
        """Real Bybit exports start with a 'UID: ...' account-info line.

        Auto-detection reads raw CSV headers before the parser runs, so it must
        also skip that metadata line — otherwise it never recognizes the file
        as Bybit at all (regression: previously detect_csv_platform found no
        match for any platform on this file).
        """
        content = (
            "UID: 507999707,Company Name: ,Country: \n"
            "Uid,Date & Time(UTC),Coin,QTY,Type,Account Balance,Description\n"
            "507999707,2025-09-30 18:23:12,USDT,0.08640857,Transfer in,0.08640857,\n"
            "507999707,2025-09-30 19:04:50,USDC,-1846.589938,Withdraw,0.00000066,Withdrawal\n"
        )
        matches = detect_csv_platform(content)
        self.assertTrue(matches, "expected Bybit to be detected from headers")
        self.assertEqual(matches[0].platform, "bybit")
        self.assertGreaterEqual(matches[0].confidence, 0.85)


class BybitImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="bybit@example.com",
            password="SecurePass123!",
            first_name="Jan",
            auth_0_id="auth0|bybit-user",
        )

    def test_import_sample_fixture(self):
        content = load_text_fixture("bybit", "sample-trades.csv")
        result = import_bybit_csv_for_user(self.user, content)
        self.assertEqual(result["transactions_imported"], 3)
        self.assertTrue(
            Transaction.objects.filter(
                portfolio__user=self.user,
                asset__asset_type=AssetType.CRYPTO,
            ).exists()
        )
