from datetime import datetime
from typing import Optional, Tuple
import re


def parse_fuzzy_date(date_str: str) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Parse a fuzzy date string into a datetime object.

    Args:
        date_str: String to parse

    Returns:
        Tuple of (parsed_datetime, error_message)
        If parsing succeeds, error_message is None
        If parsing fails, parsed_datetime is None and error_message contains the issue
    """
    if not date_str or not date_str.strip():
        return None, None

    date_str = date_str.strip()

    # Try different date formats in order of preference
    formats = [
        # Full dates
        "%Y-%m-%d",  # 2023-12-25
        "%d/%m/%Y",  # 25/12/2023
        "%m/%d/%Y",  # 12/25/2023
        "%Y/%m/%d",  # 2023/12/25
        "%B %d, %Y",  # December 25, 2023
        "%b %d, %Y",  # Dec 25, 2023
        "%d %B %Y",  # 25 December 2023
        "%d %b %Y",  # 25 Dec 2023
        # Month year formats
        "%Y %B",  # 2023 December
        "%B %Y",  # December 2023
        "%Y %b",  # 2023 Dec
        "%b %Y",  # Dec 2023
        "%m/%Y",  # 12/2023
        "%Y/%m",  # 2023/12
        # Year only
        "%Y",  # 2023
        # Month day formats (assume current year)
        "%d %B",  # 25 December
        "%B %d",  # December 25
        "%d %b",  # 25 Dec
        "%b %d",  # Dec 25
        "%d/%m",  # 25/12
        "%m/%d",  # 12/25
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # For month/day formats without year, use current year
            if "%Y" not in fmt:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed, None
        except ValueError:
            continue

    # Try to extract year from string and validate it
    year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
    if year_match:
        year = int(year_match.group())
        if 1900 <= year <= datetime.now().year + 10:  # Reasonable year range
            try:
                return datetime(year, 1, 1), None
            except ValueError:
                pass

    # If all parsing attempts fail, return error
    return (
        None,
        f"Unable to parse date: '{date_str}'. Try formats like: 2023, Dec 2023, 25/12/2023, 2023-12-25",
    )


def format_datetime_friendly(dt: datetime) -> str:
    """
    Format a datetime object in a user-friendly way.

    Args:
        dt: DateTime object to format

    Returns:
        User-friendly string representation
    """
    if dt.month == 1 and dt.day == 1:
        # If just January 1st, assume it's year-only
        return dt.strftime("%Y")
    elif dt.day == 1:
        # First of month, show month and year
        return dt.strftime("%B %Y")
    else:
        # Full date
        return dt.strftime("%B %d, %Y")


def is_valid_year(year: int) -> bool:
    """Check if a year is within reasonable bounds."""
    return 1800 <= year <= datetime.now().year + 10
