import requests
import pandas as pd
from datetime import date

# =============================================
# FX Pipeline - Extract
# Fetches FX rates from frankfurter.app API
# =============================================

CURRENCIES = ['EUR', 'NOK', 'SEK', 'PLN', 'RON', 'DKK', 'CZK']
BASE_URL = "https://api.frankfurter.app"


def fetch_rates(base: str, start_date: str, end_date: str) -> dict:
    """
    Fetch historical FX rates for a base currency against all others.
    Returns raw JSON response from the API.
    """
    targets = ",".join([c for c in CURRENCIES if c != base])
    url = f"{BASE_URL}/{start_date}..{end_date}?from={base}&to={targets}"

    response = requests.get(url)
    response.raise_for_status()  # raises error if API call fails

    return response.json()


def extract_all(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch rates for all base currencies and return a flat DataFrame.
    Each row = one pair, one date, one rate.
    """
    all_rows = []

    for base in CURRENCIES:
        print(f"Fetching {base}...")
        data = fetch_rates(base, start_date, end_date)

        # data["rates"] = { "2024-01-02": { "NOK": 11.35, "SEK": 11.2, ... }, ... }
        for date_str, rates in data["rates"].items():
            for quote, rate in rates.items():
                all_rows.append({
                    "date": date_str,
                    "base": base,
                    "quote": quote,
                    "rate": rate
                })

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["base", "quote", "date"]).reset_index(drop=True)

    print(f"\nExtracted {len(df)} rows total.")
    return df


# -----------------------------------------------
# Quick test
# -----------------------------------------------
if __name__ == "__main__":
    df = extract_all("2024-01-01", "2024-12-31")
    print(df.head(10))
    print(df.shape)