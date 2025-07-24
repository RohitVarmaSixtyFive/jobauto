from playwright.async_api import Page
import json

async def fill_skills_page(page: Page, user_data: dict, log_path: str):
    log = {'skills': []}
    skills_section = page.locator('div[role="group"][aria-labelledby="Skills-section"]')
    skills_input = skills_section.locator('input[placeholder="Search"]')
    await skills_input.click()
    prof_skills = user_data.get('personal_information', {}).get('professional_info', {}).get('skills', [])
    tech_skills = user_data.get('technical_skills', {})
    skills_list = list(set(prof_skills + [s for v in tech_skills.values() for s in (v if isinstance(v, list) else [])]))
    for skill in skills_list[:2]:
        await skills_input.fill(skill)
        await skills_input.press("Enter")
        skills = await page.query_selector_all('div[data-automation-id="promptLeafNode"]')
        if skills:
            await skills[0].click()
        log['skills'].append(skill)
        await page.wait_for_timeout(1500)
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
