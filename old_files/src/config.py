"""
Application Configuration Module

This module contains all configuration settings for the job application automation system.
It centralizes all configurable parameters and provides easy access to application settings.

Author: Job Automation Team
Date: July 23, 2025
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BrowserConfig:
    """Configuration settings for browser automation."""
    headless: bool = False
    slow_motion_delay: int = 1000  # milliseconds
    default_timeout: int = 30000   # milliseconds
    viewport_width: int = 1280
    viewport_height: int = 720
    user_agent: Optional[str] = None


@dataclass
class ApplicationPaths:
    """File and directory paths used by the application."""
    
    def __init__(self):
        # Get the project root directory
        self.project_root = self._get_project_root()
        
        # Data directory paths
        self.data_directory = os.path.join(self.project_root, 'data')
        self.user_profile_file = os.path.join(self.data_directory, 'user_profile.json')
        
        # Logs directory paths
        self.logs_directory = os.path.join(self.project_root, 'logs')
        self.workflow_results_file = os.path.join(self.logs_directory, 'workflow_results.json')
        self.form_data_logs = os.path.join(self.logs_directory, 'form_data_logs')
        
        # Ensure directories exist
        self._ensure_directories_exist()
    
    def _get_project_root(self) -> str:
        """Get the absolute path to the project root directory."""
        current_file = os.path.abspath(__file__)
        # Navigate up from src/config.py to project root
        return os.path.dirname(os.path.dirname(current_file))
    
    def _ensure_directories_exist(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_directory,
            self.logs_directory,
            self.form_data_logs
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


class ApplicationConfig:
    """
    Main application configuration class.
    
    This class provides centralized access to all application settings
    and configuration parameters.
    """
    
    # Target application URL
    TARGET_APPLICATION_URL = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/US%2C-CA%2C-Santa-Clara/Senior-AI-and-ML-Engineer---AI-for-Networking_JR2000376/apply/applyManually?q=ml+enginer"  # Replace with actual URL
    
    # Application behavior settings
    KEEP_BROWSER_OPEN_FOR_INSPECTION = True
    ENABLE_DETAILED_LOGGING = True
    SAVE_SCREENSHOTS_ON_ERROR = True
    
    # Timing settings (in milliseconds)
    PAGE_LOAD_TIMEOUT = 30000
    ELEMENT_WAIT_TIMEOUT = 10000
    FORM_SUBMISSION_DELAY = 2000
    
    def __init__(self):
        """Initialize application configuration."""
        self.browser = BrowserConfig()
        self.paths = ApplicationPaths()
        
        # Development vs Production settings
        self.is_development_mode = self._is_development_mode()
        
        if self.is_development_mode:
            self.browser.headless = False
            self.keep_browser_open = True
        else:
            self.browser.headless = True
            self.keep_browser_open = False
    
    def _is_development_mode(self) -> bool:
        """
        Determine if the application is running in development mode.
        
        Returns:
            True if in development mode, False otherwise
        """
        return os.getenv('JOB_AUTO_ENV', 'development').lower() == 'development'
    
    def get_target_url(self) -> str:
        """
        Get the target application URL.
        
        Returns:
            The URL of the job application portal
        """
        return self.TARGET_APPLICATION_URL
    
    def get_browser_config(self) -> BrowserConfig:
        """
        Get browser configuration settings.
        
        Returns:
            BrowserConfig object with browser settings
        """
        return self.browser
    
    def get_application_paths(self) -> ApplicationPaths:
        """
        Get application file and directory paths.
        
        Returns:
            ApplicationPaths object with all path configurations
        """
        return self.paths


# Legacy compatibility - maintain existing import structure
START_URL = ApplicationConfig().get_target_url()
