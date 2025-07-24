from playwright.async_api import Page
import json

async def fill_education_page(page: Page, user_data: dict, log_path: str):
    log = {'education': []}
    education_entries = user_data.get('education', [])
    if not education_entries:
        with open(log_path, 'w') as f:
            json.dump(log, f, indent=2)
        return
    education_section = page.locator('div[role="group"][aria-labelledby="Education-section"]')
    education_section_add_button = education_section.locator('button[data-automation-id="add-button"]')
    await education_section_add_button.click()
    async def fill_education_form(ed_entry, panel_number):
        panel_prefix = f'div[aria-labelledby="Education-{panel_number}-panel"]'
        await page.wait_for_selector(panel_prefix, timeout=20000)
        # School Name
        school_selector = f'{panel_prefix} input[name="schoolName"]'
        if ed_entry.get('institution'):
            await page.fill(school_selector, ed_entry['institution'])
        # Degree dropdown
        degree_button = f'{panel_prefix} button[name="degree"]'
        degree = ed_entry.get('degree', '').lower()
        if degree:
            try:
                await page.click(degree_button)
                await page.wait_for_timeout(1000)
                degree_options = await page.query_selector_all('li[role="option"]')
                for option in degree_options:
                    option_text = await option.text_content()
                    if option_text and degree in option_text.lower():
                        await option.click()
                        break
            except Exception:
                pass
        # Field of Study
        field_of_study_selector = f'{panel_prefix} [data-automation-id="multiselectInputContainer"]'
        field_of_study = ed_entry.get('field_of_study') or ed_entry.get('major') or ed_entry.get('subject')
        if field_of_study:
            try:
                await page.click(field_of_study_selector)
                await page.wait_for_timeout(1000)
                field_of_study_options = await page.query_selector_all('div[data-automation-id="promptOption"]')
                for option in field_of_study_options:
                    option_text = await option.text_content()
                    if option_text and field_of_study.lower() in option_text.lower():
                        await option.click()
                        break
            except Exception:
                pass
        # Graduation date
        graduation_date = ed_entry.get('graduation_date') or ed_entry.get('end_date') or ed_entry.get('graduation_year')
        if graduation_date:
            try:
                month_map = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                }
                if isinstance(graduation_date, int):
                    year = str(graduation_date)
                    month_num = '05'
                elif ' ' in str(graduation_date):
                    month_name, year = str(graduation_date).split(maxsplit=1)
                    month_num = month_map.get(month_name[:3], '05')
                else:
                    year = str(graduation_date)
                    month_num = '05'
                grad_month_selector = f'{panel_prefix} div[data-automation-id="formField-graduationDate"] input[data-automation-id="dateSectionMonth-input"]'
                grad_year_selector = f'{panel_prefix} div[data-automation-id="formField-graduationDate"] input[data-automation-id="dateSectionYear-input"]'
                await page.fill(grad_month_selector, month_num)
                await page.fill(grad_year_selector, year)
            except Exception:
                pass
        log['education'].append({
            'panel': panel_number,
            'school': ed_entry.get('institution'),
            'degree': ed_entry.get('degree'),
            'field_of_study': field_of_study,
            'graduation_date': graduation_date
        })
    for i, ed_entry in enumerate(education_entries):
        panel_number = i + 1
        if i == 0:
            await fill_education_form(ed_entry, panel_number)
        else:
            education_section = page.locator('div[role="group"][aria-labelledby="Education-section"]')
            add_button = education_section.locator('button[data-automation-id="add-button"]')
            await add_button.wait_for(timeout=20000)
            await add_button.click()
            await page.wait_for_timeout(3000)
            await fill_education_form(ed_entry, panel_number)
        await page.wait_for_timeout(2000)
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
