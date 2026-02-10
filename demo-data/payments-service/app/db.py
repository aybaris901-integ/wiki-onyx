from sqlalchemy import BigInteger, Column, Integer, MetaData, String, Table

metadata = MetaData()

invoices = Table(
    "invoices",
    metadata,
    Column("id", String, primary_key=True),
    Column("merchant_id", String, nullable=False),
    Column("amount_cents", Integer, nullable=False),
    Column("currency", String, nullable=False),
    Column("status", String, nullable=False, default="open"),  # open | paid
)

payments = Table(
    "payments",
    metadata,
    Column("id", String, primary_key=True),  # PayRail's payment id
    Column("invoice_id", String, nullable=False),
    Column("merchant_id", String, nullable=False),
    Column("method", String, nullable=False),  # card | ach
    Column("status", String, nullable=False),  # pending | succeeded | failed
    Column("updated_at", BigInteger, nullable=False),
)

merchant_endpoints = Table(
    "merchant_endpoints",
    metadata,
    Column("merchant_id", String, primary_key=True),
    Column("url", String, nullable=False),
)

# PayRail delivers each event at least once, so we remember the ids we've processed.
payrail_events = Table(
    "payrail_events",
    metadata,
    Column("id", String, primary_key=True),
    Column("received_at", BigInteger, nullable=False),
)
