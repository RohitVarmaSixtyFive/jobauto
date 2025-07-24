from playwright.async_api import Page
import json

async def fill_disability_page(page: Page, user_data: dict, log_path: str):
    log = {'checkboxes': [], 'date_fields': []}
    checkboxes = await page.query_selector_all('input[type="checkbox"]')
    for i, checkbox in enumerate(checkboxes, 1):
        required = await checkbox.get_attribute('aria-required')
        label_handle = await checkbox.evaluate_handle('el => el.closest("label")')
        label = label_handle.as_element() if label_handle else None
        label_text = await label.text_content() if label else ''
        if label_text and "do not have a disability" in label_text.lower():
            checked = await checkbox.is_checked()
            if not checked:
                await checkbox.click()
            log['checkboxes'].append({'checkbox': i, 'label': label_text.strip(), 'checked': True})
            break
    date_fields = [
        ("selfIdentifiedDisabilityData--dateSignedOn-dateSectionMonth-input", "07"),
        ("selfIdentifiedDisabilityData--dateSignedOn-dateSectionDay-input", "24"),
        ("selfIdentifiedDisabilityData--dateSignedOn-dateSectionYear-input", "2025"),
    ]
    for field_id, default_value in date_fields:
        selector = f'input[id="{field_id}"]'
        field = await page.query_selector(selector)
        if field:
            value = await field.input_value()
            if not value:
                await field.fill(default_value)
            log['date_fields'].append({'field_id': field_id, 'value': default_value})
    save_and_continue = page.locator('button[data-automation-id="pageFooterNextButton"]')
    await save_and_continue.click()
    await page.wait_for_timeout(5000)
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
