import asyncio
from playwright.async_api import async_playwright, Browser, Page
from typing import Tuple

async def launch_browser(url: str) -> tuple[Browser, Page]:
    playwright_instance = await async_playwright().start()
    browser = await playwright_instance.chromium.launch(
        headless=False,
        slow_mo=1000,
        args=['--disable-web-security', '--disable-features=VizDisplayCompositor']
    )
    context = await browser.new_context(
        viewport={'width': 1280, 'height': 720},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = await context.new_page()
    await page.goto(url, wait_until='networkidle', timeout=30000)
    await page.wait_for_timeout(3000)
    print("Browser opened and navigated to the URL.")
    return browser, page
