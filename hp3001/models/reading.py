from sqlalchemy import (
    Column, DateTime, Float, Index, Integer, MetaData, String, Table,
    create_engine,
)

metadata = MetaData()

readings = Table(
    "readings",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("recorded_at", DateTime, nullable=False),
    Column("device_name", String(100), nullable=False),
    Column("channel", Integer, nullable=False),
    Column("temperature_c", Float),
    Column("humidity", Integer),
    Index("ix_readings_time", "recorded_at"),
)


def get_engine(url: str):
    engine = create_engine(url)
    metadata.create_all(engine)
    return engine


def row_to_dict(row) -> dict:
    return {
        "id": row.id,
        "recorded_at": row.recorded_at.isoformat(sep=" "),
        "device_name": row.device_name,
        "channel": row.channel,
        "temperature_c": row.temperature_c,
        "humidity": row.humidity,
    }
