from __future__ import annotations

import logging
import re
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


# ==========================================
# Logging
# ==========================================

logger = logging.getLogger(__name__)


# ==========================================
# Extract number from aria-label
# ==========================================

def extract_number(
    value: str | None,
) -> int:

    if not value:
        return 0

    value = value.lower().strip()

    # --------------------------------------
    # Handle K / M / B notation
    # --------------------------------------

    match = re.search(
        r"([\d,.]+)\s*([kmb])?",
        value,
    )

    if not match:
        return 0

    number = match.group(1)

    suffix = match.group(2)

    number = number.replace(",", "")

    try:
        number = float(number)

    except ValueError:
        return 0

    if suffix == "k":
        number *= 1_000

    elif suffix == "m":
        number *= 1_000_000

    elif suffix == "b":
        number *= 1_000_000_000

    return int(number)


# ==========================================
# Extract metric from tweet
# ==========================================

def get_metric(
    article,
    metric_name: str,
) -> int:

    element = article.locator(
        f'[aria-label="{metric_name}"]'
    )

    if element.count() == 0:
        return 0

    parent = element.locator("..")

    buttons = parent.locator("button")

    # The first button is the icon.
    # The second button contains the number.

    if buttons.count() < 2:
        return 0

    try:

        value_text = buttons.nth(1).inner_text()

    except Exception:

        return 0

    return extract_number(
        value_text
    )

# ==========================================
# Open X profile
# ==========================================

def open_user_profile(
    page,
    username: str,
) -> None:

    profile_url = (
        f"{X_BASE_URL}/{username}"
    )

    logger.info(
        "Opening profile: %s",
        profile_url,
    )

    page.goto(
        profile_url,
        wait_until="domcontentloaded",
    )

    page.wait_for_timeout(4000)


# ==========================================
# Collect visible tweets
# ==========================================

def collect_visible_posts(
    page,
    max_tweets: int,
) -> list[dict]:

    collected_posts = []

    seen_ids = set()

    while len(collected_posts) < max_tweets:

        articles = page.locator(
            "article"
        )

        count = articles.count()

        logger.info(
            "Visible tweet articles: %d",
            count,
        )

        for i in range(count):

            article = articles.nth(i)


            # ==================================
            # Tweet text
            # ==================================

            try:

                text = article.inner_text()

            except Exception:

                continue

            if not text:
                continue

            # ==================================
            # Tweet URL
            # ==================================

            links = article.locator("a")

            tweet_url = None

            for j in range(
                links.count()
            ):

                href = (
                    links
                    .nth(j)
                    .get_attribute("href")
                )

                if (
                    href
                    and "/status/" in href
                ):

                    tweet_url = href

                    break

            if not tweet_url:
                continue

            # ==================================
            # Tweet ID
            # ==================================

            tweet_id = (
                tweet_url
                .split("/status/")[-1]
                .split("?")[0]
            )

            if tweet_id in seen_ids:
                continue

            seen_ids.add(tweet_id)

            # ==================================
            # Publication date
            # ==================================

            time_element = article.locator(
                "time"
            )

            created_at = None

            if time_element.count() > 0:

                created_at = (
                    time_element
                    .first
                    .get_attribute(
                        "datetime"
                    )
                )

            # ==================================
            # Engagement metrics
            # ==================================

            reply_count = get_metric(
                article,
                "Reply",
            )

            repost_count = get_metric(
                article,
                "Repost",
            )

            like_count = get_metric(
                article,
                "Like",
            )

            view_count = get_metric(
                article,
                "View count",
            )

            bookmark_count = get_metric(
                article,
                "Bookmark",
            )

            # ==================================
            # Create tweet record
            # ==================================

            post = {

                "tweet_id":
                    tweet_id,

                "text":
                    text,

                "tweet_url":
                    f"{X_BASE_URL}{tweet_url}",

                "created_at":
                    created_at,

                "like_count":
                    like_count,

                "reply_count":
                    reply_count,

                "repost_count":
                    repost_count,

                "quote_count":
                    0,

                "bookmark_count":
                    bookmark_count,

                "view_count":
                    view_count,
            }

            collected_posts.append(
                post
            )

            logger.info(
                "Tweet %s | likes=%d | replies=%d | reposts=%d | bookmarks=%d",
                tweet_id,
                like_count,
                reply_count,
                repost_count,
                bookmark_count,
            )

            # ==================================
            # Stop when enough tweets collected
            # ==================================

            if (
                len(collected_posts)
                >= max_tweets
            ):

                break

        # ======================================
        # Stop if enough tweets
        # ======================================

        if (
            len(collected_posts)
            >= max_tweets
        ):

            break

        # ======================================
        # Scroll down
        # ======================================

        previous_count = len(
            collected_posts
        )

        page.mouse.wheel(
            0,
            2500,
        )

        page.wait_for_timeout(
            2500
        )

        # ======================================
        # No new tweets
        # ======================================

        if (
            len(collected_posts)
            == previous_count
        ):

            logger.info(
                "No new posts detected."
            )

            break

    return collected_posts

# ==========================================
# Save raw dataset
# ==========================================

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


# ==========================================
# Complete agent
# ==========================================

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