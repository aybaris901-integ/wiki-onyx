from sqlalchemy import BigInteger, Column, Index, Integer, MetaData, String, Table, Text

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

webhook_deliveries = Table(
    "webhook_deliveries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("merchant_id", String, nullable=False),
    Column("url", String, nullable=False),
    Column("payload", Text, nullable=False),
    Column("attempts", Integer, nullable=False, default=0),
    Column("next_attempt_at", BigInteger, nullable=False),
    Column("status", String, nullable=False, default="queued"),  # queued | delivered | dead
)
Index("ix_webhook_deliveries_due", webhook_deliveries.c.status, webhook_deliveries.c.next_attempt_at)

idempotency_keys = Table(
    "idempotency_keys",
    metadata,
    Column("merchant_id", String, primary_key=True),
    Column("key", String, primary_key=True),
    Column("request_hash", String, nullable=False),
    Column("status", String, nullable=False),  # in_progress | completed
    Column("response_code", Integer),
    Column("response_body", Text),
    Column("created_at", BigInteger, nullable=False),
)

held_ach_failures = Table(
    "held_ach_failures",
    metadata,
    Column("payment_id", String, primary_key=True),
    Column("release_at", BigInteger, nullable=False),
    Column("status", String, nullable=False),  # held | applied | discarded
)
