from datetime import datetime, timezone
from typing import Annotated
from pydantic import AfterValidator


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


# Timestamps are stored as naive UTC; this makes the API emit them with an explicit offset
# so browsers don't interpret them as local time.
UTCDateTime = Annotated[datetime, AfterValidator(_as_utc)]
