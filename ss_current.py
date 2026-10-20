import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()
        await page.goto("http://localhost:5000/login")
        await page.fill('input[name="email"]', "maria.santos@gmail.com")
        await page.fill('input[name="password"]', "Demo1234")
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")
        await page.goto("http://localhost:5000/jobseeker/recommendations?generate=1")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(700)
        await page.screenshot(path=r"C:\Users\user\Documents\CAPSTONE\ss_before.png", full_page=False)
        await browser.close()
        print("Done")

asyncio.run(main())
