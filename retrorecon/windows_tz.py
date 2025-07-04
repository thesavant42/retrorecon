"""Mapping between Windows and IANA timezone names."""

# Subset of mappings from CLDR windowsZones
WINDOWS_TO_IANA = {
    "Dateline Standard Time": "Etc/GMT+12",
    "UTC-11": "Etc/GMT+11",
    "Hawaiian Standard Time": "Pacific/Honolulu",
    "Alaskan Standard Time": "America/Anchorage",
    "Pacific Standard Time": "America/Los_Angeles",
    "Mountain Standard Time": "America/Denver",
    "Central Standard Time": "America/Chicago",
    "Eastern Standard Time": "America/New_York",
    "Atlantic Standard Time": "America/Halifax",
    "Greenwich Standard Time": "Etc/Greenwich",
    "GMT Standard Time": "Europe/London",
    "Central Europe Standard Time": "Europe/Budapest",
    "Romance Standard Time": "Europe/Paris",
    "W. Europe Standard Time": "Europe/Berlin",
    "E. Europe Standard Time": "Europe/Bucharest",
    "Russian Standard Time": "Europe/Moscow",
    "China Standard Time": "Asia/Shanghai",
    "Tokyo Standard Time": "Asia/Tokyo",
    "Korea Standard Time": "Asia/Seoul",
    "India Standard Time": "Asia/Kolkata",
}


def to_iana(tz_name: str) -> str | None:
    """Return the IANA zone for a Windows time zone name, if known."""
    return WINDOWS_TO_IANA.get(tz_name)
