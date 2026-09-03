import pandas as pd
import re


# ==========================================
# Project paths
# ==========================================

RAW_FILE = "data/raw/tweets.csv"
PROCESSED_FILE = "data/processed/tweets_processed.csv"


# ==========================================
# Text feature functions
# ==========================================

def count_characters(text):
    return len(text)


def count_words(text):
    return len(text.split())


def count_hashtags(text):
    return len(re.findall(r"#\w+", text))


def count_mentions(text):
    return len(re.findall(r"@\w+", text))


def count_urls(text):
    return len(re.findall(r"https?://\S+", text))


# ==========================================
# Create processed dataset
# ==========================================

def create_processed_dataset():

    # ==========================================
    # Load raw data
    # ==========================================

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
    # Convert timestamp
    # ==========================================

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        utc=True
    )

    # ==========================================
    # Temporal features
    # ==========================================

    df["year"] = df["created_at"].dt.year

    df["month"] = df["created_at"].dt.month

    df["day"] = df["created_at"].dt.day

    df["hour"] = df["created_at"].dt.hour

    df["day_of_week"] = df["created_at"].dt.dayofweek

    # ==========================================
    # Text structural features
    # ==========================================

    df["char_count"] = df["text"].apply(
        count_characters
    )

    df["word_count"] = df["text"].apply(
        count_words
    )

    df["hashtag_count"] = df["text"].apply(
        count_hashtags
    )

    df["mention_count"] = df["text"].apply(
        count_mentions
    )

    df["url_count"] = df["text"].apply(
        count_urls
    )

    # ==========================================
    # Save processed dataset
    # ==========================================

    df.to_csv(
        PROCESSED_FILE,
        index=False
    )

    print(f"Processed dataset: {df.shape}")

    print(
        f"Saved to: {PROCESSED_FILE}"
    )

    return df


# ==========================================
# Run
# ==========================================

if __name__ == "__main__":
    create_processed_dataset()