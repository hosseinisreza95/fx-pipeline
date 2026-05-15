import pandas as pd

# =============================================
# FX Pipeline - Transform
# Computes YTD, daily change, and year start rate
# =============================================


def transform(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Takes raw extracted DataFrame and adds:
    - prev_day_rate: previous trading day rate
    - daily_change_pct: day-over-day percentage change
    - year_start_rate: rate on first trading day of each year
    - ytd_pct: year-to-date percentage change from first trading day of each year
    """

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    result_rows = []

    # process each currency pair separately
    for (base, quote), group in df.groupby(["base", "quote"]):

        group = group.sort_values("date").reset_index(drop=True)

        # --- prev_day_rate ---
        group["prev_day_rate"] = group["rate"].shift(1)

        # --- daily_change_pct ---
        group["daily_change_pct"] = (
            (group["rate"] - group["prev_day_rate"]) / group["prev_day_rate"] * 100
        ).round(4)

        # --- year_start_rate ---
        # for each row, find the first available rate of that row's year
        group["year"] = group["date"].dt.year
        year_start = (
            group.groupby("year")["rate"]
            .first()
            .rename("year_start_rate")
        )
        group = group.join(year_start, on="year")

        # --- ytd_pct ---
        group["ytd_pct"] = (
            (group["rate"] - group["year_start_rate"]) / group["year_start_rate"] * 100
        ).round(4)

        # drop helper column
        group = group.drop(columns=["year"])

        result_rows.append(group)

    result = pd.concat(result_rows).reset_index(drop=True)

    print(f"Transformed {len(result)} rows.")
    return result


# -----------------------------------------------
# Quick test
# -----------------------------------------------
if __name__ == "__main__":
    from extract import extract_all

    raw = extract_all("2024-01-01", "2024-12-31")
    df = transform(raw)
    print(df.head(10))
    print(df.columns.tolist())