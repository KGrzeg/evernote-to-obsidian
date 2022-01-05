import asyncio
import os
import sys
import traceback
import shutil
from pyppeteer import launch

async def take_ss(text, output):
    try:
        browser = await launch(headless='True', executablePath=shutil.which('chromium'))
        page = await browser.newPage()
        await page.goto(f'file://{output}.html')
        await page.screenshot({"path": output, "fullPage": True})
        await browser.close()
    except Exception as e:
        traceback.print_exc()

def html_to_image(html_string, output_path):
    print("Saving " + output_path)
    with open(f'{output_path}.html', 'w') as html:
        html.write(html_string)
    asyncio.get_event_loop().run_until_complete(take_ss(html_string, output_path))
    os.remove(f'{output_path}.html')
