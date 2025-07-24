from playwright.async_api import Page
import json

async def fill_application_page(page: Page, user_data: dict, log_path: str):
    log = {'work_experience': []}
    work_experiences = user_data.get('work_experience', [])
    if not work_experiences:
        with open(log_path, 'w') as f:
            json.dump(log, f, indent=2)
        return
    work_experience_section = page.locator('div[role="group"][aria-labelledby="Work-Experience-section"]')
    add_button = work_experience_section.locator('button[data-automation-id="add-button"]')
    await add_button.click()
    async def fill_work_experience_form(work_exp, panel_number):
        panel_prefix = f'div[aria-labelledby="Work-Experience-{panel_number}-panel"]'
        await page.wait_for_selector(panel_prefix, timeout=20000)
        job_title_selector = f'{panel_prefix} input[name="jobTitle"]'
        company_selector = f'{panel_prefix} input[name="companyName"]'
        location_selector = f'{panel_prefix} input[name="location"]'
        current_work_checkbox = f'{panel_prefix} input[name="currentlyWorkHere"]'
        duration = work_exp.get('duration', '')
        is_current = 'Present' in duration or 'Current' in duration.lower()
        if work_exp.get('position'):
            await page.fill(job_title_selector, work_exp['position'])
        if work_exp.get('company'):
            await page.fill(company_selector, work_exp['company'])
        if work_exp.get('location'):
            await page.fill(location_selector, work_exp['location'])
        if is_current:
            await page.check(current_work_checkbox)
        else:
            await page.uncheck(current_work_checkbox)

        # Handle FROM and TO dates (robust, notebook-style)
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        if duration:
            try:
                # Normalize all dashes to '-'
                norm_duration = duration.replace('\u2013', '-').replace('\u2014', '-').replace('–', '-').replace('—', '-')
                parts = norm_duration.split('-')
                # FROM date
                if len(parts) >= 1:
                    start_part = parts[0].strip()
                    start_split = start_part.split(maxsplit=1)
                    if len(start_split) == 2:
                        month_name, year = start_split
                        month_num = month_map.get(month_name[:3], '01')
                        start_month_selector = f'{panel_prefix} div[data-automation-id="formField-startDate"] input[data-automation-id="dateSectionMonth-input"]'
                        start_year_selector = f'{panel_prefix} div[data-automation-id="formField-startDate"] input[data-automation-id="dateSectionYear-input"]'
                        await page.fill(start_month_selector, month_num)
                        await page.fill(start_year_selector, year)
                    else:
                        print(f"  Could not parse start date from '{start_part}'")
                # TO date (if not current)
                if not is_current and len(parts) >= 2:
                    end_part = parts[1].strip()
                    if ' ' in end_part and end_part.lower() != 'present':
                        end_split = end_part.split(maxsplit=1)
                        if len(end_split) == 2:
                            end_month_name, end_year = end_split
                            end_month_num = month_map.get(end_month_name[:3], '12')
                            end_month_selector = f'{panel_prefix} div[data-automation-id="formField-endDate"] input[data-automation-id="dateSectionMonth-input"]'
                            end_year_selector = f'{panel_prefix} div[data-automation-id="formField-endDate"] input[data-automation-id="dateSectionYear-input"]'
                            await page.fill(end_month_selector, end_month_num)
                            await page.fill(end_year_selector, end_year)
                        else:
                            print(f"  Could not parse end date from '{end_part}'")
            except Exception as e:
                print(f"Error parsing dates from duration '{duration}': {e}")

        log['work_experience'].append({
            'panel': panel_number,
            'job_title': work_exp.get('position'),
            'company': work_exp.get('company'),
            'location': work_exp.get('location'),
            'is_current': is_current,
            'duration': duration
        })
    for i, work_exp in enumerate(work_experiences):
        panel_number = i + 1
        if i == 0:
            await fill_work_experience_form(work_exp, panel_number)
        else:
            work_experience_section = page.locator('div[role="group"][aria-labelledby="Work-Experience-section"]')
            add_button = work_experience_section.locator('button[data-automation-id="add-button"]')
            await add_button.wait_for(timeout=20000)
            await add_button.click()
            await page.wait_for_timeout(3000)
            await fill_work_experience_form(work_exp, panel_number)
        await page.wait_for_timeout(2000)
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
