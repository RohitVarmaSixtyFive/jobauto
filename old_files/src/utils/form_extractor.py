"""
Form Extractor Module

This module handles extraction and analysis of form elements from web pages.
It provides methods to identify form fields, buttons, and other interactive elements.

Author: Job Automation Team
Date: July 23, 2025
"""

from typing import Dict, Any, List, Optional
from playwright.async_api import Page, Locator

from src.utils.logger import ApplicationLogger


class FormExtractor:
    """
    Extracts and analyzes form elements from web pages.
    
    This class provides methods for identifying various types of form elements
    including input fields, buttons, select dropdowns, and more.
    """
    
    def __init__(self, page: Page, logger: ApplicationLogger):
        """
        Initialize the form extractor.
        
        Args:
            page: Playwright page instance
            logger: Application logger instance
        """
        self.page = page
        self.logger = logger
    
    async def extract_all_form_elements(self) -> List[Dict[str, Any]]:
        """
        Extract all form elements from the current page.
        
        Returns:
            List of dictionaries containing form element information
        """
        try:
            self.logger.debug("Starting form element extraction...")
            
            form_elements = []
            
            # Extract different types of form elements
            input_elements = await self._extract_input_elements()
            button_elements = await self._extract_button_elements()
            select_elements = await self._extract_select_elements()
            textarea_elements = await self._extract_textarea_elements()
            dropdown_option_elements = await self._extract_dropdown_option_elements()
            
            # Combine all elements
            form_elements.extend(input_elements)
            form_elements.extend(button_elements)
            form_elements.extend(select_elements)
            form_elements.extend(textarea_elements)
            form_elements.extend(dropdown_option_elements)
            
            self.logger.debug(
                f"Form extraction completed",
                total_elements=len(form_elements),
                inputs=len(input_elements),
                buttons=len(button_elements),
                selects=len(select_elements),
                textareas=len(textarea_elements),
                dropdown_options=len(dropdown_option_elements)
            )
            
            return form_elements
            
        except Exception as e:
            self.logger.error("Failed to extract form elements", exception=e)
            return []
    
    async def _extract_input_elements(self) -> List[Dict[str, Any]]:
        """Extract input form elements."""
        try:
            input_elements = []
            inputs = await self.page.query_selector_all('input')
            
            for i, input_element in enumerate(inputs):
                try:
                    # Skip hidden inputs
                    if not await input_element.is_visible():
                        continue
                    
                    element_info = await self._get_input_element_info(input_element, i)
                    if element_info:
                        input_elements.append(element_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing input element {i}", exception=e)
                    continue
            
            return input_elements
            
        except Exception as e:
            self.logger.error("Error extracting input elements", exception=e)
            return []
    
    async def _extract_button_elements(self) -> List[Dict[str, Any]]:
        """Extract button form elements."""
        try:
            button_elements = []
            
            # Get button elements, input[type=submit/button], and div[role=button]
            buttons = await self.page.query_selector_all('button, input[type="submit"], input[type="button"], div[role="button"]')
            
            for i, button_element in enumerate(buttons):
                try:
                    if not await button_element.is_visible():
                        continue
                    
                    element_info = await self._get_button_element_info(button_element, i)
                    if element_info:
                        button_elements.append(element_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing button element {i}", exception=e)
                    continue
            
            return button_elements
            
        except Exception as e:
            self.logger.error("Error extracting button elements", exception=e)
            return []
    
    async def _extract_select_elements(self) -> List[Dict[str, Any]]:
        """Extract select dropdown elements."""
        try:
            select_elements = []
            selects = await self.page.query_selector_all('select')
            
            for i, select_element in enumerate(selects):
                try:
                    if not await select_element.is_visible():
                        continue
                    
                    element_info = await self._get_select_element_info(select_element, i)
                    if element_info:
                        select_elements.append(element_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing select element {i}", exception=e)
                    continue
            
            return select_elements
            
        except Exception as e:
            self.logger.error("Error extracting select elements", exception=e)
            return []
    
    async def _extract_textarea_elements(self) -> List[Dict[str, Any]]:
        """Extract textarea form elements."""
        try:
            textarea_elements = []
            textareas = await self.page.query_selector_all('textarea')
            
            for i, textarea_element in enumerate(textareas):
                try:
                    if not await textarea_element.is_visible():
                        continue
                    
                    element_info = await self._get_textarea_element_info(textarea_element, i)
                    if element_info:
                        textarea_elements.append(element_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing textarea element {i}", exception=e)
                    continue
            
            return textarea_elements
            
        except Exception as e:
            self.logger.error("Error extracting textarea elements", exception=e)
            return []
    
    async def _get_input_element_info(self, element: Locator, index: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about an input element."""
        try:
            element_info = {
                'element_type': 'input',
                'index': index,
                'type_of_input': await element.get_attribute('type') or 'text',
                'name': await element.get_attribute('name') or '',
                'id': await element.get_attribute('id') or '',
                'id_of_input_component': await element.get_attribute('data-automation-id') or await element.get_attribute('id') or await element.get_attribute('name') or '',
                'placeholder': await element.get_attribute('placeholder') or '',
                'value': await element.get_attribute('value') or '',
                'required': await element.get_attribute('required') is not None,
                'disabled': await element.get_attribute('disabled') is not None,
                'readonly': await element.get_attribute('readonly') is not None,
                'class': await element.get_attribute('class') or '',
                'selector': await self._generate_selector(element),
                'label': await self._find_associated_label(element),
                'aria_label': await element.get_attribute('aria-label') or '',
                'autocomplete': await element.get_attribute('autocomplete') or '',
                'data_automation_id': await element.get_attribute('data-automation-id') or ''
            }
            
            return element_info
            
        except Exception as e:
            self.logger.warning(f"Error getting input element info for index {index}", exception=e)
            return None
    
    async def _get_button_element_info(self, element: Locator, index: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a button element."""
        try:
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            
            element_info = {
                'element_type': 'button',
                'index': index,
                'type_of_input': await element.get_attribute('type') or 'button',
                'name': await element.get_attribute('name') or '',
                'id': await element.get_attribute('id') or '',
                'id_of_input_component': await element.get_attribute('data-automation-id') or await element.get_attribute('id') or await element.get_attribute('name') or '',
                'value': await element.get_attribute('value') or '',
                'text': await element.text_content() or '',
                'disabled': await element.get_attribute('disabled') is not None,
                'class': await element.get_attribute('class') or '',
                'selector': await self._generate_selector(element),
                'label': await element.text_content() or await element.get_attribute('value') or await element.get_attribute('aria-label') or '',
                'aria_label': await element.get_attribute('aria-label') or '',
                'aria_haspopup': await element.get_attribute('aria-haspopup') or '',
                'data_automation_id': await element.get_attribute('data-automation-id') or '',
                'role': await element.get_attribute('role') or '',
                'tag_name': tag_name
            }
            
            return element_info
            
        except Exception as e:
            self.logger.warning(f"Error getting button element info for index {index}", exception=e)
            return None
    
    async def _get_select_element_info(self, element: Locator, index: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a select element."""
        try:
            # Get options
            options = await element.query_selector_all('option')
            option_values = []
            
            for option in options:
                try:
                    option_info = {
                        'value': await option.get_attribute('value') or '',
                        'text': await option.text_content() or '',
                        'selected': await option.get_attribute('selected') is not None
                    }
                    option_values.append(option_info)
                except:
                    continue
            
            element_info = {
                'element_type': 'select',
                'index': index,
                'type_of_input': 'select',
                'name': await element.get_attribute('name') or '',
                'id': await element.get_attribute('id') or '',
                'required': await element.get_attribute('required') is not None,
                'disabled': await element.get_attribute('disabled') is not None,
                'multiple': await element.get_attribute('multiple') is not None,
                'class': await element.get_attribute('class') or '',
                'selector': await self._generate_selector(element),
                'label': await self._find_associated_label(element),
                'aria_label': await element.get_attribute('aria-label') or '',
                'options': option_values
            }
            
            return element_info
            
        except Exception as e:
            self.logger.warning(f"Error getting select element info for index {index}", exception=e)
            return None
    
    async def _get_textarea_element_info(self, element: Locator, index: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a textarea element."""
        try:
            element_info = {
                'element_type': 'textarea',
                'index': index,
                'type_of_input': 'textarea',
                'name': await element.get_attribute('name') or '',
                'id': await element.get_attribute('id') or '',
                'placeholder': await element.get_attribute('placeholder') or '',
                'value': await element.text_content() or '',
                'required': await element.get_attribute('required') is not None,
                'disabled': await element.get_attribute('disabled') is not None,
                'readonly': await element.get_attribute('readonly') is not None,
                'rows': await element.get_attribute('rows') or '',
                'cols': await element.get_attribute('cols') or '',
                'maxlength': await element.get_attribute('maxlength') or '',
                'class': await element.get_attribute('class') or '',
                'selector': await self._generate_selector(element),
                'label': await self._find_associated_label(element),
                'aria_label': await element.get_attribute('aria-label') or ''
            }
            
            return element_info
            
        except Exception as e:
            self.logger.warning(f"Error getting textarea element info for index {index}", exception=e)
            return None
    
    async def _generate_selector(self, element: Locator) -> str:
        """Generate a reliable CSS selector for the element."""
        try:
            # Try data-automation-id first (most reliable for automation)
            automation_id = await element.get_attribute('data-automation-id')
            if automation_id:
                return f'[data-automation-id="{automation_id}"]'
            
            # Try ID next
            element_id = await element.get_attribute('id')
            if element_id:
                return f'#{element_id}'
            
            # Try name attribute
            name = await element.get_attribute('name')
            if name:
                tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                return f'{tag_name}[name="{name}"]'
            
            # Try a combination of tag and attributes
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            input_type = await element.get_attribute('type')
            
            if input_type:
                return f'{tag_name}[type="{input_type}"]'
            
            # Fall back to tag name with index
            return tag_name
            
        except Exception as e:
            self.logger.warning("Error generating selector", exception=e)
            return 'unknown'
    
    async def _find_associated_label(self, element: Locator) -> str:
        """Find the label associated with this form element."""
        try:
            # Check for aria-label first
            aria_label = await element.get_attribute('aria-label')
            if aria_label:
                return aria_label
            
            # Check for label element using 'for' attribute
            element_id = await element.get_attribute('id')
            if element_id:
                label = await self.page.query_selector(f'label[for="{element_id}"]')
                if label:
                    label_text = await label.text_content()
                    if label_text and label_text.strip():
                        return label_text.strip()
            
            # Check for parent label
            parent_label = await element.evaluate('''
                element => {
                    let parent = element.parentElement;
                    while (parent && parent.tagName !== 'BODY') {
                        if (parent.tagName === 'LABEL') {
                            return parent.textContent;
                        }
                        parent = parent.parentElement;
                    }
                    return null;
                }
            ''')
            
            if parent_label and parent_label.strip():
                return parent_label.strip()
            
            # Check placeholder as fallback
            placeholder = await element.get_attribute('placeholder')
            if placeholder:
                return placeholder
            
            return 'Unknown'
            
        except Exception as e:
            self.logger.warning("Error finding associated label", exception=e)
            return 'Unknown'

    async def _extract_dropdown_option_elements(self) -> List[Dict[str, Any]]:
        """Extract dropdown option elements (like Workday dropdown options)."""
        try:
            dropdown_option_elements = []
            
            # Look for Workday-style dropdown options
            dropdown_options = await self.page.query_selector_all(
                'div[data-automation-id="promptLeafNode"], '
                'div[data-automation-id="promptOption"], '
                '[data-uxi-widget-type="multiselectlistitem"]'
            )
            
            for i, option_element in enumerate(dropdown_options):
                try:
                    if not await option_element.is_visible():
                        continue
                    
                    element_info = await self._get_dropdown_option_element_info(option_element, i)
                    if element_info:
                        dropdown_option_elements.append(element_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing dropdown option element {i}", exception=e)
                    continue
            
            return dropdown_option_elements
            
        except Exception as e:
            self.logger.error("Error extracting dropdown option elements", exception=e)
            return []

    async def extract_visible_dropdown_options(self) -> List[Dict[str, Any]]:
        """
        Extract only currently visible dropdown options (useful for cascading dropdowns).
        
        Returns:
            List of dictionaries containing visible dropdown option information
        """
        try:
            dropdown_option_elements = []
            
            # Look for currently visible Workday-style dropdown options
            dropdown_options = await self.page.query_selector_all(
                'div[data-automation-id="promptLeafNode"], '
                'div[data-automation-id="promptOption"], '
                '[data-uxi-widget-type="multiselectlistitem"]'
            )
            
            for i, option_element in enumerate(dropdown_options):
                try:
                    # Only include if currently visible
                    if await option_element.is_visible():
                        element_info = await self._get_dropdown_option_element_info(option_element, i)
                        if element_info:
                            dropdown_option_elements.append(element_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing visible dropdown option element {i}", exception=e)
                    continue
            
            self.logger.debug(f"Found {len(dropdown_option_elements)} visible dropdown options")
            return dropdown_option_elements
            
        except Exception as e:
            self.logger.error("Error extracting visible dropdown option elements", exception=e)
            return []

    async def _get_dropdown_option_element_info(self, element: Locator, index: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a dropdown option element."""
        try:
            # Get the inner option element if it exists
            inner_option = await element.query_selector('[data-automation-id="promptOption"]')
            
            # Get text content from either the inner option or the main element
            text_content = ""
            automation_label = ""
            automation_id = ""
            
            if inner_option:
                text_content = await inner_option.text_content() or ""
                automation_label = await inner_option.get_attribute('data-automation-label') or ""
                automation_id = await inner_option.get_attribute('data-automation-id') or ""
            else:
                text_content = await element.text_content() or ""
                automation_label = await element.get_attribute('data-automation-label') or ""
                automation_id = await element.get_attribute('data-automation-id') or ""
            
            element_info = {
                'element_type': 'dropdown_option',
                'index': index,
                'type_of_input': 'dropdown_option',
                'text': text_content.strip(),
                'label': automation_label or text_content.strip(),
                'data_automation_id': automation_id,
                'data_automation_label': automation_label,
                'selector': await self._generate_dropdown_option_selector(element),
                'is_selected': await element.get_attribute('data-uxi-multiselectlistitem-isselected') == 'true',
                'checked_state': await element.get_attribute('data-automation-checked') or '',
                'multiselect_id': await element.get_attribute('data-uxi-multiselect-id') or '',
                'item_index': await element.get_attribute('data-uxi-multiselectlistitem-index') or '',
                'class': await element.get_attribute('class') or '',
                'id': await element.get_attribute('id') or '',
                'tag_name': await element.evaluate('el => el.tagName.toLowerCase()')
            }
            
            return element_info
            
        except Exception as e:
            self.logger.warning(f"Error getting dropdown option element info for index {index}", exception=e)
            return None

    async def _generate_dropdown_option_selector(self, element: Locator) -> str:
        """Generate a reliable CSS selector for dropdown option elements."""
        try:
            # Try data-automation-id first
            automation_id = await element.get_attribute('data-automation-id')
            if automation_id:
                return f'[data-automation-id="{automation_id}"]'
            
            # Try data-automation-label
            automation_label = await element.get_attribute('data-automation-label')
            if automation_label:
                return f'[data-automation-label="{automation_label}"]'
            
            # Try multiselect attributes
            multiselect_id = await element.get_attribute('data-uxi-multiselect-id')
            item_index = await element.get_attribute('data-uxi-multiselectlistitem-index')
            if multiselect_id and item_index:
                return f'[data-uxi-multiselect-id="{multiselect_id}"][data-uxi-multiselectlistitem-index="{item_index}"]'
            
            # Try ID
            element_id = await element.get_attribute('id')
            if element_id:
                return f'#{element_id}'
            
            # Fall back to text content selector
            text_content = await element.text_content()
            if text_content and text_content.strip():
                return f'text="{text_content.strip()}"'
            
            return 'div[data-automation-id="promptLeafNode"]'
            
        except Exception as e:
            self.logger.warning("Error generating dropdown option selector", exception=e)
            return 'unknown'
