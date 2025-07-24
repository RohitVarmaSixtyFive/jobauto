from playwright.async_api import Page
import json
import random

async def fill_voluntary_disclosures_page(page: Page, user_data: dict, log_path: str):
    log = {'listboxes': [], 'checkboxes': []}
    section = await page.query_selector('div[data-automation-id="applyFlowVoluntaryDisclosuresPage"]')
    if section:
        listboxes = await section.query_selector_all('button[aria-haspopup="listbox"]')
        for i, listbox in enumerate(listboxes, 1):
            await listbox.click()
            options = await page.query_selector_all('div[visibility="opened"] li[role="option"]')
            if options:
                random_option = random.choice(options)
                option_text = await random_option.text_content()
                await random_option.click()
                log['listboxes'].append({'listbox': i, 'selected': option_text.strip() if option_text else ''})
            await page.wait_for_timeout(3000)
        checkboxes = await section.query_selector_all('input[type="checkbox"]')
        for j, checkbox in enumerate(checkboxes, 1):
            checked = await checkbox.is_checked()
            if not checked:
                await checkbox.click()
            log['checkboxes'].append({'checkbox': j, 'checked': True})
            await page.wait_for_timeout(2000)
    save_and_continue = page.locator('button[data-automation-id="pageFooterNextButton"]')
    await save_and_continue.click()
    await page.wait_for_timeout(6000)
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
