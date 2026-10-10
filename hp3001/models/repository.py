import datetime as dt
from typing import Iterable, List, Optional

from sqlalchemy import and_, func, insert, select

from .reading import readings as r


class ReadingRepository:
    def __init__(self, engine):
        self.engine = engine

    def save(self, device_name: str, samples: Iterable, when: Optional[dt.datetime] = None) -> int:
        when = when or dt.datetime.now().replace(microsecond=0)
        rows = [
            dict(recorded_at=when, device_name=device_name, channel=s.channel,
                 temperature_c=s.temperature_c, humidity=s.humidity)
            for s in samples
        ]
        if rows:
            with self.engine.begin() as conn:
                conn.execute(insert(r), rows)
        return len(rows)

    @staticmethod
    def _filters(stmt, start, end, channel):
        if start:
            stmt = stmt.where(r.c.recorded_at >= start)
        if end:
            stmt = stmt.where(r.c.recorded_at < end)
        if channel:
            stmt = stmt.where(r.c.channel == channel)
        return stmt

    def query(self, start=None, end=None, channel=None, limit=None, offset=0,
              newest_first=False) -> List:
        order = (r.c.recorded_at.desc(), r.c.channel) if newest_first else (r.c.recorded_at, r.c.channel)
        stmt = self._filters(select(r), start, end, channel).order_by(*order)
        if limit:
            stmt = stmt.limit(limit).offset(offset)
        with self.engine.connect() as conn:
            return conn.execute(stmt).fetchall()

    def count(self, start=None, end=None, channel=None) -> int:
        stmt = self._filters(select(func.count()).select_from(r), start, end, channel)
        with self.engine.connect() as conn:
            return conn.execute(stmt).scalar_one()

    def latest_per_channel(self) -> List:
        last = select(r.c.channel, func.max(r.c.recorded_at).label("m")).group_by(r.c.channel).subquery()
        stmt = (select(r)
                .join(last, and_(r.c.channel == last.c.channel, r.c.recorded_at == last.c.m))
                .order_by(r.c.channel))
        with self.engine.connect() as conn:
            return conn.execute(stmt).fetchall()

    def stats_since(self, since: dt.datetime) -> dict:
        stmt = (select(r.c.channel,
                       func.min(r.c.temperature_c), func.max(r.c.temperature_c),
                       func.avg(r.c.temperature_c),
                       func.min(r.c.humidity), func.max(r.c.humidity),
                       func.avg(r.c.humidity))
                .where(r.c.recorded_at >= since).group_by(r.c.channel))
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        return {
            row[0]: dict(temp_min=row[1], temp_max=row[2], temp_avg=row[3],
                         hum_min=row[4], hum_max=row[5], hum_avg=row[6])
            for row in rows
        }

    def channels(self) -> List[int]:
        with self.engine.connect() as conn:
            return [x[0] for x in conn.execute(select(r.c.channel).distinct().order_by(r.c.channel))]
