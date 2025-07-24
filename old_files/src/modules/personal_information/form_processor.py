"""
Form Processor Module

This module handles processing and filling of various types of forms,
particularly personal information forms after authentication.

Author: Job Automation Team
Date: July 23, 2025
"""

import asyncio
from typing import Dict, Any, List, Optional
from playwright.async_api import Page

from src.utils.logger import ApplicationLogger
from src.utils.form_extractor import FormExtractor
from src.utils.form_logger import FormDataLogger


class FormProcessor:
    """
    Processes and fills various types of forms with user data.
    
    This class handles the detection, analysis, and completion of forms
    with appropriate user information based on form field types.
    """
    
    def __init__(self, page: Page, logger: ApplicationLogger):
        """
        Initialize the form processor.
        
        Args:
            page: Playwright page instance
            logger: Application logger instance
        """
        self.page = page
        self.logger = logger
        self.form_extractor = FormExtractor(page, logger)
        self.form_data_logger = FormDataLogger(logger)
    
    async def log_initial_form_state(self, form_type: str):
        """
        Log the initial state of forms on the current page.
        
        Args:
            form_type: Type of form being processed
        """
        try:
            self.logger.workflow_step(f"Form State Logging - {form_type}", "STARTED")
            
            form_elements = await self.form_extractor.extract_all_form_elements()
            
            await self.form_data_logger.log_form_elements(
                form_elements,
                f"{form_type}_initial_state",
                {
                    "description": f"Form elements found before {form_type} processing",
                    "action_about_to_perform": f"fill_{form_type}",
                    "page_url": self.page.url,
                    "page_title": await self.page.title()
                }
            )
            
            self.logger.workflow_step(
                f"Form State Logging - {form_type}",
                "COMPLETED",
                elements_found=len(form_elements)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log initial form state for {form_type}", exception=e)
    
    async def _verify_page_ready_for_form_processing(self) -> bool:
        """
        Verify that the page is ready for form processing by checking for errors and required elements.
        
        Returns:
            True if page is ready, False if errors detected or page not ready
        """
        try:
            self.logger.info("🔍 Verifying page readiness for form processing...")
            
            # Get current page info
            current_url = self.page.url
            page_title = await self.page.title()
            
            self.logger.info(f"   📍 URL: {current_url}")
            self.logger.info(f"   📋 Title: {page_title}")
            
            # Check for error messages on the page
            error_indicators = [
                "something went wrong",
                "something is wrong", 
                "error occurred",
                "page not found",
                "service unavailable",
                "temporarily unavailable",
                "please try again",
                "oops",
                "unable to process",
                "session expired",
                "access denied"
            ]
            
            # Get page text content
            try:
                page_text = await self.page.text_content('body') if await self.page.query_selector('body') else ""
                page_text_lower = page_text.lower() if page_text else ""
                
                # Check for error indicators
                errors_found = []
                for indicator in error_indicators:
                    if indicator in page_text_lower:
                        errors_found.append(indicator)
                
                if errors_found:
                    self.logger.warning("🚨 Error indicators found on page:")
                    for error in errors_found:
                        self.logger.warning(f"   ⚠️  '{error}'")
                    return False
                
            except Exception as e:
                self.logger.warning(f"Could not check page text for errors: {e}")
            
            # Check for presence of form elements that indicate the page is ready
            required_elements = [
                "form",              # Any form
                "input",             # Input fields
                "[role='button']",   # Button elements
                "button",            # Button elements
                "select"             # Select dropdowns
            ]
            
            elements_found = 0
            for selector in required_elements:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        elements_found += len(elements)
                except Exception:
                    continue
            
            if elements_found == 0:
                self.logger.warning("⚠️  No form elements found on page")
                return False
            
            self.logger.success(f"✅ Page ready for form processing ({elements_found} elements found)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying page readiness: {e}")
            return False
    
    async def process_personal_information_form(self, user_data: Dict[str, Any]) -> bool:
        """
        Process and fill personal information forms with error detection and recovery.
        
        Args:
            user_data: Complete user data dictionary
            
        Returns:
            True if form processing successful, False otherwise
        """
        try:
            self.logger.workflow_step("Personal Information Form Processing", "STARTED")
            
            # Check for page errors before proceeding
            page_ready = await self._verify_page_ready_for_form_processing()
            if not page_ready:
                self.logger.warning("⚠️  Page not ready for form processing, attempting recovery...")
                # Try to refresh and check again
                await self.page.reload(wait_until='networkidle', timeout=15000)
                await self.page.wait_for_timeout(3000)
                page_ready = await self._verify_page_ready_for_form_processing()
                if not page_ready:
                    self.logger.error("❌ Page still not ready after refresh")
                    return False
            
            # Extract form elements
            form_elements = await self.form_extractor.extract_all_form_elements()
            
            if not form_elements:
                self.logger.warning("No form elements found on personal information page")
                return False
            
            # Get personal information from user data
            personal_info = user_data.get('personal_information', {})
            if not personal_info:
                self.logger.error("No personal information found in user data")
                return False
            
            # TEMPORARY FIX: Check if name field is already filled and skip to submit if so
            name_already_filled = await self._check_if_name_already_filled(form_elements)
            if name_already_filled:
                self.logger.success("✅ Name field already filled - skipping form filling and going to submit")
                success = await self._submit_form_if_needed(form_elements)
                status = "COMPLETED" if success else "FAILED"
                self.logger.workflow_step("Personal Information Form Processing", status)
                return success
            
            # Process different types of form fields
            success = await self._fill_personal_information_fields(form_elements, personal_info)
            
            if success:
                # Submit the form if needed
                success = await self._submit_form_if_needed(form_elements)
            
            status = "COMPLETED" if success else "FAILED"
            self.logger.workflow_step("Personal Information Form Processing", status)
            
            return success
            
        except Exception as e:
            self.logger.error("Personal information form processing failed", exception=e)
            return False
    
    async def _check_if_name_already_filled(self, form_elements: List[Dict[str, Any]]) -> bool:
        """
        Quick check to see if the first name field is already filled.
        
        Args:
            form_elements: List of form elements
            
        Returns:
            True if name field has content, False otherwise
        """
        try:
            self.logger.info("🔍 Checking if name field is already filled...")
            
            # Look for the first name field specifically
            for element in form_elements:
                if (element.get('element_type') == 'input' and 
                    element.get('id') == 'name--legalName--firstName'):
                    
                    selector = element.get('selector')
                    if selector:
                        try:
                            current_value = await self.page.input_value(selector)
                            if current_value and current_value.strip():
                                self.logger.info(f"✅ Name field already filled with: '{current_value.strip()}'")
                                return True
                        except Exception as e:
                            self.logger.debug(f"Error checking name field value: {e}")
                            
            self.logger.info("📝 Name field is empty - proceeding with form filling")
            return False
            
        except Exception as e:
            self.logger.error("Error checking if name field is filled", exception=e)
            return False
    
    async def _fill_personal_information_fields(
        self, 
        form_elements: List[Dict[str, Any]], 
        personal_info: Dict[str, Any]
    ) -> bool:
        """
        Fill personal information fields in the correct order.
        
        Args:
            form_elements: List of form elements
            personal_info: Personal information dictionary
            
        Returns:
            True if filling successful, False otherwise
        """
        try:
            filled_count = 0
            total_fillable = 0
            
            # Fill fields in the specific order required by the form
            self.logger.info("Starting personal information form filling in correct order...")
            
            # Step 1: Handle "Have you previously worked for NVIDIA" radio button
            await self._handle_previous_worker_question(form_elements)
            
            # Step 1.5: Handle "How Did You Hear About Us?" multiselect (if present)
            await self._handle_how_did_you_hear_multiselect(form_elements, personal_info)
            
            # Step 2: Handle country dropdown (should select United States)
            country_success = await self._handle_country_dropdown(form_elements, personal_info)
            if country_success:
                filled_count += 1
            total_fillable += 1
            
            # Step 3: Fill name fields
            name_success = await self._fill_name_fields(form_elements, personal_info)
            filled_count += name_success[0]
            total_fillable += name_success[1]
            
            # Step 4: Fill address fields
            address_success = await self._fill_address_fields(form_elements, personal_info)
            filled_count += address_success[0]
            total_fillable += address_success[1]
            
            # Step 5: Handle phone type dropdown
            phone_type_success = await self._handle_phone_type_dropdown(form_elements)
            if phone_type_success:
                filled_count += 1
            total_fillable += 1
            
            # Step 6: Handle country phone code (complex multiselect)
            phone_code_success = await self._handle_country_phone_code(form_elements, personal_info)
            if phone_code_success:
                filled_count += 1
            total_fillable += 1
            
            # Step 7: Fill phone number
            phone_success = await self._fill_phone_number(form_elements, personal_info)
            if phone_success:
                filled_count += 1
            total_fillable += 1
            
            # Step 8: Fill any remaining fields
            remaining_success = await self._fill_remaining_fields(form_elements, personal_info)
            filled_count += remaining_success[0]
            total_fillable += remaining_success[1]
            
            self.logger.info(
                f"Form filling completed",
                filled_fields=filled_count,
                total_fillable_fields=total_fillable,
                success_rate=f"{(filled_count/total_fillable*100):.1f}%" if total_fillable > 0 else "0%"
            )
            
            # Consider successful if we filled at least 50% of fields
            return total_fillable == 0 or (filled_count / total_fillable) >= 0.5
            
        except Exception as e:
            self.logger.error("Error filling personal information fields", exception=e)
            return False
    
    async def _handle_previous_worker_question(self, form_elements: List[Dict[str, Any]]) -> bool:
        """Handle the 'Have you previously worked for NVIDIA' radio button."""
        try:
            self.logger.info("Handling previous worker question...")
            
            for element in form_elements:
                if (element.get('element_type') == 'input' and 
                    element.get('type_of_input') == 'radio' and
                    'candidateIsPreviousWorker' in element.get('name', '')):
                    
                    # Select "No" by default (value="false")
                    if element.get('value') == 'false':
                        selector = element.get('selector')
                        if selector:
                            self.logger.info(f"🔘 CLICKING RADIO BUTTON (No): {selector}")
                            await self.page.click(selector)
                            await self.page.wait_for_timeout(500)
                            self.logger.success("✅ Selected 'No' for previous worker question")
                            return True
            
            self.logger.warning("❌ Previous worker radio button not found")
            return False
            
        except Exception as e:
            self.logger.error("Error handling previous worker question", exception=e)
            return False
    
    async def _handle_how_did_you_hear_multiselect(self, form_elements, personal_info):
        """Handle the 'How Did You Hear About Us?' multiselect field."""
        try:
            # Look for the "How Did You Hear About Us?" multiselect container
            multiselect_containers = await self.page.query_selector_all('[data-automation-id="multiselectInputContainer"]')
            
            for container in multiselect_containers:
                # Check if this is the "How Did You Hear About Us?" field by looking at the label
                parent = await container.query_selector('xpath=..')
                if parent:
                    # Look for the label text in the parent or nearby elements
                    labels = await parent.query_selector_all('label')
                    for label in labels:
                        label_text = await label.inner_text()
                        if "How Did You Hear" in label_text or "hear about us" in label_text.lower():
                            self.logger.info(f"Found 'How Did You Hear About Us?' multiselect field")
                            
                            # Click the multiselect container to open it
                            await container.click()
                            await self.page.wait_for_timeout(1000)
                            
                            # Check if there's already a selection and clear it
                            existing_selection = await container.query_selector('[data-automation-id="multiselectInputLabel"]')
                            if existing_selection:
                                selection_text = await existing_selection.inner_text()
                                if selection_text and selection_text.strip() != "Select one or more options...":
                                    self.logger.info(f"Found existing selection: {selection_text}. Clearing it.")
                                    # Clear the existing selection
                                    clear_button = await container.query_selector('[data-automation-id="multiselectInputClear"]')
                                    if clear_button:
                                        await clear_button.click()
                                        await self.page.wait_for_timeout(500)
                            
                            # Look for a suitable option to select (e.g., "Job Fair" or "Other")
                            options = await self.page.query_selector_all('[data-automation-id="multiselectOption"]')
                            
                            # Prefer certain options in order
                            preferred_options = ["Job Fair", "Other", "University Career Center", "Referral"]
                            
                            selected = False
                            for preferred in preferred_options:
                                for option in options:
                                    option_text = await option.inner_text()
                                    if preferred.lower() in option_text.lower():
                                        self.logger.info(f"Selecting option: {option_text}")
                                        await option.click()
                                        await self.page.wait_for_timeout(500)
                                        selected = True
                                        break
                                if selected:
                                    break
                            
                            # If no preferred option found, select the first available option
                            if not selected and options:
                                first_option = options[0]
                                option_text = await first_option.inner_text()
                                self.logger.info(f"Selecting first available option: {option_text}")
                                await first_option.click()
                                await self.page.wait_for_timeout(500)
                            
                            # Click outside to close the dropdown
                            await self.page.click('body')
                            await self.page.wait_for_timeout(500)
                            
                            return
            
            self.logger.info("'How Did You Hear About Us?' multiselect field not found")
            
        except Exception as e:
            self.logger.error(f"Error handling 'How Did You Hear About Us?' multiselect: {str(e)}")
    
    async def _handle_country_dropdown(self, form_elements: List[Dict[str, Any]], personal_info: Dict[str, Any]) -> bool:
        """Handle the country dropdown selection."""
        try:
            self.logger.info("Handling country dropdown...")
            
            for element in form_elements:
                if (element.get('element_type') == 'button' and 
                    element.get('name') == 'country' and
                    element.get('id') == 'country--country'):
                    
                    target_country = personal_info.get('address', {}).get('country', 'United States')
                    return await self._handle_dropdown_button(element, personal_info)
            
            self.logger.warning("Country dropdown button not found")
            return False
            
        except Exception as e:
            self.logger.error("Error handling country dropdown", exception=e)
            return False
    
    async def _fill_name_fields(self, form_elements: List[Dict[str, Any]], personal_info: Dict[str, Any]) -> tuple:
        """Fill name fields (first name, last name)."""
        try:
            self.logger.info("Filling name fields...")
            filled = 0
            total = 0
            
            name_mappings = {
                'name--legalName--firstName': personal_info.get('first_name', ''),
                'name--legalName--lastName': personal_info.get('last_name', '')
            }
            
            for element in form_elements:
                if element.get('element_type') == 'input':
                    element_id = element.get('id', '')
                    if element_id in name_mappings:
                        total += 1
                        value = name_mappings[element_id]
                        if value:
                            success = await self._fill_form_field_safe(element, value)
                            if success:
                                filled += 1
            
            self.logger.info(f"Name fields: {filled}/{total} filled")
            return (filled, total)
            
        except Exception as e:
            self.logger.error("Error filling name fields", exception=e)
            return (0, 0)
    
    async def _fill_address_fields(self, form_elements: List[Dict[str, Any]], personal_info: Dict[str, Any]) -> tuple:
        """Fill address fields."""
        try:
            self.logger.info("Filling address fields...")
            filled = 0
            total = 0
            
            address_info = personal_info.get('address', {})
            
            # Use actual user data or defaults
            address_mappings = {
                'address--addressLine1': address_info.get('street', '') or '123 Main Street',  # Default if empty
                'address--city': address_info.get('city', '') or 'San Francisco',
                'address--postalCode': address_info.get('zipcode', '') or '94102'
            }
            
            for element in form_elements:
                if element.get('element_type') == 'input':
                    element_id = element.get('id', '')
                    element_name = element.get('name', '')
                    
                    # Check both ID and name for address fields
                    for field_key, field_value in address_mappings.items():
                        if (field_key in element_id or 
                            any(part in element_name for part in field_key.split('--'))):
                            total += 1
                            if field_value:
                                self.logger.info(f"📝 FILLING ADDRESS FIELD: {element_id} = '{field_value}'")
                                success = await self._fill_form_field_safe(element, field_value)
                                if success:
                                    filled += 1
                            break
            
            self.logger.info(f"Address fields: {filled}/{total} filled")
            return (filled, total)
            
        except Exception as e:
            self.logger.error("Error filling address fields", exception=e)
            return (0, 0)
    
    async def _handle_phone_type_dropdown(self, form_elements: List[Dict[str, Any]]) -> bool:
        """Handle the phone type dropdown selection."""
        try:
            self.logger.info("Handling phone type dropdown...")
            
            for element in form_elements:
                if (element.get('element_type') == 'button' and 
                    element.get('name') == 'phoneType' and
                    'phoneNumber--phoneType' in element.get('id', '')):
                    
                    selector = element.get('selector')
                    if selector:
                        self.logger.info(f"🔄 CLICKING PHONE TYPE DROPDOWN: {selector}")
                        # Click to open dropdown
                        await self.page.click(selector)
                        await self.page.wait_for_timeout(1500)
                        
                        # Look for "Home" option specifically
                        home_option_selectors = [
                            'li[role="option"]:has-text("Home")',
                            'div:has-text("Home")',
                            '[data-value*="0c40f6bd1d8f10adf2900b7a81fc435a"]',
                            'li[data-value="0c40f6bd1d8f10adf2900b7a81fc435a"]'
                        ]
                        
                        for option_selector in home_option_selectors:
                            try:
                                option = await self.page.query_selector(option_selector)
                                if option and await option.is_visible():
                                    self.logger.info(f"🎯 CLICKING HOME OPTION: {option_selector}")
                                    await option.click()
                                    await self.page.wait_for_timeout(500)
                                    self.logger.success("✅ Selected 'Home' for phone type")
                                    return True
                            except Exception as e:
                                self.logger.warning(f"Failed to click {option_selector}: {e}")
                                continue
                        
                        # Fallback: try clicking any option containing "Home"
                        try:
                            self.logger.info("🔍 SEARCHING for Home option with XPath...")
                            xpath_home = "//li[@role='option']//div[text()='Home']"
                            home_elements = await self.page.query_selector_all(f"xpath={xpath_home}")
                            if home_elements:
                                self.logger.info(f"🎯 CLICKING HOME via XPath")
                                await home_elements[0].click()
                                await self.page.wait_for_timeout(500)
                                self.logger.success("✅ Selected 'Home' via XPath")
                                return True
                        except Exception as e:
                            self.logger.warning(f"XPath fallback failed: {e}")
            
            self.logger.warning("❌ Phone type dropdown not found or Home option not available")
            return False
            
        except Exception as e:
            self.logger.error("Error handling phone type dropdown", exception=e)
            return False
    
    async def _handle_country_phone_code(self, form_elements: List[Dict[str, Any]], personal_info: Dict[str, Any]) -> bool:
        """Handle the complex country phone code multiselect input."""
        try:
            self.logger.info("Handling country phone code selection...")
            
            # Look for the specific multiselect input container for phone code
            phone_code_selector = "[data-automation-id='multiselectInputContainer']:has([data-automation-label*='Country Phone Code'])"
            
            # Fallback selectors
            fallback_selectors = [
                "#phoneNumber--countryPhoneCode",
                "[data-automation-id='multiselectInputContainer']",
            ]
            
            element_found = False
            active_selector = None
            
            # Try primary selector first
            try:
                element_exists = await self.page.query_selector(phone_code_selector)
                if element_exists:
                    active_selector = phone_code_selector
                    element_found = True
                    self.logger.info(f"📱 FOUND PHONE CODE MULTISELECT: {phone_code_selector}")
            except Exception:
                pass
            
            # Try fallback selectors
            if not element_found:
                for selector in fallback_selectors:
                    try:
                        element_exists = await self.page.query_selector(selector)
                        if element_exists:
                            active_selector = selector
                            element_found = True
                            self.logger.info(f"📱 FOUND PHONE CODE INPUT: {selector}")
                            break
                    except Exception:
                        continue
            
            if not element_found:
                self.logger.warning("❌ Country phone code input not found")
                return False
            
            # Check if there's already a selection and clear it if it's not US
            try:
                phone_code_container = await self.page.query_selector(active_selector)
                if phone_code_container:
                    # Look for selected items within the container
                    current_selection = await phone_code_container.query_selector('[data-automation-id="selectedItem"]')
                    if current_selection:
                        selection_text = await current_selection.text_content() or ""
                        self.logger.info(f"🔍 CURRENT PHONE CODE SELECTION: '{selection_text}'")
                        
                        # Only clear if it's not already US
                        if ("united states" not in selection_text.lower() and "+1" not in selection_text):
                            delete_charm = await current_selection.query_selector('[data-automation-id="DELETE_charm"]')
                            if delete_charm:
                                self.logger.info(f"🗑️ CLEARING NON-US PHONE CODE SELECTION: '{selection_text}'")
                                await delete_charm.click()
                                await self.page.wait_for_timeout(800)
                        else:
                            self.logger.info("✅ US phone code already selected, skipping")
                            if "+1" in selection_text or "united states" in selection_text.lower():
                                return True
            except Exception as e:
                self.logger.debug(f"Error checking existing selection: {e}")
            
            # Click the input field to open dropdown
            self.logger.info(f"🔄 CLICKING PHONE CODE INPUT: {active_selector}")
            await self.page.click(active_selector)
            await self.page.wait_for_timeout(1000)
            
            # Type "United States" to search
            self.logger.info("⌨️ TYPING 'United States' in phone code search...")
            await self.page.fill(active_selector, "United States")
            await self.page.wait_for_timeout(2000)
            
            # Look for United States option in dropdown
            us_option_selectors = [
                '[data-automation-id="promptOption"]:has-text("United States (+1)")',
                '[data-automation-id="promptOption"]:has-text("United States")',
                'text="United States (+1)"',
                'text="United States"',
                '[data-automation-label*="United States"]',
                '[title*="United States"]'
            ]
            
            for selector in us_option_selectors:
                try:
                    self.logger.info(f"🔍 SEARCHING FOR US PHONE CODE OPTION: {selector}")
                    option = await self.page.query_selector(selector)
                    if option and await option.is_visible():
                        option_text = await option.text_content() or ""
                        if "+" in option_text or "phone" in option_text.lower() or len(option_text) < 30:
                            self.logger.info(f"🎯 CLICKING US PHONE CODE OPTION: {selector} - '{option_text}'")
                            await option.click()
                            await self.page.wait_for_timeout(800)
                            self.logger.success("✅ Selected United States (+1) for country phone code")
                            return True
                        else:
                            self.logger.info(f"⏭️ SKIPPING non-phone option: '{option_text}'")
                except Exception as e:
                    self.logger.warning(f"Failed with selector {selector}: {e}")
                    continue
            
            # Fallback: use XPath to find United States with phone code context
            try:
                self.logger.info("🔍 TRYING XPATH for United States phone code...")
                xpath_selectors = [
                    "//div[contains(text(), 'United States') and contains(text(), '+1')]",
                    "//div[contains(text(), 'United States') and string-length(text()) < 30]",
                    "//p[contains(text(), 'United States (+1)')]"
                ]
                
                for xpath in xpath_selectors:
                    us_elements = await self.page.query_selector_all(f"xpath={xpath}")
                    if us_elements:
                        self.logger.info(f"🎯 CLICKING US phone code via XPath: {xpath}")
                        await us_elements[0].click()
                        await self.page.wait_for_timeout(800)
                        self.logger.success("✅ Selected United States phone code via XPath")
                        return True
            except Exception as e:
                self.logger.warning(f"XPath fallback failed: {e}")
            
            # Final fallback: press Enter to select first match
            self.logger.info("⏎ PRESSING ENTER as final fallback for phone code...")
            await self.page.press(active_selector, "Enter")
            await self.page.wait_for_timeout(800)
            self.logger.info("✅ Used Enter key to select country phone code")
            return True
            
        except Exception as e:
            self.logger.error("Error handling country phone code", exception=e)
            return False
    
    async def _fill_phone_number(self, form_elements: List[Dict[str, Any]], personal_info: Dict[str, Any]) -> bool:
        """Fill the phone number field."""
        try:
            self.logger.info("Filling phone number...")
            
            phone_number = personal_info.get('phone', '')
            if not phone_number:
                self.logger.warning("No phone number found in user data")
                return False
            
            for element in form_elements:
                if (element.get('element_type') == 'input' and 
                    element.get('name') == 'phoneNumber' and
                    element.get('id') == 'phoneNumber--phoneNumber'):
                    
                    success = await self._fill_form_field_safe(element, phone_number)
                    if success:
                        self.logger.success(f"Phone number filled: {phone_number}")
                        return True
            
            self.logger.warning("Phone number field not found")
            return False
            
        except Exception as e:
            self.logger.error("Error filling phone number", exception=e)
            return False
    
    async def _fill_remaining_fields(self, form_elements: List[Dict[str, Any]], personal_info: Dict[str, Any]) -> tuple:
        """Fill any remaining fields that weren't handled in the specific steps."""
        try:
            self.logger.info("Filling remaining fields...")
            filled = 0
            total = 0
            
            # Fields already handled - skip these
            handled_fields = {
                'candidateIsPreviousWorker',  # radio buttons
                'country',  # country dropdown
                'name--legalName--firstName',  # first name
                'name--legalName--lastName',   # last name
                'address--addressLine1',       # address
                'address--city',              # city
                'address--postalCode',        # postal code
                'phoneType',                  # phone type dropdown
                'phoneNumber--countryPhoneCode',  # country phone code
                'phoneNumber--phoneNumber'    # phone number
            }
            
            for element in form_elements:
                element_type = element.get('element_type', '')
                if element_type not in ['input', 'select', 'textarea']:
                    continue
                
                # Skip buttons and already handled fields
                input_type = element.get('type_of_input', '').lower()
                if input_type in ['submit', 'button', 'reset', 'radio']:
                    continue
                
                element_id = element.get('id', '')
                element_name = element.get('name', '')
                
                # Skip if already handled
                if (element_id in handled_fields or 
                    element_name in handled_fields or
                    any(handled in element_id for handled in handled_fields) or
                    any(handled in element_name for handled in handled_fields)):
                    continue
                
                total += 1
                
                # Try to determine value for this field
                value_to_fill = self._determine_field_value(element, personal_info)
                
                if value_to_fill is not None:
                    success = await self._fill_form_field_safe(element, value_to_fill)
                    if success:
                        filled += 1
            
            self.logger.info(f"Remaining fields: {filled}/{total} filled")
            return (filled, total)
            
        except Exception as e:
            self.logger.error("Error filling remaining fields", exception=e)
            return (0, 0)
    
    async def _is_dropdown_button(self, element: Dict[str, Any]) -> bool:
        """
        Check if a button element is a dropdown trigger.
        
        Args:
            element: Button element information
            
        Returns:
            True if this appears to be a dropdown button, False otherwise
        """
        try:
            # Check for aria-haspopup attribute (from extracted data)
            aria_haspopup = element.get('aria_haspopup', '')
            if aria_haspopup in ['listbox', 'menu', 'true']:
                return True
            
            # If not captured in extraction, check directly
            selector = element.get('selector')
            if selector:
                try:
                    aria_haspopup_direct = await self.page.get_attribute(selector, 'aria-haspopup')
                    if aria_haspopup_direct in ['listbox', 'menu', 'true']:
                        return True
                except Exception:
                    pass
            
            # Check for common dropdown patterns in name/id
            name = element.get('name', '').lower()
            element_id = element.get('id', '').lower()
            label = element.get('label', '').lower()
            
            # Common dropdown field patterns
            dropdown_patterns = ['country', 'state', 'province', 'region', 'phone type', 'device type']
            
            field_text = f"{name} {element_id} {label}".lower()
            
            return any(pattern in field_text for pattern in dropdown_patterns)
            
        except Exception as e:
            self.logger.warning("Error checking if button is dropdown", exception=e)
            return False
    
    async def _handle_dropdown_button(
        self, 
        element: Dict[str, Any], 
        personal_info: Dict[str, Any]
    ) -> bool:
        """
        Handle clicking and selecting from a dropdown button.
        
        Args:
            element: Button element information
            personal_info: Personal information dictionary
            
        Returns:
            True if selection successful, False otherwise
        """
        try:
            selector = element.get('selector')
            if not selector:
                return False
            
            name = element.get('name', '').lower()
            label = element.get('label', '').lower()
            element_id = element.get('id', '').lower()
            
            # Determine what value we want to select
            target_value = None
            
            # Handle country selection
            if 'country' in f"{name} {label} {element_id}":
                target_value = personal_info.get('address', {}).get('country', '')
                if not target_value:
                    target_value = personal_info.get('country', '')
            
            # Handle state/province selection
            elif any(term in f"{name} {label} {element_id}" for term in ['state', 'province', 'region']):
                target_value = personal_info.get('address', {}).get('state', '')
                if not target_value:
                    target_value = personal_info.get('state', '')
            
            # Handle phone type selection
            elif 'phone' in f"{name} {label} {element_id}" and 'type' in f"{name} {label} {element_id}":
                target_value = 'Mobile'  # Default to mobile
            
            if not target_value:
                self.logger.debug(f"❌ No target value determined for dropdown: {label}")
                return False
            
            # Log the interaction
            self.logger.info(f"🔄 CLICKING DROPDOWN BUTTON: {label} ({selector})")
            self.logger.info(f"   🎯 Target value: '{target_value}'")
            
            # Click the dropdown button to open it
            await self.page.click(selector)
            await self.page.wait_for_timeout(800)  # Wait for dropdown to open
            
            # Look for dropdown options
            success = await self._select_dropdown_option(target_value, element)
            
            if success:
                self.logger.success(f"✅ Successfully selected '{target_value}' from dropdown: {label}")
                
                # Log the interaction
                await self.form_data_logger.log_user_interaction(
                    "DROPDOWN_SELECT",
                    element,
                    target_value,
                    True
                )
            else:
                self.logger.warning(f"❌ Failed to select '{target_value}' from dropdown: {label}")
                
                # Log the failed interaction
                await self.form_data_logger.log_user_interaction(
                    "DROPDOWN_SELECT",
                    element,
                    target_value,
                    False
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error handling dropdown button: {element.get('label', 'Unknown')}", exception=e)
            return False
    
    async def _select_dropdown_option(self, target_value: str, dropdown_element: Dict[str, Any]) -> bool:
        """
        Select an option from an opened dropdown.
        
        Args:
            target_value: The value we want to select
            dropdown_element: The dropdown button element information
            
        Returns:
            True if selection successful, False otherwise
        """
        try:
            # Common selectors for dropdown options
            option_selectors = [
                'div[role="option"]',
                'li[role="option"]',
                '[data-automation-id*="option"]',
                '.css-option',
                '[role="listbox"] div',
                '[role="listbox"] li'
            ]
            
            # Wait a bit for options to load
            await self.page.wait_for_timeout(1000)
            
            for selector in option_selectors:
                try:
                    options = await self.page.query_selector_all(selector)
                    if not options:
                        continue
                    
                    for option in options:
                        try:
                            option_text = await option.text_content()
                            if not option_text:
                                continue
                            
                            option_text = option_text.strip()
                            
                            # Check if this option matches our target value
                            if self._option_matches_target(option_text, target_value):
                                await option.click()
                                await self.page.wait_for_timeout(500)
                                self.logger.debug(f"Selected option: {option_text}")
                                return True
                                
                        except Exception:
                            continue
                            
                except Exception:
                    continue
            
            # If no exact match found, try partial matching
            return await self._select_dropdown_option_partial_match(target_value)
            
        except Exception as e:
            self.logger.warning("Error selecting dropdown option", exception=e)
            return False
    
    async def _select_dropdown_option_partial_match(self, target_value: str) -> bool:
        """
        Attempt to select dropdown option using partial matching.
        
        Args:
            target_value: The value we want to select
            
        Returns:
            True if selection successful, False otherwise
        """
        try:
            # Try clicking on text that contains our target value
            target_lower = target_value.lower()
            
            # Use XPath to find text containing our target
            xpath_selectors = [
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_lower}')]",
                f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_lower}')]",
                f"//li[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_lower}')]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elements = await self.page.query_selector_all(f"xpath={xpath}")
                    if elements:
                        for element in elements[:3]:  # Try first 3 matches
                            try:
                                await element.click()
                                await self.page.wait_for_timeout(500)
                                self.logger.debug(f"Selected option using partial match for: {target_value}")
                                return True
                            except Exception:
                                continue
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.warning("Error in partial match selection", exception=e)
            return False
    
    def _option_matches_target(self, option_text: str, target_value: str) -> bool:
        """
        Check if an option text matches the target value.
        
        Args:
            option_text: Text of the dropdown option
            target_value: Target value we want to select
            
        Returns:
            True if they match, False otherwise
        """
        try:
            option_lower = option_text.lower().strip()
            target_lower = target_value.lower().strip()
            
            # Exact match
            if option_lower == target_lower:
                return True
            
            # Handle common country name variations
            country_mappings = {
                'united states': ['usa', 'us', 'america', 'united states of america'],
                'united kingdom': ['uk', 'britain', 'great britain', 'england'],
                'canada': ['ca'],
                'australia': ['au'],
                'germany': ['de', 'deutschland'],
                'france': ['fr'],
                'italy': ['it'],
                'spain': ['es'],
                'japan': ['jp'],
                'china': ['cn'],
                'india': ['in']
            }
            
            # Check if target matches any known variations
            for full_name, variations in country_mappings.items():
                if target_lower in [full_name] + variations:
                    if option_lower in [full_name] + variations:
                        return True
                    if any(var in option_lower for var in [full_name] + variations):
                        return True
            
            # Check if target is contained in option or vice versa
            if target_lower in option_lower or option_lower in target_lower:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _determine_field_value(
        self, 
        element: Dict[str, Any], 
        personal_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        Determine what value should be filled in a field based on its characteristics.
        
        Args:
            element: Form element information
            personal_info: Personal information dictionary
            
        Returns:
            Value to fill or None if no appropriate value found
        """
        try:
            label = element.get('label', '').lower()
            name = element.get('name', '').lower()
            placeholder = element.get('placeholder', '').lower()
            input_type = element.get('type_of_input', '').lower()
            
            # Combine all text clues
            field_text = f"{label} {name} {placeholder}".lower()
            
            # Map field patterns to data
            field_mappings = {
                # Basic personal info
                'name': ['name', 'full name', 'fullname', 'first name', 'lastname', 'last name'],
                'email': ['email', 'e-mail', 'email address'],
                'phone': ['phone', 'telephone', 'mobile', 'cell'],
                
                # Address fields
                'address': ['address', 'street', 'street address'],
                'city': ['city', 'town'],
                'state': ['state', 'province', 'region'],
                'zipcode': ['zip', 'postal', 'postcode', 'zip code', 'postal code'],
                'country': ['country', 'nation'],
                
                # Professional info
                'current_position': ['position', 'job title', 'title', 'occupation', 'role'],
                'years_of_experience': ['experience', 'years', 'years of experience'],
                
                # Other common fields
                'first_name': ['first name', 'firstname', 'given name'],
                'last_name': ['last name', 'lastname', 'surname', 'family name'],
            }
            
            # Special handling for specific input types
            if input_type == 'email':
                return personal_info.get('email', '')
            elif input_type == 'tel':
                return personal_info.get('phone', '')
            elif input_type == 'url':
                return personal_info.get('website', '')
            
            # Check for field patterns
            for data_key, patterns in field_mappings.items():
                if any(pattern in field_text for pattern in patterns):
                    value = personal_info.get(data_key)
                    if value:
                        return str(value)
            
            # Check address subdictionary
            address_info = personal_info.get('address', {})
            if isinstance(address_info, dict):
                for data_key, patterns in field_mappings.items():
                    if any(pattern in field_text for pattern in patterns):
                        value = address_info.get(data_key)
                        if value:
                            return str(value)
            
            # Check professional info subdictionary
            prof_info = personal_info.get('professional_info', {})
            if isinstance(prof_info, dict):
                for data_key, patterns in field_mappings.items():
                    if any(pattern in field_text for pattern in patterns):
                        value = prof_info.get(data_key)
                        if value:
                            return str(value)
            
            # Special handling for select fields
            if element.get('element_type') == 'select':
                return self._handle_select_field(element, personal_info)
            
            self.logger.debug(
                f"No matching value found for field",
                label=element.get('label', 'Unknown'),
                name=element.get('name', ''),
                type=input_type
            )
            
            return None
            
        except Exception as e:
            self.logger.warning("Error determining field value", exception=e)
            return None
    
    def _handle_select_field(
        self, 
        element: Dict[str, Any], 
        personal_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        Handle special logic for select dropdown fields.
        
        Args:
            element: Select element information
            personal_info: Personal information dictionary
            
        Returns:
            Option value to select or None
        """
        try:
            options = element.get('options', [])
            if not options:
                return None
            
            label = element.get('label', '').lower()
            
            # Handle country selection
            if 'country' in label:
                user_country = personal_info.get('address', {}).get('country', '')
                if user_country:
                    for option in options:
                        option_text = option.get('text', '').lower()
                        if user_country.lower() in option_text:
                            return option.get('value', '')
            
            # Handle state/province selection
            if 'state' in label or 'province' in label:
                user_state = personal_info.get('address', {}).get('state', '')
                if user_state:
                    for option in options:
                        option_text = option.get('text', '').lower()
                        if user_state.lower() in option_text:
                            return option.get('value', '')
            
            # For other selects, try to find a reasonable default
            # Skip the first option if it's a placeholder
            if len(options) > 1:
                first_option = options[0]
                if (not first_option.get('value') or 
                    'select' in first_option.get('text', '').lower() or
                    'choose' in first_option.get('text', '').lower()):
                    return options[1].get('value', '')
            
            return None
            
        except Exception as e:
            self.logger.warning("Error handling select field", exception=e)
            return None
    
    async def _fill_form_field_safe(self, element: Dict[str, Any], value: str) -> bool:
        """
        Safely fill a form field with error handling and logging.
        
        Args:
            element: Form element information
            value: Value to fill
            
        Returns:
            True if successful, False otherwise
        """
        try:
            selector = element.get('selector')
            if not selector:
                self.logger.warning("❌ No selector available for form field")
                return False
            
            element_type = element.get('element_type', '')
            input_type = element.get('type_of_input', '')
            label = element.get('label', 'Unknown')
            element_id = element.get('id', '')
            
            self.logger.info(f"📝 FILLING FIELD: {element_type} - {label} (ID: {element_id})")
            self.logger.info(f"   🎯 Selector: {selector}")
            self.logger.info(f"   ✏️  Value: '{value}'")
            
            # Handle different element types
            if element_type == 'select':
                self.logger.info(f"🔄 SELECTING OPTION in dropdown: {selector} = '{value}'")
                await self.page.select_option(selector, value)
            elif element_type == 'button':
                # Handle dropdown buttons
                if await self._is_dropdown_button(element):
                    self.logger.info(f"🔄 HANDLING DROPDOWN BUTTON: {selector}")
                    return await self._handle_dropdown_button(element, {'temp_value': value})
                else:
                    self.logger.warning(f"❌ Button element not recognized as dropdown: {element_type}")
                    return False
            elif element_type in ['input', 'textarea']:
                # Clear and fill
                self.logger.info(f"🧹 CLEARING FIELD: {selector}")
                await self.page.fill(selector, "")
                await self.page.wait_for_timeout(200)
                
                self.logger.info(f"✏️  TYPING VALUE: {selector} = '{value}'")
                await self.page.fill(selector, value)
            else:
                self.logger.warning(f"❌ Unsupported element type for filling: {element_type}")
                return False
            
            # Brief pause for stability
            await self.page.wait_for_timeout(300)
            
            # Log the interaction
            await self.form_data_logger.log_user_interaction(
                "FILL",
                element,
                value,
                True
            )
            
            self.logger.success(f"✅ Successfully filled field: {label} = '{value}'")
            return True
            
        except Exception as e:
            self.logger.warning(
                f"❌ Failed to fill field: {element.get('label', 'Unknown')} - {str(e)}"
            )
            
            # Log the failed interaction
            await self.form_data_logger.log_user_interaction(
                "FILL",
                element,
                value,
                False
            )
            
            return False
    
    async def _submit_form_if_needed(self, form_elements: List[Dict[str, Any]]) -> bool:
        """
        Submit the form by clicking the 'Save and Continue' button.
        
        Args:
            form_elements: List of form elements
            
        Returns:
            True if submission successful or no submit needed, False otherwise
        """
        try:
            self.logger.info("🔍 Looking for 'Save and Continue' button...")
            
            # Find submit button - prioritize "Save and Continue"
            submit_button = None
            best_match_score = 0
            
            for element in form_elements:
                if (element.get('element_type') == 'button' or 
                    element.get('type_of_input') in ['submit', 'button']):
                    
                    label = element.get('label', '').lower()
                    text = element.get('text', '').lower()
                    button_text = f"{label} {text}".strip()
                    
                    self.logger.debug(f"📋 Found button: '{button_text}'")
                    
                    # Score different button types (higher score = better match)
                    score = 0
                    if 'save and continue' in button_text:
                        score = 100  # Perfect match
                    elif 'save' in button_text and 'continue' in button_text:
                        score = 90   # Both words present
                    elif 'continue' in button_text:
                        score = 70   # Continue button
                    elif 'save' in button_text:
                        score = 60   # Save button
                    elif 'next' in button_text:
                        score = 50   # Next button
                    elif 'submit' in button_text:
                        score = 40   # Submit button
                    elif 'send' in button_text:
                        score = 30   # Send button
                    
                    if score > best_match_score:
                        best_match_score = score
                        submit_button = element
                        self.logger.debug(f"🎯 New best match (score {score}): '{button_text}'")
            
            if not submit_button:
                self.logger.warning("❌ No submit/continue button found - form may auto-save")
                return True
            
            # Click submit button
            selector = submit_button.get('selector')
            if not selector:
                self.logger.warning("Submit button found but no selector available")
                return False
            
            button_label = submit_button.get('label', submit_button.get('text', 'Unknown'))
            
            self.logger.info(f"🚀 CLICKING SUBMIT BUTTON: '{button_label}'")
            self.logger.info(f"   🎯 Selector: {selector}")
            self.logger.info(f"   📊 Match score: {best_match_score}")
            
            # Click the button
            await self.page.click(selector)
            
            # Wait for form submission and page transition
            self.logger.info("⏳ Waiting for form submission...")
            await self.page.wait_for_timeout(1000)  # Initial wait
            
            try:
                # Wait for network to settle (page might navigate)
                await self.page.wait_for_load_state('networkidle', timeout=15000)
            except Exception as e:
                self.logger.warning(f"Network wait timeout (normal for navigation): {e}")
            
            # Additional wait for any animations/transitions
            await self.page.wait_for_timeout(2000)
            
            # Log the final state
            final_url = self.page.url
            final_title = await self.page.title()
            
            self.logger.success(f"✅ Form submitted successfully!")
            self.logger.info(f"   📄 Final page: {final_title}")
            self.logger.info(f"   🔗 Final URL: {final_url}")
            
            # Log the interaction
            await self.form_data_logger.log_user_interaction(
                "SUBMIT",
                submit_button,
                f"Clicked {button_label}",
                True
            )
            
            return True
            
        except Exception as e:
            self.logger.error("❌ Form submission failed", exception=e)
            
            # Log the failed interaction
            if submit_button:
                await self.form_data_logger.log_user_interaction(
                    "SUBMIT",
                    submit_button,
                    f"Failed to click {submit_button.get('label', 'button')}",
                    False
                )
            
            return False
    
    async def log_form_completion_result(self, form_type: str, success: bool):
        """
        Log the final form completion result.
        
        Args:
            form_type: Type of form that was processed
            success: Whether processing was successful
        """
        try:
            result_data = {
                "form_type": form_type,
                "success": success,
                "final_url": self.page.url,
                "page_title": await self.page.title(),
                "timestamp": await self._get_current_timestamp()
            }
            
            await self.form_data_logger.log_step_completion(
                f"{form_type}_processing",
                success,
                result_data
            )
            
            if success:
                self.logger.success(f"{form_type.title()} form processing completed successfully")
            else:
                self.logger.failure(f"{form_type.title()} form processing failed")
                
        except Exception as e:
            self.logger.error(f"Failed to log form completion result for {form_type}", exception=e)
    
    async def _get_current_timestamp(self) -> str:
        """Get current timestamp for logging."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
