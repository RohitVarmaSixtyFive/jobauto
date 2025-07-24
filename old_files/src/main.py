"""
Job Application Automation Tool - Main Entry Point

This module serves as the main entry point for the job application automation system.
It orchestrates the complete workflow from authentication to form completion.

Author: Job Automation Team
Date: July 23, 2025
"""

import json
import asyncio
import os
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page

# Internal imports
from src.config import ApplicationConfig
from src.core.browser_manager import BrowserManager
from src.core.authentication_manager import AuthenticationManager
from src.modules.authentication.auth_handler import AuthenticationHandler
from src.modules.personal_information.form_processor import FormProcessor
from src.utils.data_loader import DataLoader
from src.utils.result_manager import ResultManager
from src.utils.logger import ApplicationLogger


class JobApplicationAutomator:
    """
    Main orchestrator class for the job application automation workflow.
    
    This class manages the complete workflow from loading user data,
    handling authentication, to completing forms.
    """
    
    def __init__(self):
        """Initialize the job application automator."""
        self.config = ApplicationConfig()
        self.logger = ApplicationLogger()
        self.data_loader = DataLoader()
        self.result_manager = ResultManager()
        
    async def initialize_user_session(self) -> Optional[Dict[str, Any]]:
        """
        Load and validate user data from configuration files.
        
        Returns:
            Dict containing user data if successful, None otherwise
        """
        self.logger.info("Loading user configuration data...")
        
        user_data = self.data_loader.load_user_profile()
        if not user_data:
            self.logger.error("Failed to load user profile data")
            return None
            
        # Validate required fields
        personal_info = user_data.get('personal_information', {})
        if not personal_info.get('email') or not personal_info.get('password'):
            self.logger.error("Missing required credentials in user data")
            return None
            
        self.logger.info(f"User profile loaded for: {personal_info.get('name', 'Unknown User')}")
        return user_data
        
    async def execute_authentication_workflow(
        self, 
        page: Page, 
        user_choice: str,
        credentials: Dict[str, str]
    ) -> bool:
        """
        Execute the authentication workflow based on user choice.
        
        Args:
            page: Playwright page object
            user_choice: Either 'signin' or 'signup'
            credentials: User credentials dictionary
            
        Returns:
            True if authentication successful, False otherwise
        """
        self.logger.info(f"Starting {user_choice} authentication workflow...")
        
        auth_handler = AuthenticationHandler(page, self.logger)
        
        # Log initial page state
        await auth_handler.log_initial_form_state(user_choice)
        
        # Execute authentication based on user choice
        auth_success = await auth_handler.execute_authentication(
            auth_type=user_choice,
            email=credentials['email'],
            password=credentials['password']
        )
        
        # Log authentication result
        await auth_handler.log_authentication_result(user_choice, auth_success)
        
        return auth_success
        
    async def execute_my_information_form_workflow(self, page: Page, user_data: Dict[str, Any]) -> bool:
        """
        Execute the my information form workflow after successful authentication.
        
        Args:
            page: Playwright page object
            user_data: Complete user data dictionary
            
        Returns:
            True if form completion successful, False otherwise
        """
        self.logger.info("Starting my information form workflow...")
        
        # Wait for page navigation after authentication with error detection
        page_ready = await self._wait_for_stable_page_after_auth(page)
        if not page_ready:
            self.logger.error("❌ Page failed to load properly after authentication")
            return False
        
        form_processor = FormProcessor(page, self.logger)
        
        # TEMPORARY FIX: Check if name field is already filled and skip everything if so
        self.logger.info("🔍 Checking if form is already filled...")
        try:
            name_field_selector = "#name--legalName--firstName"
            name_field = await page.query_selector(name_field_selector)
            if name_field:
                current_name = await page.input_value(name_field_selector)
                if current_name and current_name.strip():
                    self.logger.success(f"✅ Form already filled with name: '{current_name.strip()}' - skipping to form processing")
                    # Skip the dropdown handling and go straight to form processing
                    await form_processor.log_initial_form_state("my_information_complete")
                    form_success = await form_processor.process_personal_information_form(user_data)
                    await form_processor.log_form_completion_result("my_information", form_success)
                    return form_success
        except Exception as e:
            self.logger.warning(f"Error checking if form is filled, proceeding normally: {e}")
        
        # Handle cascading "How Did You Hear About Us?" dropdown
        self.logger.info("Handling cascading 'How Did You Hear About Us?' dropdown...")
        try:
            # Step 1: Click the search field to open first dropdown
            how_did_you_hear_selector = "#source--source"
            await page.click(how_did_you_hear_selector)
            self.logger.info("✓ Successfully clicked 'How Did You Hear About Us?' field")
            
            # Wait for first dropdown to appear
            await page.wait_for_timeout(3000)
            
            # Step 2: Click first dropdown option (e.g., "University")
            self.logger.info("Clicking first dropdown option...")
            first_option_clicked = await self._click_first_available_dropdown_option(page)
            
            if first_option_clicked:
                self.logger.info("✓ Successfully clicked first dropdown option")
                
                # Wait for second dropdown to appear
                await page.wait_for_timeout(3000)
                
                # Step 3: Click second dropdown option if available
                self.logger.info("Looking for and clicking second dropdown option...")
                second_option_clicked = await self._click_second_dropdown_option(page)
                
                if second_option_clicked:
                    self.logger.info("✓ Successfully clicked second dropdown option")
                    # Wait for any additional elements to load
                    await page.wait_for_timeout(2000)
                else:
                    self.logger.info("ℹ️ No second dropdown option found or needed")
            else:
                self.logger.warning("⚠️ Failed to click first dropdown option")
            
            # Step 4: Extract ALL final form elements in ONE log
            self.logger.info("Extracting complete form elements after dropdown interactions...")
            await form_processor.log_initial_form_state("my_information_complete")
            
        except Exception as e:
            self.logger.error(f"Failed to handle 'How Did You Hear About Us?' dropdown: {str(e)}")
            return False
        
        # Process personal information form with user data
        self.logger.info("Processing personal information form with user data...")
        try:
            form_success = await form_processor.process_personal_information_form(user_data)
            
            if form_success:
                self.logger.success("✅ Personal information form processed successfully")
            else:
                self.logger.warning("⚠️ Personal information form processing completed with some issues")
                
        except Exception as e:
            self.logger.error(f"Failed to process personal information form: {str(e)}")
            form_success = False
        
        # Log form completion result
        await form_processor.log_form_completion_result("my_information", form_success)
        
        return form_success
        
    async def _click_first_available_dropdown_option(self, page: Page) -> bool:
        """
        Click the first available dropdown option from the "How Did You Hear About Us?" dropdown.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if option was clicked successfully, False otherwise
        """
        try:
            # Look for visible dropdown options with multiple selector strategies
            option_selectors = [
                'div[data-automation-id="promptOption"]',
                'div[data-automation-id="promptLeafNode"] div[data-automation-id="promptOption"]',
                '[id*="promptOption"]'
            ]
            
            for selector in option_selectors:
                try:
                    # Wait for options to be available
                    await page.wait_for_selector(selector, timeout=5000)
                    options = await page.query_selector_all(selector)
                    
                    for option in options:
                        if await option.is_visible():
                            # Get the option text for logging
                            option_text = await option.text_content()
                            option_text = option_text.strip() if option_text else "Unknown"
                            
                            self.logger.info(f"Clicking first dropdown option: '{option_text}'")
                            
                            # Click the option
                            await option.click()
                            
                            # Wait for any resulting changes
                            await page.wait_for_timeout(2000)
                            
                            return True
                            
                except Exception as selector_error:
                    self.logger.debug(f"Selector '{selector}' failed: {str(selector_error)}")
                    continue
            
            self.logger.warning("No visible dropdown options found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error clicking first dropdown option: {str(e)}")
            return False
    
    async def _click_second_dropdown_option(self, page: Page) -> bool:
        """
        Click an option from the second (cascading) dropdown if it appears.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if second option was clicked, False if no second dropdown or click failed
        """
        try:
            # Wait for potential second dropdown to appear
            await page.wait_for_timeout(3000)
            
            # Look for newly appeared dropdown options
            option_selectors = [
                'div[data-automation-id="promptOption"]',
                'div[data-automation-id="promptLeafNode"] div[data-automation-id="promptOption"]',
                '[id*="promptOption"]'
            ]
            
            # Count current visible options to detect new ones
            total_visible_options = 0
            
            for selector in option_selectors:
                try:
                    options = await page.query_selector_all(selector)
                    
                    for option in options:
                        if await option.is_visible():
                            total_visible_options += 1
                            
                            # Get option details
                            option_text = await option.text_content()
                            option_text = option_text.strip() if option_text else "Unknown"
                            
                            # Check if this might be a second-level option
                            # (you can customize this logic based on your specific dropdown structure)
                            option_id = await option.get_attribute('id')
                            
                            # If we find options, click the first available one
                            # (In a real scenario, you might want more specific logic here)
                            if option_text and option_text.lower() not in ['university', 'college', 'school']:
                                self.logger.info(f"Clicking second dropdown option: '{option_text}'")
                                
                                await option.click()
                                await page.wait_for_timeout(1000)
                                
                                return True
                            
                except Exception as selector_error:
                    self.logger.debug(f"Second dropdown selector '{selector}' failed: {str(selector_error)}")
                    continue
            
            # If we found multiple visible options, it might mean second dropdown appeared
            if total_visible_options > 1:
                self.logger.info(f"Found {total_visible_options} total visible options, attempting to click a second-level option")
                
                # Try clicking any visible option that's not the first one
                for selector in option_selectors:
                    try:
                        options = await page.query_selector_all(selector)
                        
                        if len(options) > 1:  # More than one option available
                            second_option = options[1]  # Click the second option
                            
                            if await second_option.is_visible():
                                option_text = await second_option.text_content()
                                option_text = option_text.strip() if option_text else "Unknown"
                                
                                self.logger.info(f"Clicking second available option: '{option_text}'")
                                await second_option.click()
                                await page.wait_for_timeout(1000)
                                
                                return True
                                
                    except Exception:
                        continue
            
            self.logger.info("No second dropdown options found or needed")
            return False
            
        except Exception as e:
            self.logger.error(f"Error clicking second dropdown option: {str(e)}")
            return False
    
    async def _wait_for_stable_page_after_auth(self, page: Page, max_retries: int = 3) -> bool:
        """
        Wait for the page to load properly after authentication with error detection and recovery.
        
        Args:
            page: Playwright page object
            max_retries: Maximum number of refresh attempts if errors are detected
            
        Returns:
            True if page loaded successfully, False otherwise
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Checking page stability (attempt {attempt + 1}/{max_retries})...")
                
                # Wait for initial page load
                await page.wait_for_load_state('networkidle', timeout=15000)
                await page.wait_for_timeout(3000)  # Initial buffer
                
                # Get current page info
                current_url = page.url
                page_title = await page.title()
                
                self.logger.info(f"    Current URL: {current_url}")
                self.logger.info(f"    Page title: {page_title}")
                
                # Check for error indicators on the page
                error_indicators = [
                    "something went wrong",
                    "something is wrong", 
                    "error occurred",
                    "page not found",
                    "service unavailable",
                    "temporarily unavailable",
                    "please try again",
                    "oops",
                    "unable to process"
                ]
                
                # Get page content to check for errors
                page_content = await page.content()
                page_text = await page.text_content('body') if await page.query_selector('body') else ""
                page_text_lower = page_text.lower() if page_text else ""
                
                # Check if any error indicators are present
                error_found = any(indicator in page_text_lower for indicator in error_indicators)
                
                if error_found:
                    self.logger.warning(f"🚨 Error detected on page (attempt {attempt + 1}):")
                    for indicator in error_indicators:
                        if indicator in page_text_lower:
                            self.logger.warning(f"   ⚠️  Found: '{indicator}'")
                    
                    if attempt < max_retries - 1:
                        self.logger.info("🔄 Refreshing page to recover from error...")
                        await page.reload(wait_until='networkidle', timeout=15000)
                        await page.wait_for_timeout(5000)
                        continue
                    else:
                        self.logger.error("❌ Max retries reached, page still showing errors")
                        return False
                
                # Check if essential form elements are present
                # Look for common form indicators
                form_indicators = [
                    "#source--source",  # "How did you hear about us" field
                    "[name='country']",  # Country field
                    "[id*='firstName']",  # First name field
                    "[id*='lastName']",   # Last name field
                    "form",              # Any form element
                    "[type='submit']",   # Submit button
                    "[role='button']"    # Button elements
                ]
                
                form_elements_found = 0
                for indicator in form_indicators:
                    try:
                        element = await page.query_selector(indicator)
                        if element:
                            form_elements_found += 1
                    except Exception:
                        continue
                
                if form_elements_found == 0:
                    self.logger.warning(f"⚠️  No form elements detected (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        self.logger.info("🔄 Refreshing page - no form elements found...")
                        await page.reload(wait_until='networkidle', timeout=15000)
                        await page.wait_for_timeout(5000)
                        continue
                    else:
                        self.logger.warning("❌ No form elements found after all retries")
                        # Don't fail completely, might be a different page layout
                
                # Additional stability wait
                await page.wait_for_timeout(2000)
                
                self.logger.success(f"✅ Page appears stable and ready!")
                self.logger.info(f"   📊 Form elements detected: {form_elements_found}")
                return True
                
            except Exception as e:
                self.logger.warning(f"⚠️  Page stability check failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    self.logger.info("🔄 Retrying page stability check...")
                    await page.wait_for_timeout(3000)
                    continue
                else:
                    self.logger.error("❌ Page stability check failed after all retries")
                    return False
        
        return False
        
    async def execute_complete_workflow(self) -> Dict[str, Any]:
        """
        Execute the complete job application automation workflow.
        
        Returns:
            Dictionary containing the workflow execution results
        """
        workflow_result = {
            "workflow_started": True,
            "authentication_successful": False,
            "form_completion_successful": False,
            "workflow_completed": False,
            "errors": []
        }
        
        try:
            # Step 1: Initialize user session
            user_data = await self.initialize_user_session()
            if not user_data:
                workflow_result["errors"].append("Failed to initialize user session")
                return workflow_result
                
            # Step 2: Get user authentication choice
            auth_manager = AuthenticationManager()
            user_choice = await auth_manager.get_user_authentication_choice()
            self.logger.info(f"User selected authentication method: {user_choice.upper()}")
            
            # Step 3: Initialize browser session
            browser_manager = BrowserManager(self.config)
            async with browser_manager.get_browser_context() as (browser, page):
                
                # Step 4: Navigate to target application
                navigation_success = await browser_manager.navigate_to_application(
                    page, 
                    user_data['personal_information']['email'],
                    user_data['personal_information']['password']
                )
                
                if not navigation_success:
                    workflow_result["errors"].append("Failed to navigate to application")
                    return workflow_result
                
                # Step 5: Execute authentication workflow
                auth_success = await self.execute_authentication_workflow(
                    page, 
                    user_choice,
                    {
                        'email': user_data['personal_information']['email'],
                        'password': user_data['personal_information']['password']
                    }
                )
                
                workflow_result["authentication_successful"] = auth_success
                
                if not auth_success:
                    workflow_result["errors"].append(f"{user_choice} authentication failed")
                    return workflow_result
                
                self.logger.success(f"✅ {user_choice} authentication completed successfully")
                
                # Step 6: Execute my information form workflow
                self.logger.info("Proceeding to my information form completion...")
                form_success = await self.execute_my_information_form_workflow(page, user_data)
                
                workflow_result["form_completion_successful"] = form_success
                
                if not form_success:
                    workflow_result["errors"].append("My information form completion failed")
                    self.logger.warning("⚠️ My information form completion failed, but authentication was successful")
                else:
                    self.logger.success("✅ My information form completion completed successfully")
                
                # Mark workflow as completed if authentication succeeded (form completion is optional)
                workflow_result["workflow_completed"] = True
                
                # Optional: Wait a bit to see final state
                self.logger.info("Workflow completed. Waiting 10 seconds before closing...")
                await page.wait_for_timeout(10000)  # 10 seconds
                    
        except Exception as e:
            error_message = f"Workflow execution error: {str(e)}"
            self.logger.error(error_message)
            workflow_result["errors"].append(error_message)
            
        return workflow_result


async def main():
    """
    Main entry point for the job application automation system.
    
    This function initializes the application and executes the complete workflow.
    """
    print("=" * 60)
    print("🤖 Job Application Automation System")
    print("=" * 60)
    
    # Initialize the automator
    automator = JobApplicationAutomator()
    
    try:
        # Execute the complete workflow
        results = await automator.execute_complete_workflow()
        
        # Save and display results
        await automator.result_manager.save_workflow_results(results)
        automator.result_manager.display_workflow_summary(results)
        
        # Determine exit status
        if results.get("workflow_completed", False):
            print("\n🎉 Workflow completed successfully!")
            return 0
        else:
            print("\n❌ Workflow completed with errors.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Workflow interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n💥 Critical error: {str(e)}")
        return 1


if __name__ == "__main__":
    """
    Entry point when script is run directly.
    
    To run this application:
    1. Navigate to the jobauto_main directory
    2. Execute: python -m src.main
    """
    exit_code = asyncio.run(main())
    exit(exit_code)
