import asyncio
from pyppeteer import launch

async def take_ss(text, output):
    browser = await launch()
    page = await browser.newPage()
    await page.setContent(text)
    await page.screenshot({"path": output})
    await browser.close()


def html_to_image(html_string, output_path):
    asyncio.get_event_loop().run_until_complete(take_ss(html_string, output_path))
