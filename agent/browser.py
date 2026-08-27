from playwright.sync_api import sync_playwright


def start_browser():

    playwright = sync_playwright().start()

    browser = playwright.chromium.connect_over_cdp(
        "http://127.0.0.1:9222"
    )

    context = browser.contexts[0]

    if context.pages:
        page = context.pages[0]
    else:
        page = context.new_page()

    return (
        playwright,
        browser,
        context,
        page,
    )


def close_browser(
    playwright,
    browser,
):
    browser.close()
    playwright.stop()