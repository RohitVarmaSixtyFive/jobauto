from playwright.async_api import Page
import json

async def upload_resume(page: Page, user_data: dict, log_path: str):
    log = {}
    file_input = page.locator('input[data-automation-id="file-upload-input-ref"]')
    resume_path = '/Users/mjolnir/Downloads/Lin Mei_Experiened Level Software.pdf'
    await file_input.set_input_files(resume_path)
    log['resume_uploaded'] = resume_path
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
