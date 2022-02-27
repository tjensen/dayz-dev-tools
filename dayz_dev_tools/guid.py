import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "steamid64", type=int, help="A 64-bit SteamID to convert to a DayZ GUID")
    args = parser.parse_args()

    print(f"DayZ GUID: {guid_for_steamid64(args.steamid64)}")


if __name__ == "__main__":
    main()
