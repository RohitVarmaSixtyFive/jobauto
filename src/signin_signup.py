def load_user_data(path='data/user_profile.json'):
    with open(path, 'r') as f:
        return json.load(f)

import json
import asyncio
from playwright.async_api import Page

async def signin_signup(page: Page, user_data: dict, log_path: str):
    log = {}
    user_choice = int(input("Enter 1 for sign in or 2 for sign up: "))
    log['user_choice'] = user_choice
    email = user_data['personal_information']['email']
    password = user_data['personal_information']['password']
    log['email'] = email
    log['password'] = '***'
    if user_choice == 2:
        # Sign Up
        email_input = await page.query_selector('input[data-automation-id="email"]')
        password_input = await page.query_selector('input[data-automation-id="password"]')
        verify_password_input = await page.query_selector('input[data-automation-id="verifyPassword"]')
        checkbox = await page.query_selector('input[data-automation-id="createAccountCheckbox"]')
        submit_btn = await page.query_selector('div[aria-label="Create Account"]')
        log['elements'] = {
            'email_input': bool(email_input),
            'password_input': bool(password_input),
            'verify_password_input': bool(verify_password_input),
            'checkbox': bool(checkbox),
            'submit_btn': bool(submit_btn)
        }
        if email_input:
            await email_input.fill(email)
        if password_input:
            await password_input.fill(password)
        if verify_password_input:
            await verify_password_input.fill(password)
        if checkbox:
            checked = await checkbox.is_checked()
            if not checked:
                await checkbox.check()
        if submit_btn:
            await submit_btn.click()
    elif user_choice == 1:
        # Sign In
        sign_in_link_selector = 'button[data-automation-id="signInLink"]'
        sign_in_link = await page.query_selector(sign_in_link_selector)
        if sign_in_link:
            await sign_in_link.click()
        email_input = await page.query_selector('input[data-automation-id="email"]')
        password_input = await page.query_selector('input[data-automation-id="password"]')
        submit_btn = await page.query_selector('div[aria-label="Sign In"]')
        log['elements'] = {
            'sign_in_link': bool(sign_in_link),
            'email_input': bool(email_input),
            'password_input': bool(password_input),
            'submit_btn': bool(submit_btn)
        }
        if email_input:
            await email_input.fill(email)
        if password_input:
            await password_input.fill(password)
        if submit_btn:
            await submit_btn.click()
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
