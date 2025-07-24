from playwright.async_api import Page
import json
import re

async def fill_information_page(page: Page, user_data: dict, log_path: str):
    log = {'inputs': [], 'dropdowns': [], 'checkboxes': []}
    # How did you hear about us
    try:
        await page.wait_for_selector('div[data-automation-id="formField-source"] div[data-automation-id="multiselectInputContainer"]', timeout=15000)
        how_did_you_hear_selector = page.locator('div[data-automation-id="formField-source"] div[data-automation-id="multiselectInputContainer"]')
        await how_did_you_hear_selector.click()
        prompt_options = await page.query_selector_all('[data-automation-id="promptLeafNode"]')
        if prompt_options:
            await prompt_options[0].click()
        log['dropdowns'].append('how_did_you_hear')
    except Exception as e:
        log['dropdowns'].append({'how_did_you_hear': 'not found or not clickable', 'error': str(e)})
    # Country
    country_button = await page.query_selector('button[aria-haspopup="listbox"][id*="country"]')
    if country_button:
        await country_button.click()
        options = await page.query_selector_all('div[visibility="opened"] li[role="option"]')
        for option in options:
            text = await option.text_content()
        for option in options:
            text = await option.text_content()
            if text and "united states of america" in text.lower():
                await option.click()
                break
        else:
            if options:
                await options[0].click()
        log['dropdowns'].append('country')
    # Phone device type
    phone_type_button = await page.query_selector('div[data-automation-id="formField-phoneType"] button[aria-haspopup="listbox"]')
    if phone_type_button:
        await phone_type_button.click()
        options = await page.query_selector_all('div[visibility="opened"] li[role="option"]')
        if options:
            await options[1].click()
        log['dropdowns'].append('phone_type')
    # Country Phone Code
    phone_device = page.locator('div[data-automation-id="formField-countryPhoneCode"] div[data-automation-id="multiselectInputContainer"]')
    await phone_device.click()
    input_elem = phone_device.locator('input[placeholder="Search"]')
    await input_elem.fill('United States')
    await input_elem.press('Enter')
    prompt_options = await page.query_selector_all('[data-automation-id="promptLeafNode"]')
    if prompt_options:
        await prompt_options[0].click()
    log['dropdowns'].append('country_phone_code')
    # Text inputs
    def get_nested(data, keys):
        for k in keys:
            if isinstance(data, dict):
                data = data.get(k)
            else:
                return ""
        return data if data is not None else ""
    label_map = {
        "given name": ["personal_information", "first_name"],
        "first name": ["personal_information", "first_name"],
        "family name": ["personal_information", "last_name"],
        "last name": ["personal_information", "last_name"],
        "address line 1": ["personal_information", "address", "street"],
        "city": ["personal_information", "address", "city"],
        "town": ["personal_information", "address", "city"],
        "postal code": ["personal_information", "address", "zipcode"],
        "zip": ["personal_information", "address", "zipcode"],
        "phone number": ["personal_information", "phone"],
        "extension": ["personal_information", "extension"],
        "country": ["personal_information", "address", "country"],
        "state": ["personal_information", "address", "state"]
    }
    inputs = await page.query_selector_all('div[data-automation-id="applyFlowMyInfoPage"] input[type="text"]')
    for input_elem in inputs:
        label_text = None
        input_id = await input_elem.get_attribute('id')
        if input_id:
            label_elem = await page.query_selector(f'label[for="{input_id}"]')
            if label_elem:
                label_text = await label_elem.text_content()
        if not label_text:
            parent_label_handle = await input_elem.evaluate_handle('el => el.closest("label")')
            parent_label = parent_label_handle.as_element() if parent_label_handle else None
            if parent_label:
                label_text = await parent_label.text_content()
        if not label_text:
            continue
        label_text_clean = re.sub(r'[^a-zA-Z0-9 ]', '', label_text).strip().lower()
        matched = False
        for key, json_path in label_map.items():
            if key in label_text_clean:
                value = get_nested(user_data, json_path)
                if value:
                    await input_elem.fill(str(value))
                    matched = True
                    log['inputs'].append({'label': label_text.strip(), 'value': value})
                    break
        if not matched:
            log['inputs'].append({'label': label_text.strip(), 'value': None})
    # Checkboxes
    no_radio = await page.query_selector('input[name="candidateIsPreviousWorker"][type="radio"][value="false"]')
    if no_radio:
        checked = await no_radio.is_checked()
        if not checked:
            await no_radio.check()
        log['checkboxes'].append('candidateIsPreviousWorker_no')
    # Save and continue
    save_and_continue_button = await page.locator('button[data-automation-id="pageFooterNextButton"]').click()
    await page.wait_for_load_state('networkidle')
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
