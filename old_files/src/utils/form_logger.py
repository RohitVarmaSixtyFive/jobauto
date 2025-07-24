"""
Form Data Logger Module

This module handles logging of form data and workflow steps to JSON files.
It provides structured logging for form elements, user interactions, and workflow progress.

Author: Job Automation Team
Date: July 23, 2025
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.config import ApplicationConfig
from src.utils.logger import ApplicationLogger


class FormDataLogger:
    """
    Handles structured logging of form data and workflow steps.
    
    This class provides methods for logging form elements, user interactions,
    and workflow progress to JSON files for analysis and debugging.
    """
    
    def __init__(self, logger: ApplicationLogger):
        """
        Initialize the form data logger.
        
        Args:
            logger: Application logger instance
        """
        self.logger = logger
        self.config = ApplicationConfig()
        self.logs_directory = self.config.paths.form_data_logs
        
        # Ensure logs directory exists
        os.makedirs(self.logs_directory, exist_ok=True)
    
    async def log_form_elements(
        self,
        form_elements: List[Dict[str, Any]],
        step_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log form elements to a JSON file.
        
        Args:
            form_elements: List of form element dictionaries
            step_name: Name of the workflow step
            metadata: Additional metadata to include in the log
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"form_data_{step_name}_{timestamp}.json"
            file_path = os.path.join(self.logs_directory, filename)
            
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "step_name": step_name,
                "metadata": metadata or {},
                "form_elements_count": len(form_elements),
                "form_elements": form_elements
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(
                f"Form elements logged successfully",
                step=step_name,
                elements_count=len(form_elements),
                file_path=filename
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log form elements for step: {step_name}", exception=e)
    
    async def log_step_completion(
        self,
        step_name: str,
        success: bool,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log workflow step completion status.
        
        Args:
            step_name: Name of the completed step
            success: Whether the step completed successfully
            additional_data: Additional data to include in the log
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"step_completion_{step_name}_{timestamp}.json"
            file_path = os.path.join(self.logs_directory, filename)
            
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "step_name": step_name,
                "success": success,
                "status": "COMPLETED" if success else "FAILED",
                "additional_data": additional_data or {}
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            status_msg = "successfully" if success else "with errors"
            self.logger.info(
                f"Step completion logged {status_msg}",
                step=step_name,
                success=success,
                file_path=filename
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log step completion for: {step_name}", exception=e)
    
    async def log_user_interaction(
        self,
        interaction_type: str,
        element_info: Dict[str, Any],
        value: Optional[str] = None,
        success: bool = True
    ):
        """
        Log user interaction with form elements.
        
        Args:
            interaction_type: Type of interaction (FILL, CLICK, SELECT, etc.)
            element_info: Information about the target element
            value: Value used in the interaction (for fill operations)
            success: Whether the interaction was successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interaction_{interaction_type.lower()}_{timestamp}.json"
            file_path = os.path.join(self.logs_directory, filename)
            
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "interaction_type": interaction_type,
                "success": success,
                "element_info": element_info,
                "value": value if value and interaction_type != "FILL" else "[REDACTED]" if value else None
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(
                f"User interaction logged",
                interaction=interaction_type,
                element_label=element_info.get('label', 'Unknown'),
                success=success
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log user interaction: {interaction_type}", exception=e)
    
    async def log_page_state(
        self,
        state_name: str,
        page_url: str,
        page_title: str,
        additional_info: Optional[Dict[str, Any]] = None
    ):
        """
        Log current page state information.
        
        Args:
            state_name: Name describing the current state
            page_url: Current page URL
            page_title: Current page title
            additional_info: Additional state information
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"page_state_{state_name}_{timestamp}.json"
            file_path = os.path.join(self.logs_directory, filename)
            
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "state_name": state_name,
                "page_url": page_url,
                "page_title": page_title,
                "additional_info": additional_info or {}
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(
                f"Page state logged",
                state=state_name,
                url=page_url,
                title=page_title
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log page state: {state_name}", exception=e)
    
    def get_latest_log_file(self, log_type: str) -> Optional[str]:
        """
        Get the path to the most recent log file of a specific type.
        
        Args:
            log_type: Type of log file to find (form_data, step_completion, etc.)
            
        Returns:
            Path to the latest log file, or None if not found
        """
        try:
            log_files = [
                f for f in os.listdir(self.logs_directory)
                if f.startswith(log_type) and f.endswith('.json')
            ]
            
            if not log_files:
                return None
            
            # Sort by modification time, newest first
            log_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(self.logs_directory, x)),
                reverse=True
            )
            
            return os.path.join(self.logs_directory, log_files[0])
            
        except Exception as e:
            self.logger.error(f"Failed to get latest log file for type: {log_type}", exception=e)
            return None
    
    def clean_old_logs(self, max_age_days: int = 7):
        """
        Clean up log files older than the specified number of days.
        
        Args:
            max_age_days: Maximum age of log files to keep
        """
        try:
            current_time = datetime.now()
            cutoff_time = current_time.timestamp() - (max_age_days * 24 * 60 * 60)
            
            removed_count = 0
            
            for filename in os.listdir(self.logs_directory):
                if not filename.endswith('.json'):
                    continue
                
                file_path = os.path.join(self.logs_directory, filename)
                file_time = os.path.getmtime(file_path)
                
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        removed_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove old log file: {filename}", exception=e)
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old log files")
            
        except Exception as e:
            self.logger.error("Failed to clean old log files", exception=e)
