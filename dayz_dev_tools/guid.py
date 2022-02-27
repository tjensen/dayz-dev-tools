import base64
import hashlib


def guid_for_steamid64(steamid64: int) -> str:
    """Convert a SteamID64 identifier to a DayZ GUID identifier.

    :Parameters:
      - `steamid64`: A 64-bit SteamID used to uniquely identify a Steam account.

    :Returns:
      The DayZ GUID corresponding to the given 64-bit SteamID.
    """
    return base64.urlsafe_b64encode(hashlib.sha256(str(steamid64).encode()).digest()).decode()
