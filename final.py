"""
Job Application Automation System

A comprehensive, modular system for automating job applications on Workday-based platforms.
This system handles authentication, form filling, and various application sections including
personal information, work experience, education, skills, and voluntary disclosures.

Author: Automated Job Application System
Version: 2.0
"""

import asyncio
import json
import os
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

import openai
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from dotenv import load_dotenv


class JobApplicationBot:
    """Main class for job application automation"""
    
    def __init__(self, config_path: str = "data/user_profile.json"):
        """Initialize the job application bot
        
        Args:
            config_path: Path to user profile configuration file
        """
        load_dotenv()
        self.config_path = config_path
        self.user_data = self._load_user_profile()
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Application URLs for different companies
        self.company_urls = {
            "nvidia": "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/US%2C-CA%2C-Santa-Clara/Senior-AI-and-ML-Engineer---AI-for-Networking_JR2000376/apply/applyManually?q=ml+enginer",
            "salesforce": "https://salesforce.wd12.myworkdayjobs.com/en-US/External_Career_Site/job/Singapore---Singapore/Senior-Manager--Solution-Engineering--Philippines-_JR301876/apply/applyManually",
            "hitachi": "https://hitachi.wd1.myworkdayjobs.com/en-US/hitachi/job/Krakow%2C-Lesser-Poland%2C-Poland/Internship---NET-Developer_R0071999/apply/applyManually",
            "icf": "https://icf.wd5.myworkdayjobs.com/en-US/ICFExternal_Career_Site/job/Reston%2C-VA/Senior-Paid-Search-Manager_R2502057/apply/applyManually",
            "harris": "https://harriscomputer.wd3.myworkdayjobs.com/en-US/1/job/Florida%2C-United-States/Vice-President-of-Sales_R0030918/apply/applyManually"
        }
        
        # Logging setup
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.current_run_dir = self.logs_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_run_dir.mkdir(exist_ok=True)
        
        # Track the previous question and whether it was a listbox
        self.previous_question = None
        self.previous_was_listbox = False

    def _load_user_profile(self) -> Dict[str, Any]:
        """Load user profile data from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"User profile file not found: {self.config_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Invalid JSON in user profile file: {self.config_path}")
            return {}

    def reset_duplicate_tracking(self) -> None:
        """Reset the duplicate question tracking for new applications"""
        self.previous_question = None
        self.previous_was_listbox = False
        print("Reset duplicate question tracking")

    async def initialize_browser(self, headless: bool = False, slow_mo: int = 100) -> None:
        """Initialize browser and page"""
        playwright_instance = await async_playwright().start()
        self.browser = await playwright_instance.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        self.page = await self.context.new_page()

    async def navigate_to_job(self, company: str = "harris") -> None:
        """Navigate to job application page"""
        if company not in self.company_urls:
            raise ValueError(f"Company '{company}' not supported. Available: {list(self.company_urls.keys())}")
        
        url = self.company_urls[company]
        await self.page.goto(url, wait_until='networkidle', timeout=30000)
        print(f"Navigated to {company} job application page")

    async def handle_authentication(self, auth_type: int = 1) -> bool:
        """Handle authentication (sign in or sign up)
        
        Args:
            auth_type: 1 for sign in, 2 for sign up
        """
        if auth_type == 2:
            return await self._handle_signup()
        else:
            return await self._handle_signin()

    async def _handle_signup(self) -> bool:
        """Handle user sign up process"""
        try:
            personal_info = self.user_data.get('personal_information', {})
            email = personal_info.get('email', '')
            password = personal_info.get('password', '')

            # Fill email
            email_input = await self.page.query_selector('input[data-automation-id="email"]')
            if email_input:
                await email_input.fill(email)
                print(f"Filled email: {email}")

            # Fill password
            password_input = await self.page.query_selector('input[data-automation-id="password"]')
            if password_input:
                await password_input.fill(password)
                print("Filled password")

            # Fill verify password
            verify_password_input = await self.page.query_selector('input[data-automation-id="verifyPassword"]')
            if verify_password_input:
                await verify_password_input.fill(password)
                print("Filled verify password")

            # Check the create account checkbox
            checkbox = await self.page.query_selector('input[data-automation-id="createAccountCheckbox"]')
            if checkbox:
                checked = await checkbox.is_checked()
                if not checked:
                    await checkbox.check()
                print("Checked create account checkbox")

            # Click submit button
            await asyncio.sleep(1)
            submit_btn = await self.page.query_selector('div[aria-label="Create Account"]')
            if submit_btn:
                await submit_btn.click()
                print("Clicked create account submit button")
                return True

        except Exception as e:
            print(f"Error during signup: {e}")
            return False

    async def _handle_signin(self) -> bool:
        """Handle user sign in process"""
        try:
            # Click sign in link
            sign_in_link = await self.page.query_selector('button[data-automation-id="signInLink"]')
            if sign_in_link:
                await sign_in_link.click()
                print("Clicked sign in link")

            personal_info = self.user_data.get('personal_information', {})
            email = personal_info.get('email', '')
            password = personal_info.get('password', '')

            # Fill email
            email_input = await self.page.query_selector('input[data-automation-id="email"]')
            if email_input:
                await email_input.fill(email)
                print(f"Filled email: {email}")

            # Fill password
            password_input = await self.page.query_selector('input[data-automation-id="password"]')
            if password_input:
                await password_input.fill(password)
                print("Filled password")

            # Click submit button
            await asyncio.sleep(1)
            submit_btn = await self.page.query_selector('div[aria-label="Sign In"]')
            if submit_btn:
                await submit_btn.click()
                print("Clicked sign in submit button")
                return True

        except Exception as e:
            print(f"Error during signin: {e}")
            return False

    async def process_application_form(self) -> None:
        """Process the main application form with all sections"""
        await asyncio.sleep(12)  # Wait for page to load
        
        # Get main page container
        main_page = await self.page.query_selector('div[data-automation-id="applyFlowPage"]')
        if not main_page:
            print("Main page container not found")
            return

        # Find all sections in the application
        sections = await main_page.query_selector_all('div[role="group"][aria-labelledby]')
        print(f"Found {len(sections)} sections to process")

        for section in sections:
            aria_labelledby = await section.get_attribute('aria-labelledby')
            if not aria_labelledby:
                continue

            print(f"\n=== Processing section: {aria_labelledby} ===")
            
            # Process different section types
            if any(keyword in aria_labelledby.lower() for keyword in ["information", "personal"]):
                await self._process_personal_information_section(section)
            elif any(keyword in aria_labelledby.lower() for keyword in ["work", "experience", "history"]):
                await self._process_experience_section(section)
            elif any(keyword in aria_labelledby.lower() for keyword in ["education"]):
                await self._process_education_section(section)
            elif any(keyword in aria_labelledby.lower() for keyword in ["language"]):
                await self._process_language_section(section)
            elif any(keyword in aria_labelledby.lower() for keyword in ["skill"]):
                await self._process_skills_section(section)
            elif any(keyword in aria_labelledby.lower() for keyword in ["application", "question"]):
                await self._process_application_questions_section(section)
            elif any(keyword in aria_labelledby.lower() for keyword in ["voluntary", "disclosure"]):
                await self._process_voluntary_disclosures_section(section)
            elif any(keyword in aria_labelledby.lower() for keyword in ["resume", "document"]):
                await self._process_resume_section(section)
            elif any(keyword in aria_labelledby.lower() for keyword in ["disability"]):
                await self._process_disability_section(section)
            else:
                print(f"Unknown section type: {aria_labelledby}")
                await self._process_generic_section(section, aria_labelledby)

    async def _process_personal_information_section(self, section) -> None:
        """Process personal information section using extract-fill-repeat workflow"""
        print("Processing Personal Information section")
        
        await asyncio.sleep(5)  # Wait for page to load
        
        main_page = await self.page.query_selector('div[data-automation-id="applyFlowPage"]')
        INPUT_SELECTOR = 'button, input, select, textarea, [role="button"]'
        
        i = 0
        prev_answered_question = None
        
        while True:
            # Re-extract elements on each iteration (fresh DOM state)
            inputs = await main_page.query_selector_all(INPUT_SELECTOR)
            
            if i >= len(inputs):
                print("Reached end of inputs, exiting loop")
                break
                
            input_el = inputs[i]
            
            # Get element information
            input_id = await input_el.get_attribute('data-automation-id') or await input_el.get_attribute('aria-haspopup') or 'unknown'
            group_label, aria_labelledby = await self._get_group_label_and_aria(input_el)
            question = group_label or 'UNLABELED'
            
            input_type = await input_el.get_attribute('type') or 'unknown'
            role = await input_el.get_attribute('role')
            placeholder = await input_el.get_attribute('placeholder')
            required = await input_el.get_attribute('required')

            # Get more specific question label
            question = await self._get_nearest_label_text(input_el) or question

            if input_type == "radio":
                question = f"Choose yes or no for the question {group_label} with Radio Button Option: {question}. choose yes if the button has to be clicked otherwise choose no."
            
            # Skip duplicate questions
            if question != 'UNLABELED' and question == prev_answered_question:
                print(f"⏩ Skipping duplicate question at index {i}: '{question}'")
                i += 1
                continue
            
            # Skip navigation buttons
            if input_id in ["pageFooterBackButton", "backToJobPosting"]:
                i += 1
                continue
            
            print("--------------------------------")
            print(f"Processing element {i}: Input ID: {input_id}, Question: {question}, aria-labelledby: {aria_labelledby or 'None'}")
            
            # Handle Next button
            if input_id == "pageFooterNextButton":
                print("Clicking Next button")
                await input_el.click()
                break
            
            # Process form elements one by one
            else:
                section = await main_page.query_selector(f'div[aria-labelledby="{aria_labelledby}"]') if aria_labelledby else main_page
                
                if role == "spinbutton":
                    input_type = "spinbutton"
                
                tag_name = await input_el.evaluate("(el) => el.tagName.toLowerCase()")
                if tag_name and tag_name.lower() == 'textarea':
                    input_type = 'textarea'
                input_tag = tag_name
                
                # Skip elements with certain directions (like RTL text)
                element_dir = await input_el.get_attribute('dir')
                if element_dir and element_dir != 'ltr':
                    print(f"Skipping element {input_id} with dir={element_dir}")
                    i += 1
                    continue
                
                # Get options for relevant input types
                options = await self._get_element_options(input_el, input_tag, input_type)
                
                print(f"Processing form element: {question}")
                
                # Create element info for AI processing
                element_info = {
                    'question': question or 'UNLABELED',
                    'aria_labelledby': aria_labelledby,
                    'input_type': input_type,
                    'input_tag': input_tag,
                    'input_id': input_id,
                    'options': options,
                    'placeholder': placeholder,
                    'required': required,
                    'role': role
                }
                
                print(f"Element info: {element_info}")
                
                # Get AI response for this single element
                full_key = f"[{element_info['question']}, {element_info['input_id']}, {element_info['input_type']}, {element_info['aria_labelledby']}, {element_info['input_tag']}]"
                ai_values, _ = await self._get_ai_response_for_section_for_personal_information(self.user_data.get('personal_information', {}), [element_info])
                response = ai_values.get(full_key, 'SKIP')
                
                print(f"AI response for field '{question}': {response}")
                
                # Fill this single element
                await self._fill_single_element(
                    input_el, 
                    input_id, 
                    input_type, 
                    input_tag, 
                    response,
                    options
                )
                
                # Update tracking
                if question != 'UNLABELED':
                    prev_answered_question = question
            
            # Move to next element
            i += 1
            
            # Small delay to prevent overwhelming the page
            await asyncio.sleep(0.5)
    
    async def _process_experience_section(self, section) -> None:
        """Process work experience section with add functionality"""
        print("Processing Work Experience section")
        await self._handle_section_with_add(section, "experience")

    async def _process_education_section(self, section) -> None:
        """Process education section with add functionality"""
        print("Processing Education section")
        await self._handle_section_with_add(section, "education")

    async def _process_language_section(self, section) -> None:
        """Process language section with add functionality"""
        print("Processing Language section")
        await self._handle_section_with_add(section, "language")

    async def _process_skills_section(self, section) -> None:
        """Process skills section"""
        print("Processing Skills section")
        
        # Extract form elements from this section
        form_elements = await self._extract_form_elements_from_section(section)
        
        if not form_elements:
            print("No form elements found in skills section")
            return

        # Get skills data
        skills_data = {
            "technical_skills": self.user_data.get('technical_skills', {}),
            "skills": self.user_data.get('personal_information', {}).get('professional_info', {}).get('skills', [])
        }
        
        # Use AI to map and fill the form
        ai_response, key_mapping = await self._get_ai_response_for_section(skills_data, form_elements)
        
        # Fill the form elements
        await self._fill_form_elements(ai_response, key_mapping)

    async def _process_application_questions_section(self, section) -> None:
        """Process application questions section"""
        print("Processing Application Questions section")
        
        # Extract form elements from this section
        form_elements = await self._extract_form_elements_from_section(section)
        
        if not form_elements:
            print("No form elements found in application questions section")
            return

        # Use entire user data for application questions
        ai_response, key_mapping = await self._get_ai_response_for_section(self.user_data, form_elements)
        
        # Fill the form elements
        await self._fill_form_elements(ai_response, key_mapping)

    async def _process_voluntary_disclosures_section(self, section) -> None:
        """Process voluntary disclosures section with proper diversity information"""
        print("Processing Voluntary Disclosures section")
        
        # Look for the specific voluntary disclosures page container
        voluntary_section = await self.page.query_selector('div[data-automation-id="applyFlowVoluntaryDisclosuresPage"]')
        
        if not voluntary_section:
            # Fall back to the passed section
            voluntary_section = section
        
        log_data = {'listboxes': [], 'checkboxes': []}
        
        # Handle listboxes (dropdown selections for gender, ethnicity, veteran status)
        listboxes = await voluntary_section.query_selector_all('button[aria-haspopup="listbox"]')
        print(f"Found {len(listboxes)} listboxes in voluntary disclosures section")
        
        for i, listbox in enumerate(listboxes, 1):
            try:
                # Get the question context first
                question_context = await self._get_listbox_question_context(listbox)
                current_question = question_context.lower().strip()
                
                # Skip if this question is the same as previous AND previous was a listbox
                if (self.previous_question and 
                    current_question == self.previous_question and 
                    self.previous_was_listbox):
                    print(f"Skipping duplicate listbox question {i}: {question_context} because previous question was a listbox")
                    continue
                
                # Update tracking for next iteration (this is a listbox)
                self.previous_question = current_question
                self.previous_was_listbox = True
                
                await listbox.click()
                await asyncio.sleep(1)
                
                # Get options
                options = await self.page.query_selector_all('div[visibility="opened"] li[role="option"]')
                
                if options:
                    selected_option = await self._select_appropriate_voluntary_disclosure_option(
                        options, question_context, i
                    )
                    
                    if selected_option:
                        option_text = await selected_option.text_content()
                        await selected_option.click()
                        log_data['listboxes'].append({
                            'listbox': i, 
                            'question': question_context,
                            'selected': option_text.strip() if option_text else ''
                        })
                        print(f"Selected option for listbox {i}: {option_text.strip()}")
                
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Error processing listbox {i}: {e}")
        
        # Handle checkboxes
        checkboxes = await voluntary_section.query_selector_all('input[type="checkbox"]')
        print(f"Found {len(checkboxes)} checkboxes in voluntary disclosures section")
        
        for j, checkbox in enumerate(checkboxes, 1):
            try:
                # Get question context for checkbox (if available)
                checkbox_question = await self._get_element_question_context(checkbox)
                current_question = checkbox_question.lower().strip() if checkbox_question else ""
                
                # Skip if this question is the same as previous AND previous was a listbox
                if (self.previous_question and 
                    current_question and 
                    current_question == self.previous_question and 
                    self.previous_was_listbox):
                    print(f"Skipping duplicate checkbox question {j}: {checkbox_question} because previous question was a listbox")
                    continue
                
                # Update tracking for next iteration (this is not a listbox)
                if current_question:
                    self.previous_question = current_question
                    self.previous_was_listbox = False
                
                checked = await checkbox.is_checked()
                if not checked:
                    await checkbox.click()
                    print(f"Checked checkbox {j}")
                else:
                    print(f"Checkbox {j} already checked")
                
                log_data['checkboxes'].append({'checkbox': j, 'checked': True})
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error processing checkbox {j}: {e}")
        
        # Save log
        log_path = self.current_run_dir / "voluntary_disclosures.json"
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

    async def _select_appropriate_voluntary_disclosure_option(self, options, question_context: str, listbox_num: int):
        """Select appropriate option for voluntary disclosure questions"""
        # Convert options to text for analysis
        option_texts = []
        for option in options:
            text = await option.text_content()
            if text:
                option_texts.append(text.strip())
        
        # Define selection logic based on question context
        question_lower = question_context.lower()
        
        if any(keyword in question_lower for keyword in ["gender", "sex"]):
            # For gender questions, select "Male", "Female", or "Prefer not to disclose"
            for i, option in enumerate(options):
                text = await option.text_content()
                if text and any(gender in text.lower() for gender in ["male", "female", "prefer not"]):
                    return option
        
        elif any(keyword in question_lower for keyword in ["race", "ethnicity", "ethnic"]):
            # For ethnicity questions, select an appropriate option or "Prefer not to disclose"
            for i, option in enumerate(options):
                text = await option.text_content()
                if text and any(eth in text.lower() for eth in ["asian", "white", "prefer not", "decline"]):
                    return option
        
        elif any(keyword in question_lower for keyword in ["veteran", "military"]):
            # For veteran status, select "No" or appropriate option
            for i, option in enumerate(options):
                text = await option.text_content()
                if text and any(vet in text.lower() for vet in ["not a protected veteran", "no", "not applicable"]):
                    return option
        
        elif any(keyword in question_lower for keyword in ["disability", "disabled"]):
            # For disability questions, select "No" or "Prefer not to disclose"
            for i, option in enumerate(options):
                text = await option.text_content()
                if text and any(dis in text.lower() for dis in ["no", "do not have", "prefer not"]):
                    return option
        
        # Default: select first option or "Prefer not to disclose" if available
        for option in options:
            text = await option.text_content()
            if text and "prefer not" in text.lower():
                return option
        
        # If no "prefer not" option, select the first option
        return options[0] if options else None

    async def _get_listbox_question_context(self, listbox) -> str:
        """Get the question context for a listbox"""
        try:
            # Try to find the nearest label or legend
            question = await listbox.evaluate('''
                el => {
                    // Look for aria-labelledby
                    let labelledby = el.getAttribute('aria-labelledby');
                    if (labelledby) {
                        let labelEl = document.getElementById(labelledby);
                        if (labelEl && labelEl.textContent) return labelEl.textContent.trim();
                    }
                    
                    // Look for nearest fieldset legend
                    let fieldset = el.closest('fieldset');
                    if (fieldset) {
                        let legend = fieldset.querySelector('legend');
                        if (legend && legend.textContent) return legend.textContent.trim();
                    }
                    
                    // Look for nearest label
                    let label = el.closest('label');
                    if (label && label.textContent) return label.textContent.trim();
                    
                    // Look for aria-label
                    let ariaLabel = el.getAttribute('aria-label');
                    if (ariaLabel) return ariaLabel;
                    
                    return 'Unknown Question';
                }
            ''')
            return question or "Unknown Question"
        except:
            return "Unknown Question"

    async def _process_resume_section(self, section) -> None:
        """Process resume upload section"""
        print("Processing Resume section")
        
        # Look for file input
        file_input = await section.query_selector('input[type="file"]')
        if file_input:
            resume_path = self.user_data.get('documents', {}).get('resume_path', '')
            if resume_path and os.path.exists(resume_path):
                await file_input.set_input_files([resume_path])
                print(f"Uploaded resume: {resume_path}")
            else:
                print("Resume file not found or not specified")

    async def _process_disability_section(self, section) -> None:
        """Process disability disclosure section"""
        print("Processing Disability section")
        
        log_data = {'checkboxes': [], 'date_fields': []}
        
        # Find checkboxes
        checkboxes = await section.query_selector_all('input[type="checkbox"]')
        
        for i, checkbox in enumerate(checkboxes, 1):
            try:
                label_handle = await checkbox.evaluate_handle('el => el.closest("label")')
                label = label_handle.as_element() if label_handle else None
                label_text = await label.text_content() if label else ''
                
                # Select "do not have a disability" option
                if label_text and "do not have a disability" in label_text.lower():
                    checked = await checkbox.is_checked()
                    if not checked:
                        await checkbox.click()
                        print(f"Selected: {label_text.strip()}")
                    
                    log_data['checkboxes'].append({
                        'checkbox': i, 
                        'label': label_text.strip(), 
                        'checked': True
                    })
                    break
                    
            except Exception as e:
                print(f"Error processing disability checkbox {i}: {e}")
        
        # Fill date fields if present
        current_date = datetime.now()
        date_fields = [
            ("selfIdentifiedDisabilityData--dateSignedOn-dateSectionMonth-input", f"{current_date.month:02d}"),
            ("selfIdentifiedDisabilityData--dateSignedOn-dateSectionDay-input", f"{current_date.day:02d}"),
            ("selfIdentifiedDisabilityData--dateSignedOn-dateSectionYear-input", str(current_date.year)),
        ]
        
        for field_id, default_value in date_fields:
            selector = f'input[id="{field_id}"]'
            field = await self.page.query_selector(selector)
            if field:
                value = await field.input_value()
                if not value:
                    await field.fill(default_value)
                    log_data['date_fields'].append({'field_id': field_id, 'value': default_value})
        
        # Save log
        log_path = self.current_run_dir / "disability_disclosures.json"
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

    async def _process_generic_section(self, section, section_name: str) -> None:
        """Process any generic section using AI"""
        print(f"Processing Generic section: {section_name}")
        
        # Extract form elements from this section
        form_elements = await self._extract_form_elements_from_section(section)
        
        if not form_elements:
            print(f"No form elements found in {section_name} section")
            return

        # Use entire user data for unknown sections
        ai_response, key_mapping = await self._get_ai_response_for_section(self.user_data, form_elements)
        
        # Fill the form elements
        await self._fill_form_elements(ai_response, key_mapping)

    async def _handle_section_with_add(self, section, section_type: str) -> None:
        """Handle sections that have add functionality (experience, education, language)"""
        # Get appropriate data based on section type
        if section_type == "experience":
            items_data = self.user_data.get("work_experience", [])
        elif section_type == "education":
            items_data = self.user_data.get("education", [])
        elif section_type == "language":
            items_data = self.user_data.get("fluent_languages", [])
        else:
            items_data = []
        
        print(f"Found {len(items_data)} {section_type} entries")
        
        if not items_data:
            return
            
        # Process each item
        for i, item_data in enumerate(items_data):
            print(f"\n=== Filling {section_type} {i + 1} ===")
            
            # Click add button for each entry
            add_button = await self.page.query_selector('button[data-automation-id="add-button"]')
            if add_button:
                await add_button.click()
                await asyncio.sleep(2)
                print(f"Clicked add button for {section_type} {i + 1}")
            
            main_page = await self.page.query_selector('div[data-automation-id="applyFlowPage"]')            

            # Get all inputs from the page (not just section)
            inputs = await main_page.query_selector_all('input, button, textarea, select')
            panel_elements = []
            previous_question = None
            previous_type = None

            for input_el in inputs:
                input_id = await input_el.get_attribute('data-automation-id') or await input_el.get_attribute('aria-haspopup') or 'unknown'
                if input_id in ["pageFooterBackButton", "pageFooterNextButton", "backToJobPosting"]:
                    continue

                group_label, aria_labelledby = await self._get_group_label_and_aria(input_el)
                question = await self._get_nearest_label_text(input_el) or 'UNLABELED'

                input_type = await input_el.get_attribute('type') or 'unknown'
                role = await input_el.get_attribute('role')
                placeholder = await input_el.get_attribute('placeholder')
                required = await input_el.get_attribute('required')

                if role == "spinbutton":
                    input_type = "spinbutton"

                # Enhanced duplicate question detection like in the notebook
                print(f"Input ID: {input_id}, Question: {question}, aria-labelledby: {aria_labelledby or 'None'}")
                print(f"Previous question: {previous_question}, Previous type: {previous_type}")
                
                if (question != 'UNLABELED' and 
                    question == previous_question and 
                    previous_type == "listbox" and 
                    input_id != "file-upload-input-ref"):
                    print(f"Skipping duplicate question: '{question}'")
                    continue

                input_tag = await input_el.evaluate("(el) => el.tagName.toLowerCase()")
                if input_tag and input_tag.lower() == 'textarea':
                    input_type = 'textarea'
                
                # Get options for all relevant input types
                options = await self._get_element_options(input_el, input_tag, input_type)

                # Only include elements that belong to the current panel
                if aria_labelledby and f'{i + 1}-panel' in aria_labelledby:
                    panel_elements.append({
                        'element': input_el,
                        'question': question or 'UNLABELED',
                        'aria_labelledby': aria_labelledby,
                        'input_type': input_type,
                        'input_tag': input_tag,
                        'input_id': input_id,
                        'options': options,
                        'placeholder': placeholder,
                        'required': required,
                        'role': role
                    })

                # Update tracking variables like in the notebook
                if question != 'UNLABELED':
                    previous_question = question
                    previous_type = input_type

            if panel_elements:
                print(f"Panel Elements Count: {len(panel_elements)}")
                for field in panel_elements:
                    input_type = field['input_type']
                    options = field['options'] if field['options'] else 'None'
                    print(f"Element: {field['question']}, Type: {input_type}, Options: {options}")

                # Get AI response with complete element information
                ai_values, key_mapping = await self._get_ai_response_for_section(item_data, panel_elements)
                print("AI Response:", ai_values)

                # Fill all elements with validation
                await self._fill_form_elements(ai_values, key_mapping)
                
            await asyncio.sleep(2)

    async def _extract_form_elements_from_section(self, section) -> List[Dict[str, Any]]:
        """Extract form elements from a specific section with duplicate question filtering based on previous listbox"""
        try:
            elements = []
            
            # Find all input elements in the section
            inputs = await section.query_selector_all('input, button, textarea, select')
            
            for input_el in inputs:
                element_info = await self._extract_element_info(input_el)
                if element_info:
                    current_question = element_info['question'].lower().strip()
                    is_current_listbox = (element_info['input_tag'] == 'button' and 
                                        await input_el.get_attribute('aria-haspopup') == 'listbox')
                    
                    # Skip if this question is the same as previous AND previous was a listbox
                    if (self.previous_question and 
                        current_question == self.previous_question and 
                        self.previous_was_listbox):
                        print(f"Skipping duplicate question '{element_info['question']}' because previous question was a listbox")
                        continue
                    
                    # Update tracking for next iteration
                    self.previous_question = current_question
                    self.previous_was_listbox = is_current_listbox
                    
                    elements.append(element_info)
            
            return elements
            
        except Exception as e:
            print(f"Error extracting form elements from section: {e}")
            return []

    async def _extract_form_elements_from_page(self) -> List[Dict[str, Any]]:
        """Extract all form elements from the current page with duplicate question filtering based on previous listbox"""
        try:
            elements = []
            
            # Find all input elements on the page
            inputs = await self.page.query_selector_all('input, button, textarea, select')
            
            for input_el in inputs:
                element_info = await self._extract_element_info(input_el)
                if element_info:
                    current_question = element_info['question'].lower().strip()
                    is_current_listbox = (element_info['input_tag'] == 'button' and 
                                        await input_el.get_attribute('aria-haspopup') == 'listbox')
                    
                    # Skip if this question is the same as previous AND previous was a listbox
                    if (self.previous_question and 
                        current_question == self.previous_question and 
                        self.previous_was_listbox):
                        print(f"Skipping duplicate question '{element_info['question']}' because previous question was a listbox")
                        continue
                    
                    # Update tracking for next iteration
                    self.previous_question = current_question
                    self.previous_was_listbox = is_current_listbox
                    
                    elements.append(element_info)
            
            return elements
            
        except Exception as e:
            print(f"Error extracting form elements from page: {e}")
            return []

    async def _extract_element_info(self, input_el) -> Optional[Dict[str, Any]]:
        """Extract information about a form element"""
        try:
            input_tag = await input_el.evaluate('el => el.tagName.toLowerCase()')
            input_type = await input_el.get_attribute('type') or 'unknown'
            input_id = await input_el.get_attribute('id') or 'unknown'
            
            # Get label information
            question = await self._get_nearest_label_text(input_el)
            group_label, aria_labelledby = await self._get_group_label_and_aria(input_el)
            
            # Get options for dropdown elements
            options = await self._get_element_options(input_el, input_tag, input_type)
            
            # Get other attributes
            placeholder = await input_el.get_attribute('placeholder')
            required = await input_el.get_attribute('aria-required')
            role = await input_el.get_attribute('role')
            
            return {
                'element': input_el,
                'question': question or 'Unknown',
                'input_id': input_id,
                'input_type': input_type,
                'input_tag': input_tag,
                'aria_labelledby': aria_labelledby,
                'options': options,
                'placeholder': placeholder,
                'required': required,
                'role': role
            }
            
        except Exception as e:
            print(f"Error extracting element info: {e}")
            return None

    async def _get_nearest_label_text(self, element) -> Optional[str]:
        """Get the nearest label text for a form element"""
        try:
            # Try multiple methods to find the label
            element_id = await element.get_attribute('id')
            if element_id and element_id != "unknown":
                label_elem = await self.page.query_selector(f'label[for="{element_id}"]')
                if label_elem:
                    label_text = await label_elem.text_content()
                    if label_text:
                        return label_text.replace('*', '').strip()
            
            # Try parent label
            parent_label_handle = await element.evaluate_handle('el => el.closest("label")')
            parent_label = parent_label_handle.as_element() if parent_label_handle else None
            if parent_label:
                label_text = await parent_label.text_content()
                if label_text:
                    return label_text.replace('*', '').strip()
            
            # Try form field label
            form_field_label = await element.evaluate('''
                el => {
                    let cur = el.parentElement;
                    let depth = 0;
                    while (cur && depth < 10) {
                        if (cur.tagName.toLowerCase() === "div" &&
                            cur.getAttribute("data-automation-id")?.startsWith("formField-")) {
                            const lbl = cur.querySelector("label span, label");
                            if (lbl && lbl.textContent) return lbl.textContent.trim();
                        }
                        cur = cur.parentElement;
                        depth++;
                    }
                    return null;
                }
            ''')
            if form_field_label:
                return form_field_label.replace('*', '').strip()
            
            # Try aria-labelledby
            aria_labelledby = await element.get_attribute('aria-labelledby')
            if aria_labelledby:
                label_element = await self.page.query_selector(f'#{aria_labelledby}')
                if label_element:
                    label_text = await label_element.text_content()
                    if label_text:
                        return label_text.replace('*', '').strip()
            
            # Try aria-label
            aria_label = await element.get_attribute('aria-label')
            if aria_label:
                return aria_label.replace('*', '').strip()
            
            # Try placeholder as fallback
            placeholder = await element.get_attribute('placeholder')
            if placeholder:
                return placeholder.replace('*', '').strip()
            
            return None
        except Exception as e:
            print(f"Error getting label for element: {e}")
            return None

    async def _get_group_label_and_aria(self, element) -> Tuple[Optional[str], Optional[str]]:
        """Get group label and aria-labelledby information"""
        try:
            result = await element.evaluate('''
                el => {
                    let group = el.closest("fieldset, [role='group']");
                    let aria_labelledby = null;
                    let label_text = null;
                    if (group) {
                        let legend = group.querySelector("legend");
                        if (legend && legend.textContent) label_text = legend.textContent.trim();
                        let labelledby = group.getAttribute("aria-labelledby");
                        if (labelledby) {
                            aria_labelledby = labelledby;
                            let labelEl = document.getElementById(labelledby);
                            if (labelEl && labelEl.textContent) label_text = labelEl.textContent.trim();
                        }
                        if (!label_text) {
                            let label = group.querySelector("label");
                            if (label && label.textContent) label_text = label.textContent.trim();
                        }
                    }
                    if (!label_text) {
                        let cur = el.parentElement;
                        let depth = 0;
                        while (cur && depth < 15) {
                            let labelledby = cur.getAttribute && cur.getAttribute("aria-labelledby");
                            if (labelledby) {
                                aria_labelledby = labelledby;
                                let labelEl = document.getElementById(labelledby);
                                if (labelEl && labelEl.textContent) {
                                    label_text = labelEl.textContent.trim();
                                    break;
                                }
                            }
                            cur = cur.parentElement;
                            depth++;
                        }
                    }
                    return {label_text, aria_labelledby};
                }
            ''')
            return result.get('label_text'), result.get('aria_labelledby')
        except:
            return None, None

    async def _get_element_options(self, input_el, input_tag: str, input_type: str) -> Optional[List[str]]:
        """Get options for dropdown/select elements"""
        try:
            options = None
            
            if input_tag == "button" or await input_el.get_attribute('role') == 'combobox':
                aria_haspopup = await input_el.get_attribute('aria-haspopup')
                if aria_haspopup == "listbox":
                    options = await self._get_listbox_options(input_el)
            
            return options
        except:
            return None

    async def _get_listbox_options(self, input_el) -> List[str]:
        """Extract options from a listbox by clicking it"""
        try:
            await input_el.click()
            await asyncio.sleep(1)
            
            options = []
            listbox_container = await self.page.query_selector('div[visibility="opened"]')
            
            if listbox_container:
                li_elements = await listbox_container.query_selector_all('li[role="option"]')
                for li in li_elements:
                    text = await li.text_content()
                    if text and text.strip():
                        options.append(text.strip())
                    else:
                        div_text = await li.query_selector('div')
                        if div_text:
                            nested_text = await div_text.text_content()
                            if nested_text and nested_text.strip():
                                options.append(nested_text.strip())

            await input_el.click()  # Close the dropdown
            await asyncio.sleep(0.5)
            return options
        except:
            return []

    async def _get_ai_response_for_section_for_personal_information(self, current_data: Dict[str, Any], panel_elements: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Get AI response for form fields using OpenAI"""
        try:
            form_fields = []
            key_mapping = {}

            for el in panel_elements:
                full_key = f"[{el['question']}, {el['input_id']}, {el['input_type']}, {el['aria_labelledby']}, {el['input_tag']}]"
                
                form_fields.append({
                    "full_key": full_key,
                    "question": el['question'],
                    "input_id": el['input_id'],
                    "input_type": el['input_type'],
                    "input_tag": el['input_tag'],
                    "aria_labelledby": el['aria_labelledby'],
                    "options": el['options'], 
                    "placeholder": el.get('placeholder'),
                    "required": el.get('required'),
                    "role": el.get('role')
                })
                
                key_mapping[full_key] = el

            prompt = f"""
You are helping fill a job application form.
You are mapping user profile data to a web form.

You are given:
- An Entry from user profile data (JSON)
- A list of form fields from the application panel (including labels, field types, and available options if there is dropdown for the element)

Return a JSON dictionary mapping the EXACT "full_key" values to appropriate values. Use the user data to fill the values. 
do not SKIP any field in the my information section, fill up the most accurate response you can come up with based on user profile

CRITICAL: You MUST use the EXACT "full_key" value as the key in your response JSON. Do NOT use just the question text.

IMPORTANT RULES:
- For radio buttons the question is given along with the radio option(Example : Have you worked with us before?(Radio Button Option: Yes?No)): . If the button has to be clicked then answer yes otherwise answer no
- For the country phone code under multiinputcontainer(as a button). Output the country name not the phone code as it fills automatically.
- For fields with "options" not None:
  - You MUST select ONLY from the list of provided OPTIONS (case-sensitive)
  - If the user data is longer (e.g., "Bachelor of Engineering in Computer Science") and options are shorter (e.g., "BS"), choose the CLOSEST MATCH based on meaning
- For text fields: Keep responses concise and relevant
- Match options exactly as they appear in the options list (case-sensitive) when options is not None
- After filling the form, if a field for save and continue is present, respond with yes to save the form

SPECIAL HANDLING FOR SKILLS/MULTI-VALUE FIELDS:
- For fields related to skills, technologies, competencies, or any field that should contain multiple items:
  - Return an ARRAY of strings instead of a single comma-separated string
  - Each skill/technology should be a separate string in the array
  - Example: ["C#", "TypeScript", "Java", "SQL", "HTML5", "CSS3", "Python"] instead of "C#, TypeScript, Java, SQL, HTML5, CSS3, Python"
- Identify skills fields by keywords in the question like: "skills", "technologies", "competencies", "tools", "programming languages", etc.

Data from User Profile:
{json.dumps(current_data, indent=2)}

Form Fields:
{json.dumps(form_fields, indent=2)}

Example response format:
{{
  "[School or University*, unknown, text, Education-(Optional)-2-panel, input]": "University Name",
  "[Degree*, unknown, button, Education-(Optional)-2-panel, button]": "MS",
  "[Field of Study, unknown, unknown, Education-(Optional)-2-panel, input]": "Computer Science",
  "[Type to Add Skills, unknown, unknown, Skills-section, input]": ["C#", "TypeScript", "Java", "SQL", "HTML5", "CSS3", "Python", ".NET Core", "Angular 2+", "RxJS", "Entity Framework", "React", "Redux", "Bootstrap 4"]
}}

Respond ONLY with a valid JSON object using the exact "full_key" values as keys.
"""
            
            response = await self.client.chat.completions.create(
                model="o4-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content.strip()
            
            # Clean up the response to extract JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            ai_response = json.loads(content)
            return ai_response, key_mapping
            
        except Exception as e:
            print(f"Error in get_ai_response_for_section: {e}")
            return {}, {}

    async def _get_ai_response_for_section(self, current_data: Dict[str, Any], panel_elements: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Get AI response for form fields using OpenAI"""
        try:
            form_fields = []
            key_mapping = {}

            for el in panel_elements:
                full_key = f"[{el['question']}, {el['input_id']}, {el['input_type']}, {el['aria_labelledby']}, {el['input_tag']}]"
                
                form_fields.append({
                    "full_key": full_key,
                    "question": el['question'],
                    "input_id": el['input_id'],
                    "input_type": el['input_type'],
                    "input_tag": el['input_tag'],
                    "aria_labelledby": el['aria_labelledby'],
                    "options": el['options'], 
                    "placeholder": el.get('placeholder'),
                    "required": el.get('required'),
                    "role": el.get('role')
                })
                
                key_mapping[full_key] = el

            prompt = f"""
You are helping fill a job application form.
You are mapping user profile data to a web form.

You are given:
- An Entry from user profile data (JSON)
- A list of form fields from the application panel (including labels, field types, and available options if there is dropdown for the element)

Return a JSON dictionary mapping the EXACT "full_key" values to appropriate values. Use the user data to fill the values. If a field is not relevant, map it to "SKIP".

CRITICAL: You MUST use the EXACT "full_key" value as the key in your response JSON. Do NOT use just the question text.

IMPORTANT RULES:
- For fields with "options" not None:
  - You MUST select ONLY from the list of provided OPTIONS (case-sensitive)
  - If the user data is longer (e.g., "Bachelor of Engineering in Computer Science") and options are shorter (e.g., "BS"), choose the CLOSEST MATCH based on meaning
  - If no match is appropriate, use "SKIP"
- For date fields: Month should be number format (e.g., "01" for January), year should be "YYYY" format
- For date-related fields (e.g. type="spinbutton" or input_id includes "Month" or "Year"):
  - Use "MM" format for months (e.g., "01" for January)
  - Use "YYYY" format for years (e.g., "2022")
  - Match "start date", "end date", "graduation date", etc., with the corresponding data from user profile
- Make sure not to skip voluntary disclosure questions about gender, ethnicity, disability, and veteran status and other similar questions
- For text fields: Keep responses concise and relevant
- Match options exactly as they appear in the options list (case-sensitive) when options is not None
- After filling the form, if a field for save and continue is present, respond with yes to save the form

SPECIAL HANDLING FOR SKILLS/MULTI-VALUE FIELDS:
- For fields related to skills, technologies, competencies, or any field that should contain multiple items:
  - Return an ARRAY of strings instead of a single comma-separated string
  - Each skill/technology should be a separate string in the array
  - Example: ["C#", "TypeScript", "Java", "SQL", "HTML5", "CSS3", "Python"] instead of "C#, TypeScript, Java, SQL, HTML5, CSS3, Python"
- Identify skills fields by keywords in the question like: "skills", "technologies", "competencies", "tools", "programming languages", etc.

Data from User Profile:
{json.dumps(current_data, indent=2)}

Form Fields:
{json.dumps(form_fields, indent=2)}

Example response format:
{{
  "[School or University*, unknown, text, Education-(Optional)-2-panel, input]": "University Name",
  "[Degree*, unknown, button, Education-(Optional)-2-panel, button]": "MS",
  "[Field of Study, unknown, unknown, Education-(Optional)-2-panel, input]": "Computer Science",
  "[Type to Add Skills, unknown, unknown, Skills-section, input]": ["C#", "TypeScript", "Java", "SQL", "HTML5", "CSS3", "Python", ".NET Core", "Angular 2+", "RxJS", "Entity Framework", "React", "Redux", "Bootstrap 4"]
}}

Respond ONLY with a valid JSON object using the exact "full_key" values as keys.
"""
            
            response = await self.client.chat.completions.create(
                model="o4-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content.strip()
            
            # Clean up the response to extract JSON
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            ai_response = json.loads(content)
            return ai_response, key_mapping
            
        except Exception as e:
            print(f"Error in get_ai_response_for_section: {e}")
            return {}, {}

    async def _fill_form_elements(self, ai_response: Dict[str, Any], key_mapping: Dict[str, Any]) -> None:
        """Fill form elements based on AI response"""

        for full_key, response_value in ai_response.items():
            if full_key in key_mapping:
                element_info = key_mapping[full_key]
                input_el = element_info['element']
                
                try:
                    print(f"Filling element {element_info['input_id']} with response: {response_value}")
                    await self._fill_single_element(
                        input_el, 
                        element_info['input_id'],
                        element_info['input_type'],
                        element_info['input_tag'],
                        response_value,
                        element_info.get('options')
                    )
                except Exception as e:
                    print(f"Error filling element {element_info['input_id']}: {e}")

    async def _fill_single_element(self, input_el, input_id: str, input_type: str, input_tag: str, response: Any, options: Optional[List[str]] = None) -> None:
        """Fill a single form element"""
        try:
            if response == "SKIP":
                print(f"Skipping input {input_id} as per AI response")
                return

            # Handle file uploads
            if input_tag == "input" and input_type == "file" and isinstance(response, str):
                if os.path.exists(response):
                    await input_el.set_input_files([response])
                    print(f"Uploaded file: {response}")
                return

            # Check if element is inside a multiSelectContainer
            is_multi_select = await input_el.evaluate('''
                el => {
                    let cur = el.parentElement;
                    let depth = 0;
                    while (cur && depth < 10) {
                        if (cur.getAttribute("data-automation-id")?.includes("multiSelectContainer")) {
                            return true;
                        }
                        cur = cur.parentElement;
                        depth++;
                    }
                    return false;
                }
            ''')

            # Handle multi-select containers (skills, etc.)
            if is_multi_select:
                await self._fill_multi_select_element(input_el, input_id, response)
                return

            # Handle regular text inputs and textareas
            if input_tag in ["input", "textarea"] and input_type not in ["radio", "checkbox", "spinbutton"]:
                if isinstance(response, list):
                    response = ", ".join(response)
                await input_el.fill(str(response))
                print(f"Filled {input_id} with: {response}")
                return

            # Handle listbox/dropdown elements
            if input_tag == "button" or await input_el.get_attribute('role') == 'combobox':
                await self._fill_listbox_element(input_el, response)
                return

            # Handle radio buttons
            if input_type == "radio":
                if response in [True, "true", "yes", "Yes", 1]:
                    await input_el.check()
                    print(f"Selected radio button {input_id}")
                else:
                    print(f"Skipping radio button {input_id} as response is not affirmative")
                return

            # Handle checkboxes
            if input_type == "checkbox":
                if response in [True, "true", "yes", "Yes", 1]:
                    await input_el.check()
                    print(f"Checked checkbox {input_id}")
                return

            # Handle spinbutton (number inputs)
            if input_type == "spinbutton":
                await input_el.fill(str(response))
                print(f"Filled spinbutton {input_id} with: {response}")
                return

            print(f"Unhandled element type: {input_tag}/{input_type} for {input_id}")

        except Exception as e:
            print(f"Error filling element {input_id}: {e}")

    async def _fill_multi_select_element(self, input_el, input_id: str, response: Any) -> None:
        """Fill multi-select container element (like skills)"""
        try:
            if not isinstance(response, list):
                response = [response] if response else []

            print(f"Filling MultiInputContainer for {input_id} with responses: {response}")

            # Get the container
            container_handle = await input_el.evaluate_handle('''
                el => {
                    let cur = el.parentElement;
                    let depth = 0;
                    while (cur && depth < 10) {
                        if (cur.getAttribute("data-automation-id")?.includes("multiSelectContainer")) {
                            return cur;
                        }
                        cur = cur.parentElement;
                        depth++;
                    }
                    return null;
                }
            ''')

            container = container_handle.as_element() if container_handle else None
            if not container:
                print(f"Could not find multiSelectContainer for {input_id}")
                return
            max_depth = 3

            if "skills" in input_id.lower():
                max_depth = 1

            # Add each skill/item
            for item in response:
                try:
                    # Click the container to focus
                    await container.click()
                    await asyncio.sleep(1)
                    
                    # Type the skill
                    await input_el.fill(str(item))
                    await asyncio.sleep(0.5)
                    
                    # Press Enter or Tab to add the item
                    await input_el.press('Enter')
                    await asyncio.sleep(1)

                    prompt_options = await self.page.query_selector_all('div[data-automation-id="promptLeafNode"]')

                    while prompt_options and max_depth > 0:
                        selected_options = random.choice(prompt_options) if prompt_options else None    

                        for opt in prompt_options:
                            print(await opt.text_content())

                        if selected_options:
                            await selected_options.click()
                            print("Clicked on a random prompt option.")
                        await asyncio.sleep(1)
                        max_depth -= 1
                        prompt_options = await self.page.query_selector_all('div[data-automation-id="promptLeafNode"]')

                    print(f"Added skill: {item}")
                    
                except Exception as e:
                    print(f"Error adding skill '{item}': {e}")

        except Exception as e:
            print(f"Error filling multi-select element {input_id}: {e}")

    async def _fill_listbox_element(self, input_el, response: str) -> None:
        """Fill a listbox/combobox element"""
        try:
            await input_el.click()
            await asyncio.sleep(0.5)
            
            listbox = await self.page.query_selector('div[visibility="opened"]')
            if listbox:
                li_elements = await listbox.query_selector_all('li')
                for li in li_elements:
                    text = await li.text_content()
                    if text and (text.lower() == response.lower() or response.lower() in text.lower()):
                        await li.click()
                        print(f"Selected option: {text}")
                        return True
                        
                    # Check nested div elements
                    div_element = await li.query_selector('div')
                    if div_element:
                        div_text = await div_element.text_content()
                        if div_text and response.lower() in div_text.lower():
                            await li.click()
                            print(f"Selected option: {div_text}")
                            await asyncio.sleep(0.2)
                            return True
            
            print(f"Could not find option '{response}' in dropdown")
            return False
            
        except Exception as e:
            print(f"Error filling listbox element: {e}")
            return False

    async def submit_form(self) -> bool:
        """Submit the current form"""
        try:
            # Look for submit/continue button
            submit_selectors = [
                'button[data-automation-id="pageFooterNextButton"]',
                'button[aria-label*="Save and Continue"]',
                'button[aria-label*="Submit"]',
                'button[aria-label*="Next"]'
            ]
            
            for selector in submit_selectors:
                submit_btn = await self.page.query_selector(selector)
                if submit_btn:
                    await submit_btn.click()
                    print(f"Clicked submit button: {selector}")
                    await asyncio.sleep(5)
                    return True
            
            print("No submit button found")
            return False
            
        except Exception as e:
            print(f"Error submitting form: {e}")
            return False

    async def close_browser(self) -> None:
        """Close the browser"""
        if self.browser:
            await self.browser.close()
            print("Browser closed")

    async def run_full_application(self, company: str = "harris", auth_type: int = 1) -> None:
        """Run the complete job application process"""
        try:
            print("=== Starting Job Application Automation ===")
            
            # Initialize browser
            await self.initialize_browser(headless=False)
            
            # Navigate to job
            await self.navigate_to_job(company)
            
            # Handle authentication
            auth_success = await self.handle_authentication(auth_type)
            if not auth_success:
                print("Authentication failed")
                return
            
            # Process application form
            await self.process_application_form()
            
            # Submit final form
            await self.submit_form()
            
            print("=== Job Application Completed Successfully ===")
            
        except Exception as e:
            print(f"Error during job application: {e}")
        finally:
            await self.close_browser()


# Usage example
async def main():
    """Main function to run the job application bot"""
    bot = JobApplicationBot()
    
    # Get user choice for authentication
    try:
        auth_choice = int(input("Enter 1 for sign in or 2 for sign up: "))
    except ValueError:
        auth_choice = 1
    
    # Get company choice
    print("Available companies:")
    for i, company in enumerate(bot.company_urls.keys(), 1):
        print(f"{i}. {company.title()}")
    
    try:
        company_choice = int(input("Select company (1-5): "))
        company_names = list(bot.company_urls.keys())
        selected_company = company_names[company_choice - 1]
    except (ValueError, IndexError):
        selected_company = "harris"  # Default
    
    # Run the application
    await bot.run_full_application(company=selected_company, auth_type=auth_choice)


if __name__ == "__main__":
    asyncio.run(main())
