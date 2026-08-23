from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from config import HEADLESS, SLOW_MO


def start_browser() -> tuple[
    Playwright,
    Browser,
    BrowserContext,
    Page,
]:

    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=HEADLESS,
        slow_mo=SLOW_MO,
    )

    context = browser.new_context(
        viewport={
            "width": 1440,
            "height": 900,
        }
    )

    page = context.new_page()

    return (
        playwright,
        browser,
        context,
        page,
    )


def close_browser(
    playwright: Playwright,
    browser: Browser,
) -> None:

    browser.close()

    playwright.stop()