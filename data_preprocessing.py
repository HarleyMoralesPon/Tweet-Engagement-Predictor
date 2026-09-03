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
    return text.count("<URL>")


# ==========================================
# Extract author's actual tweet text
# ==========================================

def extract_tweet_text(text):
    lines = text.split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    # ==========================================
    # 1. Find tweet date
    # ==========================================

    date_index = None

    for i, line in enumerate(lines):
        if re.match(
            r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
            r"\d{1,2}, \d{4}$",
            line
        ):
            date_index = i
            break

    if date_index is None:
        return text.strip()

    # ==========================================
    # 2. Everything after the date
    # ==========================================

    tweet_lines = lines[date_index + 1:]

    # ==========================================
    # 3. Remove UI elements
    # ==========================================

    clean_lines = []

    for line in tweet_lines:

        if line == "Quote":
            break

        if line == "Show more":
            break

        clean_lines.append(line)

    # ==========================================
    # 4. Reconstruct text
    # ==========================================

    tweet_text = " ".join(clean_lines)

    # ==========================================
    # 5. Detect fragmented URLs
    # ==========================================

    tweet_text = re.sub(
        r"https?://\s+",
        "http://",
        tweet_text
    )

    # ==========================================
    # 6. Replace complete URLs
    # ==========================================

    tweet_text = re.sub(
        r"https?://\S+",
        "<URL>",
        tweet_text
    )

    # ==========================================
    # 7. Remove trailing metrics
    # ==========================================

    tweet_text = re.sub(
        r"\s+\d[\d.,]*\s+\d[\d.,]*\s+[\d.,]+[KMB]?\s*$",
        "",
        tweet_text
    )

    # ==========================================
    # 8. Remove remaining URL fragments
    # ==========================================

    tweet_text = re.sub(
        r"\b[\w.-]+\.(?:com|net|org|ni|tv|co)\S*",
        "<URL>",
        tweet_text
    )

    # ==========================================
    # 9. Clean whitespace
    # ==========================================

    tweet_text = re.sub(r"\s+", " ", tweet_text)

    return tweet_text.strip()

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

    df = df[
        df["view_count"] > 0
    ].copy()

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

    df["day_of_week"] = (
        df["created_at"].dt.dayofweek
    )

    # ==========================================
    # Extract author's actual tweet text
    # ==========================================

    df["tweet_text"] = df["text"].apply(
        extract_tweet_text
    )

    # ==========================================
    # Text structural features
    # ==========================================

    df["char_count"] = df["tweet_text"].apply(
        count_characters
    )

    df["word_count"] = df["tweet_text"].apply(
        count_words
    )

    df["hashtag_count"] = df["tweet_text"].apply(
        count_hashtags
    )

    df["mention_count"] = df["tweet_text"].apply(
        count_mentions
    )

    df["url_count"] = df["tweet_text"].apply(
        count_urls
    )

    # ==========================================
    # Save processed dataset
    # ==========================================

    df.to_csv(
        PROCESSED_FILE,
        index=False
    )

    print(
        f"Processed dataset: {df.shape}"
    )

    print(
        f"Saved to: {PROCESSED_FILE}"
    )

    return df


# ==========================================
# Test extraction
# ==========================================

if __name__ == "__main__":

    df = pd.read_csv(RAW_FILE)

    for index in [0, 10, 50, 100]:

        print("\n" + "=" * 80)
        print(f"TWEET {index}")
        print("=" * 80)

        print("\nRAW:")
        print(df.loc[index, "text"])

        print("\nEXTRACTED:")
        print(
            extract_tweet_text(
                df.loc[index, "text"]
            )
        )