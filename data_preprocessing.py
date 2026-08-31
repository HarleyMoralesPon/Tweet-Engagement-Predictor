import pandas as pd


RAW_FILE = "data/raw/tweets.csv"
PROCESSED_FILE = "data/processed/tweets_processed.csv"


def create_processed_dataset():

    # Load raw data
    df = pd.read_csv(RAW_FILE)

    print(f"Raw dataset: {df.shape}")

    # Keep tweets with a valid view count
    df = df[df["view_count"] > 0].copy()

    # Create total engagement
    df["engagement"] = (
        df["like_count"]
        + df["repost_count"]
    )

    # Create engagement rate
    df["engagement_rate"] = (
        df["engagement"]
        / df["view_count"]
    )

    # Save processed dataset
    df.to_csv(
        PROCESSED_FILE,
        index=False
    )

    print(f"Processed dataset: {df.shape}")
    print(f"Saved to: {PROCESSED_FILE}")

    return df


if __name__ == "__main__":
    create_processed_dataset()