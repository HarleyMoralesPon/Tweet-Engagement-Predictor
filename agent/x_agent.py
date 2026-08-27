from __future__ import annotations
import re
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

    # Find an element containing the combined engagement metrics
    metric_elements = article.locator(
        '[aria-label*="likes"][aria-label*="views"]'
    )

    if metric_elements.count() == 0:
        return 0

    for i in range(metric_elements.count()):

        try:

            aria_label = metric_elements.nth(i).get_attribute(
                "aria-label"
            )

            if not aria_label:
                continue

            # Example:
            # "8 reposts, 9 likes, 1765 views"

            if metric_name.lower() == "like":
                match = re.search(
                    r"([\d.,]+)\s+likes?",
                    aria_label,
                    re.IGNORECASE
                )

            elif metric_name.lower() == "repost":
                match = re.search(
                    r"([\d.,]+)\s+reposts?",
                    aria_label,
                    re.IGNORECASE
                )

            elif metric_name.lower() == "view count":
                match = re.search(
                    r"([\d.,]+)\s+views?",
                    aria_label,
                    re.IGNORECASE
                )

            else:
                return 0

            if match:
                return extract_number(
                    match.group(1)
                )

        except Exception:
            continue

    return 0
# ==========================================
# Open X profile
# ==========================================

def open_user_profile(
    page,
    username: str,
) -> None:

    page.goto(
        f"{X_BASE_URL}/login",
        wait_until="domcontentloaded",
    )

    logger.info(
        "Please log into X manually."
    )

    logger.info(
        "Waiting 60 seconds for login..."
    )

    page.wait_for_timeout(
        120000
    )

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

    page.wait_for_timeout(
        4000
    )


# ==========================================
# Collect visible tweets
# ==========================================

def collect_visible_posts(
    page,
    max_tweets: int,
) -> list[dict]:

    collected_posts = []
    seen_ids = set()

    no_new_tweet_attempts = 0
    max_no_new_attempts = 5

    while len(collected_posts) < max_tweets:

        articles = page.locator("article")

        count = articles.count()

        logger.info(
            "Visible tweet articles: %d",
            count,
        )

        tweets_found_this_round = 0

        for i in range(count):

            article = articles.nth(i)

            page.wait_for_timeout(500)

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

            # ==================================
            # Skip already collected tweets
            # ==================================

            if tweet_id in seen_ids:

                continue

            seen_ids.add(tweet_id)

            tweets_found_this_round += 1

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
                "Tweet %s | likes=%d | replies=%d | reposts=%d | views=%d | bookmarks=%d",
                tweet_id,
                like_count,
                reply_count,
                repost_count,
                view_count,
                bookmark_count,
            )

            # ==================================
            # Stop when enough tweets
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
        # Check whether we found new tweets
        # ======================================

        if tweets_found_this_round == 0:

            no_new_tweet_attempts += 1

            logger.info(
                "No new tweets found. "
                "Attempt %d/%d",
                no_new_tweet_attempts,
                max_no_new_attempts,
            )

        else:

            no_new_tweet_attempts = 0

        # ======================================
        # Stop after several failed attempts
        # ======================================

        if (
            no_new_tweet_attempts
            >= max_no_new_attempts
        ):

            logger.info(
                "No new tweets after multiple "
                "scroll attempts. Stopping."
            )

            break

        # ======================================
        # Scroll page using JavaScript
        # ======================================

        page.evaluate(
            """
            () => {
                window.scrollTo(
                    0,
                    document.body.scrollHeight
                );
            }
            """
        )
        # ======================================
        # Give X time to load new tweets
        # ======================================

        page.wait_for_timeout(
            4000
        )

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