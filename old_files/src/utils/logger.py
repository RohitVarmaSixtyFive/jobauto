"""
Application Logger Module

This module provides a centralized logging system for the job application automation tool.
It handles different log levels, formatting, and output destinations.

Author: Job Automation Team
Date: July 23, 2025
"""

import logging
import os
from datetime import datetime
from typing import Optional
from src.config import ApplicationConfig


class ApplicationLogger:
    """
    Centralized logging system for the application.
    
    This class provides methods for logging at different levels with consistent
    formatting and output handling.
    """
    
    def __init__(self, logger_name: str = "JobAutoLogger"):
        """
        Initialize the application logger.
        
        Args:
            logger_name: Name identifier for this logger instance
        """
        self.config = ApplicationConfig()
        self.logger_name = logger_name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up and configure the logger with appropriate handlers and formatting.
        
        Returns:
            Configured logger instance
        """
        # Create logger
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG if self.config.ENABLE_DETAILED_LOGGING else logging.INFO)
        
        # Prevent duplicate handlers if logger already exists
        if logger.handlers:
            return logger
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler for detailed logging
        if self.config.ENABLE_DETAILED_LOGGING:
            log_file_path = self._get_log_file_path()
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _get_log_file_path(self) -> str:
        """
        Generate the log file path with timestamp.
        
        Returns:
            Full path to the log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"job_automation_{timestamp}.log"
        return os.path.join(self.config.paths.logs_directory, log_filename)
    
    def debug(self, message: str, **kwargs):
        """
        Log a debug message.
        
        Args:
            message: Debug message to log
            **kwargs: Additional context data
        """
        if kwargs:
            message = f"{message} | Context: {kwargs}"
        self.logger.debug(message)
    
    def info(self, message: str, **kwargs):
        """
        Log an informational message.
        
        Args:
            message: Information message to log
            **kwargs: Additional context data
        """
        if kwargs:
            message = f"{message} | Context: {kwargs}"
        self.logger.info(message)
    
    def warning(self, message: str, **kwargs):
        """
        Log a warning message.
        
        Args:
            message: Warning message to log
            **kwargs: Additional context data
        """
        if kwargs:
            message = f"{message} | Context: {kwargs}"
        self.logger.warning(message)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """
        Log an error message.
        
        Args:
            message: Error message to log
            exception: Optional exception object for additional context
            **kwargs: Additional context data
        """
        if exception:
            message = f"{message} | Exception: {str(exception)}"
        if kwargs:
            message = f"{message} | Context: {kwargs}"
        self.logger.error(message)
    
    def success(self, message: str, **kwargs):
        """
        Log a success message with special formatting.
        
        Args:
            message: Success message to log
            **kwargs: Additional context data
        """
        success_message = f"✅ SUCCESS: {message}"
        if kwargs:
            success_message = f"{success_message} | Context: {kwargs}"
        self.logger.info(success_message)
    
    def failure(self, message: str, **kwargs):
        """
        Log a failure message with special formatting.
        
        Args:
            message: Failure message to log
            **kwargs: Additional context data
        """
        failure_message = f"❌ FAILURE: {message}"
        if kwargs:
            failure_message = f"{failure_message} | Context: {kwargs}"
        self.logger.error(failure_message)
    
    def workflow_step(self, step_name: str, status: str = "STARTED", **kwargs):
        """
        Log workflow step information with consistent formatting.
        
        Args:
            step_name: Name of the workflow step
            status: Status of the step (STARTED, COMPLETED, FAILED)
            **kwargs: Additional context data
        """
        workflow_message = f"🔄 WORKFLOW: {step_name} - {status}"
        if kwargs:
            workflow_message = f"{workflow_message} | Context: {kwargs}"
        
        if status.upper() == "FAILED":
            self.logger.error(workflow_message)
        else:
            self.logger.info(workflow_message)
    
    def form_interaction(self, action: str, element_info: str, **kwargs):
        """
        Log form interaction events with special formatting.
        
        Args:
            action: Type of action performed (FILL, CLICK, SELECT, etc.)
            element_info: Information about the form element
            **kwargs: Additional context data
        """
        form_message = f"📝 FORM: {action} - {element_info}"
        if kwargs:
            form_message = f"{form_message} | Context: {kwargs}"
        self.logger.info(form_message)
    
    def page_navigation(self, url: str, action: str = "NAVIGATED", **kwargs):
        """
        Log page navigation events.
        
        Args:
            url: URL that was navigated to
            action: Type of navigation action
            **kwargs: Additional context data
        """
        nav_message = f"🌐 NAVIGATION: {action} - {url}"
        if kwargs:
            nav_message = f"{nav_message} | Context: {kwargs}"
        self.logger.info(nav_message)
    
    def performance_metric(self, metric_name: str, value: float, unit: str = "ms", **kwargs):
        """
        Log performance metrics.
        
        Args:
            metric_name: Name of the performance metric
            value: Measured value
            unit: Unit of measurement
            **kwargs: Additional context data
        """
        perf_message = f"📊 PERFORMANCE: {metric_name} = {value}{unit}"
        if kwargs:
            perf_message = f"{perf_message} | Context: {kwargs}"
        self.logger.info(perf_message)
