from playwright.async_api import Page
import json

async def fill_disclosures_page(page: Page, user_data: dict, log_path: str):
    log = {'questions': []}
    label_text = "Are you legally authorized to work in the United States?"
    legend = await page.query_selector(f'legend:has-text("{label_text}")')
    if not legend:
        legend = await page.query_selector(f'label:has-text("{label_text}")')
    if legend:
        fieldset = await legend.evaluate_handle('node => node.closest("fieldset")')
        button = await fieldset.query_selector('button[aria-haspopup="listbox"]')
        if button:
            await button.click()
            yes_option = await page.query_selector('div[visibility="opened"] li[role="option"] >> text=Yes')
            if yes_option:
                await yes_option.click()
                log['questions'].append({'question': label_text, 'answer': 'Yes'})
    save_and_continue = page.locator('button[data-automation-id="pageFooterNextButton"]')
    await save_and_continue.click()
    await page.wait_for_timeout(5000)
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
