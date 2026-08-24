from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from config import (
    X_BASE_URL,
    X_USERNAME,
    MAX_TWEETS,
    RAW_DATA_FILE,
)

from agent.browser import (
    start_browser,
    close_browser,
)


logger = logging.getLogger(__name__)


def open_user_profile(
    page,
    username: str,
) -> None:

    profile_url = (
        f"{X_BASE_URL}/{username}"
    )

    page.goto(
        profile_url,
        wait_until="domcontentloaded",
    )

    page.wait_for_timeout(3000)


def extract_number(
    value: str,
) -> int | None:

    import re

    match = re.search(
        r"([\d,.]+)",
        value,
    )

    if not match:
        return None

    number = (
        match.group(1)
        .replace(",", "")
        .replace(".", "")
    )

    try:
        return int(number)

    except ValueError:
        return None


def collect_visible_posts(
    page,
    max_tweets: int,
) -> list[dict]:

    collected_posts = []
    seen_ids = set()

    while len(collected_posts) < max_tweets:

        articles = page.locator("article")

        count = articles.count()

        for i in range(count):

            article = articles.nth(i)

            try:
                text = article.inner_text()

            except Exception:
                continue

            if not text:
                continue

            # --------------------------------------
            # Tweet URL / ID
            # --------------------------------------

            links = article.locator("a")

            tweet_url = None

            for j in range(links.count()):

                href = links.nth(j).get_attribute(
                    "href"
                )

                if href and "/status/" in href:

                    tweet_url = href

                    break

            if not tweet_url:
                continue

            tweet_id = (
                tweet_url
                .split("/status/")[-1]
                .split("?")[0]
            )

            if tweet_id in seen_ids:
                continue

            seen_ids.add(tweet_id)

            # --------------------------------------
            # Publication date
            # --------------------------------------

            time_element = article.locator("time")

            created_at = None

            if time_element.count() > 0:

                created_at = (
                    time_element
                    .first
                    .get_attribute("datetime")
                )

            # --------------------------------------
            # Engagement metrics
            # --------------------------------------

            like_count = 0
            reply_count = 0
            repost_count = 0
            quote_count = 0
            bookmark_count = 0

            buttons = article.locator(
                '[role="button"]'
            )

            for j in range(buttons.count()):

                button = buttons.nth(j)

                try:

                    aria_label = (
                        button
                        .get_attribute("aria-label")
                    )

                    if not aria_label:
                        continue

                    label = aria_label.lower()

                    # Replies
                    if "repl" in label:

                        value = extract_number(
                            aria_label
                        )

                        if value is not None:
                            reply_count = value

                    # Reposts
                    elif (
                        "repost" in label
                        or "retweet" in label
                    ):

                        value = extract_number(
                            aria_label
                        )

                        if value is not None:
                            repost_count = value

                    # Likes
                    elif "like" in label:

                        value = extract_number(
                            aria_label
                        )

                        if value is not None:
                            like_count = value

                    # Bookmarks
                    elif "bookmark" in label:

                        value = extract_number(
                            aria_label
                        )

                        if value is not None:
                            bookmark_count = value

                except Exception:
                    continue

            # --------------------------------------
            # Save tweet
            # --------------------------------------

            collected_posts.append(
                {
                    "tweet_id": tweet_id,

                    "text": text,

                    "tweet_url": (
                        f"{X_BASE_URL}"
                        f"{tweet_url}"
                    ),

                    "created_at": created_at,

                    "like_count": like_count,

                    "reply_count": reply_count,

                    "repost_count": repost_count,

                    "quote_count": quote_count,

                    "bookmark_count": bookmark_count,
                }
            )

            if len(collected_posts) >= max_tweets:
                break

        # --------------------------------------
        # Scroll
        # --------------------------------------

        if len(collected_posts) >= max_tweets:
            break

        previous_count = len(
            collected_posts
        )

        page.mouse.wheel(
            0,
            2500,
        )

        page.wait_for_timeout(
            2000
        )

        if (
            len(collected_posts)
            == previous_count
        ):

            logger.info(
                "No new posts detected."
            )

            break

    return collected_posts

def save_raw_data(
    posts: list[dict],
    filepath: Path,
) -> None:

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.DataFrame(posts)

    df.to_csv(
        filepath,
        index=False,
    )

    logger.info(
        "Saved %d tweets to %s",
        len(df),
        filepath,
    )


def run_agent() -> pd.DataFrame:

    logger.info(
        "Starting X browser agent."
    )

    (
        playwright,
        browser,
        context,
        page,
    ) = start_browser()

    try:

        open_user_profile(
            page,
            X_USERNAME,
        )

        posts = collect_visible_posts(
            page,
            MAX_TWEETS,
        )

        save_raw_data(
            posts,
            RAW_DATA_FILE,
        )

        return pd.DataFrame(posts)

    finally:

        context.close()

        close_browser(
            playwright,
            browser,
        )