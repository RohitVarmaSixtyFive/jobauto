"""
Authentication Handler Module

This module handles the actual authentication process including form detection,
filling, and submission for both sign-in and sign-up workflows.

Author: Job Automation Team
Date: July 23, 2025
"""

import asyncio
from typing import Dict, Any, List, Optional
from playwright.async_api import Page, Locator

from src.utils.logger import ApplicationLogger
from src.utils.form_extractor import FormExtractor
from src.utils.form_logger import FormDataLogger


class AuthenticationHandler:
    """
    Handles authentication form interactions for sign-in and sign-up processes.
    
    This class provides methods for detecting authentication forms, filling them
    with user credentials, and submitting them with proper error handling.
    """
    
    def __init__(self, page: Page, logger: ApplicationLogger):
        """
        Initialize the authentication handler.
        
        Args:
            page: Playwright page instance
            logger: Application logger instance
        """
        self.page = page
        self.logger = logger
        self.form_extractor = FormExtractor(page, logger)
        self.form_data_logger = FormDataLogger(logger)
    
    async def log_initial_form_state(self, auth_type: str):
        """
        Log the initial state of authentication forms on the page.
        
        Args:
            auth_type: Type of authentication (signin/signup)
        """
        try:
            self.logger.workflow_step(f"Form State Logging - {auth_type}", "STARTED")
            
            form_elements = await self.form_extractor.extract_all_form_elements()
            
            await self.form_data_logger.log_form_elements(
                form_elements,
                f"{auth_type}_initial_state",
                {
                    "description": f"Form elements found before {auth_type} process",
                    "action_about_to_perform": auth_type,
                    "page_url": self.page.url,
                    "page_title": await self.page.title()
                }
            )
            
            self.logger.workflow_step(
                f"Form State Logging - {auth_type}",
                "COMPLETED",
                elements_found=len(form_elements)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log initial form state for {auth_type}", exception=e)
    
    async def execute_authentication(
        self, 
        auth_type: str, 
        email: str, 
        password: str
    ) -> bool:
        """
        Execute the complete authentication process.
        
        Args:
            auth_type: Either 'signin' or 'signup'
            email: User email address
            password: User password
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.logger.workflow_step(f"Authentication - {auth_type}", "STARTED")
            
            # If user wants to sign in, try to navigate to sign in page first
            if auth_type == "signin":
                self.logger.info("Attempting to navigate to sign-in page...")
                signin_found = await self.find_and_click_signin_button()
                if signin_found:
                    # Wait for page to load after navigation
                    await self.page.wait_for_load_state('networkidle', timeout=10000)
                    await self.page.wait_for_timeout(2000)
            
            # Extract form elements
            form_elements = await self.form_extractor.extract_all_form_elements()
            
            if not form_elements:
                self.logger.error(f"No form elements found for {auth_type}")
                return False
            
            # Determine authentication strategy based on form elements
            if auth_type == "signin":
                success = await self._handle_signin_flow(form_elements, email, password)
            else:  # signup
                success = await self._handle_signup_flow(form_elements, email, password)
            
            status = "COMPLETED" if success else "FAILED"
            self.logger.workflow_step(f"Authentication - {auth_type}", status)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Authentication execution failed for {auth_type}", exception=e)
            return False
    
    async def find_and_click_signin_button(self):
        """Find and click Sign In button to navigate to sign-in page"""
        signin_selectors = [
            '[data-automation-id="signInLink"]',  # Specific to this case
            '[id="signInLink"]',
            '[name="signInLink"]',
            '[aria-label*="Sign In" i]',
            '[aria-label*="Login" i]',
            '[aria-label*="Log In" i]',
            'button:has-text("Sign In")',
            'button:has-text("Login")',
            'button:has-text("Log In")',
            '[role="button"]:has-text("Sign In")',
            '[role="button"]:has-text("Login")',
            '[role="button"]:has-text("Log In")',
            'a:has-text("Sign In")',
            'a:has-text("Login")',
            'a:has-text("Log In")',
            '*:has-text("Sign In")',
            '*:has-text("Already have an account")'
        ]
        
        for selector in signin_selectors:
            try:
                button = self.page.locator(selector).first
                if await button.count() > 0:
                    button_text = ""
                    try:
                        button_text = await button.inner_text() or await button.get_attribute('aria-label') or ""
                    except:
                        button_text = await button.get_attribute('aria-label') or ""
                    
                    print(f"Found Sign In button with selector {selector}: {button_text}")
                    await button.click()
                    print("✓ Clicked Sign In button")
                    return True
            except Exception as e:
                print(f"  Error with selector {selector}: {str(e)}")
                continue
                
        return False
    
    async def _handle_signin_flow(
        self, 
        form_elements: List[Dict[str, Any]], 
        email: str, 
        password: str
    ) -> bool:
        """
        Handle sign-in specific form filling and submission.
        
        Args:
            form_elements: List of detected form elements
            email: User email
            password: User password
            
        Returns:
            True if sign-in successful, False otherwise
        """
        try:
            self.logger.info("Processing sign-in form...")
            
            # Find email and password fields
            email_field = self._find_email_field(form_elements)
            password_field = self._find_password_field(form_elements)
            
            if not email_field or not password_field:
                self.logger.error("Could not locate email or password fields for sign-in")
                return False
            
            # Fill the form fields
            await self._fill_form_field(email_field, email, "email")
            await self._fill_form_field(password_field, password, "password")
            
            # Find and click submit button
            submit_button = self._find_submit_button(form_elements)
            if not submit_button:
                self.logger.error("Could not locate submit button for sign-in")
                return False
            
            submit_success = await self._click_submit_button(submit_button, "signin")
            if not submit_success:
                self.logger.error("Failed to click submit button for sign-in")
                return False
            
            # Wait for navigation/response (already handled in _click_submit_button)
            # await self._wait_for_authentication_response()
            
            return await self._verify_authentication_success()
            
        except Exception as e:
            self.logger.error("Sign-in flow failed", exception=e)
            return False
    
    async def _handle_signup_flow(
        self, 
        form_elements: List[Dict[str, Any]], 
        email: str, 
        password: str
    ) -> bool:
        """
        Handle sign-up specific form filling and submission.
        
        Args:
            form_elements: List of detected form elements
            email: User email
            password: User password
            
        Returns:
            True if sign-up successful, False otherwise
        """
        try:
            self.logger.info("Processing sign-up form...")
            
            # Find required fields for signup
            email_field = self._find_email_field(form_elements)
            password_field = self._find_password_field(form_elements)
            confirm_password_field = self._find_confirm_password_field(form_elements)
            
            if not email_field or not password_field:
                self.logger.error("Could not locate required fields for sign-up")
                return False
            
            # Fill the form fields
            await self._fill_form_field(email_field, email, "email")
            await self._fill_form_field(password_field, password, "password")
            
            # Fill confirm password if present
            if confirm_password_field:
                await self._fill_form_field(confirm_password_field, password, "confirm_password")
            
            # Find and check the agreement checkbox (required for signup)
            agreement_checkbox = self._find_agreement_checkbox(form_elements)
            if agreement_checkbox:
                await self._click_agreement_checkbox(agreement_checkbox)
            else:
                self.logger.warning("No agreement checkbox found, proceeding without checking it")
            
            # Find and click submit button
            submit_button = self._find_submit_button(form_elements)
            if not submit_button:
                self.logger.error("Could not locate submit button for sign-up")
                return False
            
            submit_success = await self._click_submit_button(submit_button, "signup")
            if not submit_success:
                self.logger.error("Failed to click submit button for sign-up")
                return False
            
            # Wait for navigation/response (already handled in _click_submit_button)
            # await self._wait_for_authentication_response()
            
            return await self._verify_authentication_success()
            
        except Exception as e:
            self.logger.error("Sign-up flow failed", exception=e)
            return False
    
    def _find_email_field(self, form_elements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find email input field from form elements."""
        email_keywords = ["email", "e-mail", "username", "login"]
        
        for element in form_elements:
            element_type = element.get('type_of_input', '').lower()
            label = element.get('label', '').lower()
            name = element.get('name', '').lower()
            
            if (element_type == 'email' or 
                any(keyword in label for keyword in email_keywords) or
                any(keyword in name for keyword in email_keywords)):
                return element
        
        return None
    
    def _find_password_field(self, form_elements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find password input field from form elements."""
        for element in form_elements:
            if element.get('type_of_input', '').lower() == 'password':
                label = element.get('label', '').lower()
                if 'confirm' not in label and 'repeat' not in label:
                    return element
        
        return None
    
    def _find_confirm_password_field(self, form_elements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find confirm password input field from form elements."""
        confirm_keywords = ["confirm", "repeat", "verify"]
        
        for element in form_elements:
            if element.get('type_of_input', '').lower() == 'password':
                label = element.get('label', '').lower()
                if any(keyword in label for keyword in confirm_keywords):
                    return element
        
        return None
    
    def _find_agreement_checkbox(self, form_elements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find agreement/terms checkbox from form elements."""
        agreement_keywords = ["agree", "terms", "condition", "accept", "privacy", "policy"]
        
        for element in form_elements:
            if element.get('type_of_input', '').lower() == 'checkbox':
                # Check by specific data automation ID first
                if element.get('data_automation_id') == 'createAccountCheckbox':
                    return element
                
                # Check by id if it matches our expected pattern
                element_id = element.get('id', '')
                if element_id == 'input-8':  # The specific checkbox ID we're looking for
                    return element
                
                # Check by label content
                label = element.get('label', '').lower()
                if any(keyword in label for keyword in agreement_keywords):
                    return element
        
        return None
    
    async def _click_agreement_checkbox(self, checkbox_info: Dict[str, Any]):
        """
        Click the agreement checkbox to accept terms.
        
        Args:
            checkbox_info: Dictionary containing checkbox element information
        """
        try:
            # Get multiple selector options
            selectors_to_try = []
            
            # Primary selectors based on element info
            if checkbox_info.get('data_automation_id'):
                selectors_to_try.append(f'[data-automation-id="{checkbox_info["data_automation_id"]}"]')
            
            if checkbox_info.get('id'):
                selectors_to_try.append(f'#{checkbox_info["id"]}')
            
            # Add generic selectors
            selectors_to_try.extend([
                'input[type="checkbox"][data-automation-id="createAccountCheckbox"]',
                '#input-8',
                'input[type="checkbox"]#input-8',
                'input[type="checkbox"]:has-text("I agree")',
                'input[type="checkbox"][aria-checked="false"]'
            ])
            
            self.logger.info(f"Attempting to click agreement checkbox with {len(selectors_to_try)} selectors")
            
            for selector in selectors_to_try:
                try:
                    checkbox = self.page.locator(selector)
                    count = await checkbox.count()
                    
                    if count > 0:
                        checkbox_first = checkbox.first
                        
                        # Check if checkbox is already checked
                        is_checked = False
                        try:
                            aria_checked = await checkbox_first.get_attribute('aria-checked')
                            is_checked = aria_checked == 'true'
                        except:
                            try:
                                is_checked = await checkbox_first.is_checked()
                            except:
                                pass
                        
                        if is_checked:
                            self.logger.info("✓ Agreement checkbox is already checked")
                            return True
                        
                        self.logger.form_interaction(
                            "CLICK",
                            "agreement checkbox",
                            selector=selector,
                            label=checkbox_info.get('label', 'Agreement')
                        )
                        
                        # Try clicking the checkbox
                        await checkbox_first.click()
                        
                        # Verify it was checked
                        await self.page.wait_for_timeout(500)  # Brief wait for UI update
                        
                        try:
                            aria_checked = await checkbox_first.get_attribute('aria-checked')
                            if aria_checked == 'true':
                                self.logger.info(f"✓ SUCCESS: Agreement checkbox clicked and checked using selector: {selector}")
                                return True
                        except:
                            # Fallback verification
                            try:
                                if await checkbox_first.is_checked():
                                    self.logger.info(f"✓ SUCCESS: Agreement checkbox clicked and checked using selector: {selector}")
                                    return True
                            except:
                                pass
                        
                        self.logger.warning(f"Checkbox clicked but verification failed with selector: {selector}")
                        
                except Exception as e:
                    self.logger.warning(f"Error with checkbox selector {selector}: {str(e)}")
                    continue
            
            self.logger.error("Failed to click agreement checkbox with all selectors")
            return False
            
        except Exception as e:
            self.logger.error("Failed to click agreement checkbox", exception=e)
            return False
    
    def _find_submit_button(self, form_elements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find submit button from form elements."""
        
        # First priority: Look for the specific create account button (for signup)
        for element in form_elements:
            if element.get('data_automation_id') == 'createAccountSubmitButton':
                return element
        
        # Second priority: Look for the specific sign-in button with click_filter
        for element in form_elements:
            if (element.get('data_automation_id') == 'click_filter' and 
                element.get('aria_label') and 
                'sign in' in element.get('aria_label', '').lower()):
                return element
        
        # Third priority: Standard submit keywords
        submit_keywords = ["submit", "sign in", "sign up", "login", "register", "continue", "create account"]
        
        for element in form_elements:
            element_type = element.get('type_of_input', '').lower()
            label = element.get('label', '').lower()
            text = element.get('text', '').lower()
            aria_label = element.get('aria_label', '').lower()
            
            if (element_type in ['submit', 'button'] or
                any(keyword in label for keyword in submit_keywords) or
                any(keyword in text for keyword in submit_keywords) or
                any(keyword in aria_label for keyword in submit_keywords)):
                return element
        
        return None
    
    async def _fill_form_field(self, field_info: Dict[str, Any], value: str, field_type: str):
        """
        Fill a form field with the provided value.
        
        Args:
            field_info: Dictionary containing field information
            value: Value to fill
            field_type: Type of field for logging
        """
        try:
            # Get the primary selector
            primary_selector = field_info.get('selector')
            
            # Also try alternative selectors like the old code
            element_id = field_info.get('id_of_input_component') or field_info.get('data_automation_id') or field_info.get('id') or field_info.get('name')
            
            selectors_to_try = []
            
            if primary_selector:
                selectors_to_try.append(primary_selector)
            
            if element_id:
                selectors_to_try.extend([
                    f'[data-automation-id="{element_id}"]',
                    f'#{element_id}',
                    f'[name="{element_id}"]'
                ])
            
            if not selectors_to_try:
                self.logger.error(f"No selectors available for {field_type} field")
                return
            
            # Try each selector until one works
            for selector in selectors_to_try:
                try:
                    input_field = self.page.locator(selector)
                    if await input_field.count() > 0:
                        self.logger.form_interaction(
                            "FILL", 
                            f"{field_type} field",
                            selector=selector,
                            label=field_info.get('label', 'Unknown')
                        )
                        
                        # Clear field first, then fill
                        await input_field.fill("")
                        await input_field.fill(value)
                        
                        # Brief pause for stability
                        await self.page.wait_for_timeout(500)
                        
                        self.logger.info(f"✓ Successfully filled {field_type} field with selector: {selector}")
                        return
                        
                except Exception as e:
                    self.logger.warning(f"Failed to fill {field_type} field with selector {selector}: {str(e)}")
                    continue
            
            # If we get here, all selectors failed
            self.logger.error(f"All selectors failed for {field_type} field")
            
        except Exception as e:
            self.logger.error(f"Failed to fill {field_type} field", exception=e)
            raise
    
    async def _click_submit_button(self, button_info: Dict[str, Any], auth_type: str = None):
        """
        Click the submit button.
        
        Args:
            button_info: Dictionary containing button information
            auth_type: Type of authentication (signin/signup) to prioritize correct selectors
        """
        try:
            # Get the primary selector
            primary_selector = button_info.get('selector')
            
            # Also try alternative selectors like the old code
            element_id = button_info.get('id_of_input_component') or button_info.get('data_automation_id') or button_info.get('id') or button_info.get('name')
            
            selectors_to_try = []
            
            if primary_selector:
                selectors_to_try.append(primary_selector)
            
            if element_id:
                selectors_to_try.extend([
                    f'[data-automation-id="{element_id}"]',
                    f'#{element_id}',
                    f'[name="{element_id}"]'
                ])
            
            # Add context-specific selectors based on auth type
            if auth_type == "signup":
                # Prioritize signup-specific selectors
                selectors_to_try.extend([
                    '[data-automation-id="createAccountSubmitButton"]',
                    'button[type="submit"]:has-text("Create Account")',
                    'button:has-text("Create Account")',
                    '[role="button"]:has-text("Create Account")',
                    'button[type="submit"]'
                ])
            elif auth_type == "signin":
                # Prioritize signin-specific selectors
                selectors_to_try.extend([
                    '[data-automation-id="click_filter"][aria-label="Sign In"]',
                    'div[data-automation-id="click_filter"][aria-label*="Sign In" i]',
                    '[data-automation-id="click_filter"][aria-label*="Sign In" i]',
                    '[data-automation-id="utilityButtonSignIn"]',
                    '[data-automation-id="signInSubmitButton"]',
                    'button:has-text("Sign In")',
                    'button:has-text("Login")',
                    'button:has-text("Log In")',
                    '[role="button"]:has-text("Sign In")',
                    '[role="button"]:has-text("Login")',
                    '[role="button"]:has-text("Log In")',
                    'button[type="submit"]'
                ])
            else:
                # Fallback - try both but prioritize createAccount first
                selectors_to_try.extend([
                    '[data-automation-id="createAccountSubmitButton"]',
                    '[data-automation-id="click_filter"][aria-label="Sign In"]',
                    'div[data-automation-id="click_filter"][aria-label*="Sign In" i]',
                    '[data-automation-id="click_filter"][aria-label*="Sign In" i]',
                    '[data-automation-id="utilityButtonSignIn"]',
                    '[data-automation-id="signInSubmitButton"]',
                    'button[type="submit"]',
                    'button:has-text("Sign In")',
                    'button:has-text("Login")',
                    'button:has-text("Log In")',
                    'button:has-text("Create Account")',
                    '[role="button"]:has-text("Sign In")',
                    '[role="button"]:has-text("Login")',
                    '[role="button"]:has-text("Log In")',
                    '[role="button"]:has-text("Create Account")',
                    '[aria-label*="Sign In" i]',
                    '[aria-label*="Login" i]'
                ])
            
            if not selectors_to_try:
                self.logger.error("No selectors available for submit button")
                return False
            
            self.logger.info(f"Trying {len(selectors_to_try)} selectors for {auth_type or 'unknown'} submit button")
            
            # Try each selector until one works (like the old code)
            for selector in selectors_to_try:
                try:
                    button = self.page.locator(selector)
                    count = await button.count()
                    
                    if count > 0:
                        button_first = button.first
                        
                        self.logger.form_interaction(
                            "CLICK",
                            f"{auth_type or 'submit'} button",
                            selector=selector,
                            label=button_info.get('label', 'Unknown')
                        )
                        
                        try:
                            # Try simple click first
                            await button_first.click()
                            self.logger.info(f"✓ SUCCESS: Clicked {auth_type or 'submit'} button with simple click using selector: {selector}")
                            
                            # Wait for navigation/new page to load
                            current_url = self.page.url
                            self.logger.info(f"Waiting for navigation from: {current_url}")
                            
                            # Wait for either URL change or network idle
                            try:
                                await self.page.wait_for_function(
                                    f"window.location.href !== '{current_url}'",
                                    timeout=3000
                                )
                                self.logger.info(f"Navigation detected to: {self.page.url}")
                            except:
                                self.logger.info("No URL change detected, waiting for network idle...")
                            
                            await self.page.wait_for_load_state('networkidle', timeout=15000)
                            self.logger.info(f"✓ Page loaded after {auth_type or 'submit'} button click")
                            return True
                            
                        except Exception as e:
                            self.logger.warning(f"Simple click failed: {str(e)}")
                            
                            # Try force click as backup
                            try:
                                await button_first.click(force=True)
                                self.logger.info(f"✓ SUCCESS: Clicked {auth_type or 'submit'} button with force click using selector: {selector}")
                                
                                # Wait for navigation
                                current_url = self.page.url
                                try:
                                    await self.page.wait_for_function(
                                        f"window.location.href !== '{current_url}'",
                                        timeout=3000
                                    )
                                except:
                                    pass
                                
                                await self.page.wait_for_load_state('networkidle', timeout=15000)
                                return True
                                
                            except Exception as e2:
                                self.logger.warning(f"Force click also failed: {str(e2)}")
                                continue
                        
                except Exception as e:
                    self.logger.warning(f"Error with selector {selector}: {str(e)}")
                    continue
            
            # If we reach here, submit button was not found or clicked successfully
            self.logger.error(f"All selectors failed for {auth_type or 'submit'} button")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to click {auth_type or 'submit'} button", exception=e)
            return False
    
    async def _wait_for_authentication_response(self):
        """Wait for authentication response/navigation."""
        try:
            # Get current URL before waiting
            current_url = self.page.url
            self.logger.info(f"Waiting for navigation from: {current_url}")
            
            # Wait for either URL change or network idle
            try:
                await asyncio.wait_for(
                    self.page.wait_for_function(
                        f"window.location.href !== '{current_url}'",
                        timeout=3000
                    ),
                    timeout=3.0
                )
                new_url = self.page.url
                self.logger.info(f"Navigation detected to: {new_url}")
            except asyncio.TimeoutError:
                self.logger.info("No URL change detected, waiting for network idle...")
            
            # Wait for network idle with longer timeout
            await asyncio.wait_for(
                self.page.wait_for_load_state('networkidle'),
                timeout=15.0
            )
            
            # Additional buffer for page stability
            await self.page.wait_for_timeout(2000)
            
            self.logger.info("✓ Page loaded after authentication")
            
        except asyncio.TimeoutError:
            self.logger.warning("Authentication response timeout")
        except Exception as e:
            self.logger.error("Error waiting for authentication response", exception=e)
    
    async def _verify_authentication_success(self) -> bool:
        """
        Verify if authentication was successful by checking page changes.
        
        Returns:
            True if authentication appears successful, False otherwise
        """
        try:
            current_url = self.page.url
            page_title = await self.page.title()
            
            self.logger.info(f"Verifying authentication success...")
            self.logger.info(f"Current URL: {current_url}")
            self.logger.info(f"Page Title: {page_title}")
            
            # Check for error messages on page first
            error_selectors = [
                '[class*="error"]',
                '[class*="alert"]',
                '[id*="error"]',
                'text="Invalid"',
                'text="Error"',
                'text="Failed"',
                'text="incorrect"',
                'text="wrong"'
            ]
            
            has_error = False
            for selector in error_selectors:
                try:
                    error_element = await self.page.query_selector(selector)
                    if error_element and await error_element.is_visible():
                        error_text = await error_element.text_content()
                        self.logger.warning(f"Found error message: {error_text}")
                        has_error = True
                        break
                except:
                    continue
            
            # If there are visible errors, authentication failed
            if has_error:
                self.logger.error("Authentication failed: Error messages found on page")
                return False
            
            # Enhanced success indicators for job application sites
            success_indicators = [
                "dashboard", "profile", "account", "welcome", "home",
                "application", "apply", "job", "form", "personal", 
                "information", "resume", "upload", "submit"
            ]
            
            url_lower = current_url.lower()
            title_lower = page_title.lower()
            
            # Check if URL or title contains success indicators
            has_success_indicator = any(
                indicator in url_lower or indicator in title_lower 
                for indicator in success_indicators
            )
            
            # Additional checks for job application sites
            # Check if we're still on login/signin page (indicates failure)
            login_indicators = ["login", "signin", "sign-in", "authenticate"]
            still_on_login = any(
                indicator in url_lower or indicator in title_lower
                for indicator in login_indicators
            )
            
            # Check for form elements that indicate we're on an application page
            form_elements_present = False
            try:
                # Look for common application form elements
                form_selectors = [
                    'input[type="text"]',
                    'input[type="email"]', 
                    'textarea',
                    'select',
                    'input[type="file"]'
                ]
                
                for selector in form_selectors:
                    elements = await self.page.query_selector_all(selector)
                    if len(elements) > 2:  # If there are multiple form elements
                        form_elements_present = True
                        break
            except:
                pass
            
            # Determine success based on multiple factors
            success = (
                not has_error and 
                (has_success_indicator or form_elements_present) and 
                not still_on_login
            )
            
            # If none of the above criteria work, check for URL change from login page
            if not success and not still_on_login:
                # If we're not still on login page and no errors, consider it successful
                success = True
            
            self.logger.info(
                f"Authentication verification result: {'SUCCESS' if success else 'FAILED'}",
                url=current_url,
                title=page_title,
                has_success_indicator=has_success_indicator,
                has_error=has_error,
                still_on_login=still_on_login,
                form_elements_present=form_elements_present
            )
            
            return success
            
        except Exception as e:
            self.logger.error("Error verifying authentication success", exception=e)
            return False
    
    async def log_authentication_result(self, auth_type: str, success: bool):
        """
        Log the final authentication result.
        
        Args:
            auth_type: Type of authentication performed
            success: Whether authentication was successful
        """
        try:
            result_data = {
                "authentication_type": auth_type,
                "success": success,
                "final_url": self.page.url,
                "page_title": await self.page.title(),
                "timestamp": await self._get_current_timestamp()
            }
            
            await self.form_data_logger.log_step_completion(
                f"{auth_type}_authentication",
                success,
                result_data
            )
            
            if success:
                self.logger.success(f"{auth_type.title()} authentication completed successfully")
            else:
                self.logger.failure(f"{auth_type.title()} authentication failed")
                
        except Exception as e:
            self.logger.error(f"Failed to log authentication result for {auth_type}", exception=e)
    
    async def _get_current_timestamp(self) -> str:
        """Get current timestamp for logging."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
