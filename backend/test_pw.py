import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    print("Testing playwright...")
    try:
        async with async_playwright() as p:
            executable_path = None
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(edge_path):
                executable_path = edge_path
            elif os.path.exists(chrome_path):
                executable_path = chrome_path
                
            browser_kwargs = {"headless": True}
            if executable_path:
                browser_kwargs["executable_path"] = executable_path
                print(f"Using executable: {executable_path}")
                
            browser = await p.chromium.launch(**browser_kwargs)
            page = await browser.new_page(viewport={"width": 1080, "height": 1080})
            await page.set_content("<h1>Hello World</h1>", wait_until="networkidle")
            await page.screenshot(path="test.jpg", type="jpeg")
            await browser.close()
            print("Playwright ran successfully!")
    except Exception as e:
        print(f"Playwright error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
