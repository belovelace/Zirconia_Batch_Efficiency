import uuid
from sqlalchemy import Table, Column, String, Float, Integer, DateTime, JSON, MetaData
from sqlalchemy.sql import func

metadata = MetaData()

cases = Table(
    "cases",
    metadata,
    Column("id", String, primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("disk_config", JSON),
)

files = Table(
    "files",
    metadata,
    Column("id", String, primary_key=True),
    Column("case_id", String),
    Column("filename", String),
    Column("path", String),
    Column("bbox_w", Float),
    Column("bbox_h", Float),
    Column("depth", Float),
    Column("feasible", Integer),
)

results = Table(
    "results",
    metadata,
    Column("id", String, primary_key=True),
    Column("case_id", String),
    Column("placement", JSON),
    Column("waste_rate", Float),
    Column("n_disks", Integer),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)
