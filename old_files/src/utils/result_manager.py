"""
Result Manager Module

This module handles generation, saving, and display of workflow results.
It provides structured output for analysis and reporting.

Author: Job Automation Team
Date: July 23, 2025
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from playwright.async_api import Page

from src.config import ApplicationConfig
from src.utils.logger import ApplicationLogger
from src.utils.form_extractor import FormExtractor


class ResultManager:
    """
    Manages workflow results including generation, saving, and display.
    
    This class provides methods for creating comprehensive result reports,
    saving them to files, and displaying summary information.
    """
    
    def __init__(self):
        """Initialize the result manager."""
        self.config = ApplicationConfig()
        self.logger = ApplicationLogger("ResultManager")
    
    async def generate_workflow_results(
        self, 
        page: Page, 
        auth_type: str, 
        auth_success: bool, 
        form_success: bool
    ) -> Dict[str, Any]:
        """
        Generate comprehensive workflow results.
        
        Args:
            page: Playwright page instance
            auth_type: Type of authentication used
            auth_success: Whether authentication was successful
            form_success: Whether form completion was successful
            
        Returns:
            Dictionary containing complete workflow results
        """
        try:
            self.logger.info("Generating comprehensive workflow results...")
            
            # Extract final form elements
            form_extractor = FormExtractor(page, self.logger)
            final_form_elements = await form_extractor.extract_all_form_elements()
            
            # Get page information
            current_url = page.url
            page_title = await page.title()
            
            # Create comprehensive results
            results = {
                "workflow_execution": {
                    "timestamp": datetime.now().isoformat(),
                    "execution_date": datetime.now().strftime("%Y-%m-%d"),
                    "execution_time": datetime.now().strftime("%H:%M:%S"),
                    "workflow_completed": auth_success and form_success,
                    "total_duration_seconds": self._calculate_execution_duration()
                },
                "authentication": {
                    "method": auth_type,
                    "success": auth_success,
                    "method_display_name": auth_type.title().replace("_", " ")
                },
                "form_processing": {
                    "success": form_success,
                    "total_elements_found": len(final_form_elements),
                    "elements_by_type": self._categorize_elements_by_type(final_form_elements)
                },
                "page_information": {
                    "final_url": current_url,
                    "page_title": page_title,
                    "domain": self._extract_domain(current_url)
                },
                "form_elements_analysis": {
                    "total_elements": len(final_form_elements),
                    "required_elements": self._count_required_elements(final_form_elements),
                    "fillable_elements": self._count_fillable_elements(final_form_elements),
                    "elements_by_category": self._categorize_elements_by_purpose(final_form_elements)
                },
                "detailed_form_elements": final_form_elements,
                "execution_summary": {
                    "steps_completed": self._get_completed_steps(auth_success, form_success),
                    "success_rate": self._calculate_success_rate(auth_success, form_success),
                    "status": self._determine_overall_status(auth_success, form_success)
                }
            }
            
            self.logger.success(
                "Workflow results generated successfully",
                total_elements=len(final_form_elements),
                auth_success=auth_success,
                form_success=form_success
            )
            
            return results
            
        except Exception as e:
            self.logger.error("Failed to generate workflow results", exception=e)
            return await self._create_error_results(page, auth_type, str(e))
    
    async def save_workflow_results(self, results: Dict[str, Any]) -> Optional[str]:
        """
        Save workflow results to a JSON file.
        
        Args:
            results: Results dictionary to save
            
        Returns:
            Path to saved file if successful, None otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"workflow_results_{timestamp}.json"
            file_path = os.path.join(self.config.paths.logs_directory, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.logger.success(f"Workflow results saved to: {filename}")
            return file_path
            
        except Exception as e:
            self.logger.error("Failed to save workflow results", exception=e)
            return None
    
    def display_workflow_summary(self, results: Dict[str, Any]):
        """
        Display a formatted summary of workflow results.
        
        Args:
            results: Results dictionary to display
        """
        try:
            print("\n" + "=" * 80)
            print("🤖 JOB APPLICATION AUTOMATION - WORKFLOW SUMMARY")
            print("=" * 80)
            
            # Execution summary
            execution = results.get("workflow_execution", {})
            print(f"📅 Execution Date: {execution.get('execution_date', 'Unknown')}")
            print(f"⏰ Execution Time: {execution.get('execution_time', 'Unknown')}")
            print(f"✅ Workflow Completed: {execution.get('workflow_completed', False)}")
            
            # Authentication summary
            auth = results.get("authentication", {})
            print(f"\n🔐 Authentication:")
            print(f"   Method: {auth.get('method_display_name', 'Unknown')}")
            print(f"   Success: {'✅ Yes' if auth.get('success') else '❌ No'}")
            
            # Form processing summary
            form = results.get("form_processing", {})
            print(f"\n📝 Form Processing:")
            print(f"   Success: {'✅ Yes' if form.get('success') else '❌ No'}")
            print(f"   Elements Found: {form.get('total_elements_found', 0)}")
            
            # Page information
            page_info = results.get("page_information", {})
            print(f"\n🌐 Final Page:")
            print(f"   URL: {page_info.get('final_url', 'Unknown')}")
            print(f"   Title: {page_info.get('page_title', 'Unknown')}")
            
            # Form elements analysis
            analysis = results.get("form_elements_analysis", {})
            print(f"\n📊 Form Elements Analysis:")
            print(f"   Total Elements: {analysis.get('total_elements', 0)}")
            print(f"   Required Elements: {analysis.get('required_elements', 0)}")
            print(f"   Fillable Elements: {analysis.get('fillable_elements', 0)}")
            
            # Elements by type
            elements_by_type = form.get("elements_by_type", {})
            if elements_by_type:
                print(f"\n📋 Elements by Type:")
                for element_type, count in elements_by_type.items():
                    print(f"   {element_type.title()}: {count}")
            
            # Execution summary
            summary = results.get("execution_summary", {})
            print(f"\n📈 Execution Summary:")
            print(f"   Steps Completed: {summary.get('steps_completed', 0)}/2")
            print(f"   Success Rate: {summary.get('success_rate', 0)}%")
            print(f"   Overall Status: {summary.get('status', 'Unknown')}")
            
            print("=" * 80)
            
        except Exception as e:
            self.logger.error("Failed to display workflow summary", exception=e)
            print(f"\n❌ Error displaying summary: {str(e)}")
    
    def _categorize_elements_by_type(self, elements: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize form elements by their type."""
        categories = {}
        
        for element in elements:
            element_type = element.get('element_type', 'unknown')
            categories[element_type] = categories.get(element_type, 0) + 1
        
        return categories
    
    def _categorize_elements_by_purpose(self, elements: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize form elements by their likely purpose."""
        categories = {
            "personal_info": 0,
            "contact_info": 0,
            "address_info": 0,
            "professional_info": 0,
            "authentication": 0,
            "actions": 0,
            "other": 0
        }
        
        for element in elements:
            label = element.get('label', '').lower()
            name = element.get('name', '').lower()
            input_type = element.get('type_of_input', '').lower()
            
            field_text = f"{label} {name}".lower()
            
            if any(keyword in field_text for keyword in ['name', 'first', 'last', 'middle']):
                categories["personal_info"] += 1
            elif any(keyword in field_text for keyword in ['email', 'phone', 'contact']):
                categories["contact_info"] += 1
            elif any(keyword in field_text for keyword in ['address', 'street', 'city', 'state', 'zip', 'country']):
                categories["address_info"] += 1
            elif any(keyword in field_text for keyword in ['job', 'position', 'title', 'company', 'experience']):
                categories["professional_info"] += 1
            elif any(keyword in field_text for keyword in ['password', 'login', 'username']):
                categories["authentication"] += 1
            elif input_type in ['submit', 'button'] or element.get('element_type') == 'button':
                categories["actions"] += 1
            else:
                categories["other"] += 1
        
        return categories
    
    def _count_required_elements(self, elements: List[Dict[str, Any]]) -> int:
        """Count required form elements."""
        return sum(1 for element in elements if element.get('required', False))
    
    def _count_fillable_elements(self, elements: List[Dict[str, Any]]) -> int:
        """Count fillable form elements."""
        fillable_types = ['input', 'textarea', 'select']
        return sum(1 for element in elements 
                  if element.get('element_type') in fillable_types 
                  and element.get('type_of_input') not in ['submit', 'button', 'reset'])
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    def _calculate_execution_duration(self) -> float:
        """Calculate approximate execution duration."""
        # This is a placeholder - in a real implementation,
        # you'd track start time and calculate actual duration
        return 0.0
    
    def _get_completed_steps(self, auth_success: bool, form_success: bool) -> int:
        """Count completed workflow steps."""
        completed = 0
        if auth_success:
            completed += 1
        if form_success:
            completed += 1
        return completed
    
    def _calculate_success_rate(self, auth_success: bool, form_success: bool) -> float:
        """Calculate overall success rate."""
        total_steps = 2
        completed_steps = self._get_completed_steps(auth_success, form_success)
        return round((completed_steps / total_steps) * 100, 1)
    
    def _determine_overall_status(self, auth_success: bool, form_success: bool) -> str:
        """Determine overall workflow status."""
        if auth_success and form_success:
            return "FULLY_SUCCESSFUL"
        elif auth_success:
            return "PARTIALLY_SUCCESSFUL"
        else:
            return "FAILED"
    
    async def _create_error_results(self, page: Page, auth_type: str, error_message: str) -> Dict[str, Any]:
        """Create error results when result generation fails."""
        try:
            current_url = page.url if page else "unknown"
            page_title = "unknown"
            
            try:
                if page:
                    page_title = await page.title()
            except:
                pass
            
            return {
                "workflow_execution": {
                    "timestamp": datetime.now().isoformat(),
                    "workflow_completed": False,
                    "error": error_message
                },
                "authentication": {
                    "method": auth_type,
                    "success": False
                },
                "form_processing": {
                    "success": False,
                    "total_elements_found": 0
                },
                "page_information": {
                    "final_url": current_url,
                    "page_title": page_title
                },
                "detailed_form_elements": [],
                "execution_summary": {
                    "status": "ERROR",
                    "error_message": error_message
                }
            }
            
        except Exception as e:
            self.logger.error("Failed to create error results", exception=e)
            return {"error": "Failed to generate results"}
    
    def create_sample_results(self) -> Dict[str, Any]:
        """Create sample results for testing purposes."""
        return {
            "workflow_execution": {
                "timestamp": datetime.now().isoformat(),
                "execution_date": datetime.now().strftime("%Y-%m-%d"),
                "execution_time": datetime.now().strftime("%H:%M:%S"),
                "workflow_completed": True,
                "total_duration_seconds": 45.2
            },
            "authentication": {
                "method": "signin",
                "success": True,
                "method_display_name": "Sign In"
            },
            "form_processing": {
                "success": True,
                "total_elements_found": 12,
                "elements_by_type": {
                    "input": 8,
                    "button": 2,
                    "select": 2
                }
            },
            "page_information": {
                "final_url": "https://example.com/dashboard",
                "page_title": "Dashboard - Job Portal",
                "domain": "example.com"
            },
            "execution_summary": {
                "steps_completed": 2,
                "success_rate": 100.0,
                "status": "FULLY_SUCCESSFUL"
            }
        }
