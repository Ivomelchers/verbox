"""Bybit export — kolomschema (trade history + asset transfers)."""

from apps.integrations.csv.column_schema import ColumnField, PlatformColumnSchema

BYBIT_SCHEMA = PlatformColumnSchema(
    platform="bybit",
    schema_version="bybit-v1",
    fields=(
        ColumnField(
            "symbol",
            "Symbol",
            frozenset({
                "symbol", "pair", "market", "trading pair", "coin",
            }),
            required=True,
            fingerprint=True,
        ),
        ColumnField(
            "side",
            "Side",
            frozenset({
                "side", "direction", "type", "order side",
            }),
            required=True,
            fingerprint=True,
        ),
        ColumnField(
            "quantity",
            "Filled Qty",
            frozenset({
                "filled qty", "filled quantity", "execqty", "exec qty",
                "quantity", "qty", "filled",
            }),
            required=True,
            fingerprint=True,
        ),
        ColumnField(
            "price",
            "Avg. Filled Price",
            frozenset({
                "avg. filled price", "avg filled price", "execprice", "exec price",
                "price", "avg price", "filled price",
            }),
            required=False,  # Optional for transfer history
            fingerprint=False,  # Don't require for fingerprint
        ),
        ColumnField(
            "fee",
            "Trading Fees",
            frozenset({
                "trading fees", "fee", "fees", "trading fee", "commission",
            }),
            fingerprint=False,  # Don't require for fingerprint
        ),
        ColumnField(
            "order_id",
            "Order No.",
            frozenset({
                "order no.", "order no", "orderid", "order id", "order number",
            }),
            fingerprint=False,
            required=False,
        ),
        ColumnField(
            "executed_at",
            "Transaction Time",
            frozenset({
                "transaction time", "exectime", "exec time", "time",
                "timestamp", "trade time", "date & time(utc)",
            }),
            required=True,
            fingerprint=True,
        ),
    ),
)
