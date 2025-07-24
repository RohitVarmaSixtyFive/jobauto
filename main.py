import asyncio
import json
import os
from src.browser_utils import launch_browser
from src.signin_signup import signin_signup, load_user_data
from src.information_page import fill_information_page
from src.application_page import fill_application_page
from src.education_page import fill_education_page
from src.skills_page import fill_skills_page
from src.resume_page import upload_resume
from src.disclosures_page import fill_disclosures_page
from src.voluntary_disclosures_page import fill_voluntary_disclosures_page
from src.disability_page import fill_disability_page

LOG_DIR = 'logs/run_1'
URL = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/US%2C-CA%2C-Santa-Clara/Senior-AI-and-ML-Engineer---AI-for-Networking_JR2000376/apply/applyManually?q=ml+enginer"

async def main():
    user_data = load_user_data('data/user_profile.json')
    os.makedirs(LOG_DIR, exist_ok=True)
    browser, page = await launch_browser(URL)
    try:
        await signin_signup(page, user_data, f'{LOG_DIR}/page_1_signin_signup.json')
        await fill_information_page(page, user_data, f'{LOG_DIR}/page_2_information.json')
        await fill_application_page(page, user_data, f'{LOG_DIR}/page_3_application.json')
        await fill_education_page(page, user_data, f'{LOG_DIR}/page_4_education.json')
        await fill_skills_page(page, user_data, f'{LOG_DIR}/page_5_skills.json')
        await upload_resume(page, user_data, f'{LOG_DIR}/page_6_resume.json')
        await fill_disclosures_page(page, user_data, f'{LOG_DIR}/page_7_disclosures.json')
        await fill_voluntary_disclosures_page(page, user_data, f'{LOG_DIR}/page_8_voluntary_disclosures.json')
        await fill_disability_page(page, user_data, f'{LOG_DIR}/page_9_disability.json')
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
