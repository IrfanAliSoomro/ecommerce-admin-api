import datetime
from typing import Optional

def parse_date_or_none(date_str: Optional[str]) -> Optional[datetime.date]:
    """
    Parses a YYYY-MM-DD string into a datetime.date object.
    Returns None if the string is None or empty, or if parsing fails.
    """
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:

        return None 