import pandas as pd


# ==========================================
# Project paths
# ==========================================

RAW_FILE = "data/raw/tweets.csv"
PROCESSED_FILE = "data/processed/tweets_processed.csv"


# ==========================================
# Create processed dataset
# ==========================================

def create_processed_dataset():

    # Load raw data
    df = pd.read_csv(RAW_FILE)

    print(f"Raw dataset: {df.shape}")

    # ==========================================
    # Remove tweets without valid views
    # ==========================================

    df = df[df["view_count"] > 0].copy()

    # ==========================================
    # Engagement
    # ==========================================

    df["engagement"] = (
        df["like_count"]
        + df["repost_count"]
    )

    # ==========================================
    # Engagement rate
    # ==========================================

    df["engagement_rate"] = (
        df["engagement"]
        / df["view_count"]
    )

    # ==========================================
    # Temporal features
    # ==========================================

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        utc=True
    )

    df["year"] = df["created_at"].dt.year

    df["month"] = df["created_at"].dt.month

    df["day"] = df["created_at"].dt.day

    df["hour"] = df["created_at"].dt.hour

    df["day_of_week"] = df["created_at"].dt.dayofweek

    # ==========================================
    # Save processed dataset
    # ==========================================

    df.to_csv(
        PROCESSED_FILE,
        index=False
    )

    print(f"Processed dataset: {df.shape}")
    print(f"Saved to: {PROCESSED_FILE}")

    return df


# ==========================================
# Run
# ==========================================

if __name__ == "__main__":
    create_processed_dataset()