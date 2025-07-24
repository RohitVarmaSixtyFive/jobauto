"""
Browser Manager Module

This module handles browser initialization, configuration, and navigation operations.
It provides a clean interface for managing Playwright browser instances and page interactions.

Author: Job Automation Team
Date: July 23, 2025
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Tuple, Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from src.config import ApplicationConfig, BrowserConfig
from src.utils.logger import ApplicationLogger


class BrowserManager:
    """
    Manages browser instances and provides high-level navigation operations.
    
    This class handles browser launching, page creation, and basic navigation
    operations with proper error handling and logging.
    """
    
    def __init__(self, config: ApplicationConfig):
        """
        Initialize the browser manager.
        
        Args:
            config: Application configuration object
        """
        self.config = config
        self.browser_config = config.get_browser_config()
        self.logger = ApplicationLogger("BrowserManager")
    
    async def _launch_browser(self) -> Browser:
        """
        Launch a browser instance with configured settings.
        
        Returns:
            Playwright Browser instance
            
        Raises:
            Exception: If browser launch fails
        """
        try:
            self.logger.info("Launching browser...")
            
            playwright = await async_playwright().start()
            
            # Configure browser launch options
            launch_options = {
                'headless': self.browser_config.headless,
                'slow_mo': self.browser_config.slow_motion_delay,
            }
            
            # Add additional options for development mode
            if not self.browser_config.headless:
                launch_options.update({
                    'args': [
                        '--start-maximized',
                        '--disable-blink-features=AutomationControlled'
                    ]
                })
            
            browser = await playwright.chromium.launch(**launch_options)
            
            self.logger.success(
                f"Browser launched successfully",
                headless=self.browser_config.headless,
                slow_mo=self.browser_config.slow_motion_delay
            )
            
            return browser
            
        except Exception as e:
            self.logger.error("Failed to launch browser", exception=e)
            raise
    
    async def _create_page(self, browser: Browser) -> Page:
        """
        Create a new page with configured settings.
        
        Args:
            browser: Browser instance to create page in
            
        Returns:
            Playwright Page instance
            
        Raises:
            Exception: If page creation fails
        """
        try:
            self.logger.info("Creating new browser page...")
            
            # Create browser context with settings
            context = await browser.new_context(
                viewport={
                    'width': self.browser_config.viewport_width,
                    'height': self.browser_config.viewport_height
                },
                user_agent=self.browser_config.user_agent
            )
            
            # Create new page
            page = await context.new_page()
            
            # Set default timeout
            page.set_default_timeout(self.browser_config.default_timeout)
            
            self.logger.success(
                "Browser page created successfully",
                viewport_size=f"{self.browser_config.viewport_width}x{self.browser_config.viewport_height}",
                timeout=self.browser_config.default_timeout
            )
            
            return page
            
        except Exception as e:
            self.logger.error("Failed to create browser page", exception=e)
            raise
    
    @asynccontextmanager
    async def get_browser_context(self):
        """
        Context manager for browser and page lifecycle.
        
        Yields:
            Tuple of (Browser, Page) instances
            
        Usage:
            async with browser_manager.get_browser_context() as (browser, page):
                # Use browser and page here
                pass
        """
        browser = None
        page = None
        
        try:
            # Launch browser and create page
            browser = await self._launch_browser()
            page = await self._create_page(browser)
            
            self.logger.info("Browser context ready for use")
            yield browser, page
            
        except Exception as e:
            self.logger.error("Error in browser context", exception=e)
            raise
        finally:
            # Cleanup resources
            try:
                if page:
                    await page.close()
                    self.logger.debug("Page closed successfully")
                    
                if browser:
                    await browser.close()
                    self.logger.debug("Browser closed successfully")
                    
            except Exception as cleanup_error:
                self.logger.warning("Error during browser cleanup", exception=cleanup_error)
    
    async def navigate_to_application(
        self, 
        page: Page, 
        email: str, 
        password: str
    ) -> bool:
        """
        Navigate to the target application and perform initial setup.
        
        Args:
            page: Browser page instance
            email: User email for potential pre-authentication
            password: User password for potential pre-authentication
            
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            target_url = self.config.get_target_url()
            
            self.logger.workflow_step("Navigation", "STARTED", target_url=target_url)
            
            # Navigate to the target URL
            self.logger.info(f"Navigating to: {target_url}")
            response = await page.goto(target_url, wait_until='networkidle')
            
            # Check response status
            if response and response.status >= 400:
                self.logger.error(
                    f"Navigation failed with HTTP status: {response.status}",
                    url=target_url
                )
                return False
            
            # Wait for page to be fully loaded
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Log current page information
            current_url = page.url
            page_title = await page.title()
            
            self.logger.page_navigation(
                current_url, 
                "COMPLETED",
                title=page_title,
                status_code=response.status if response else "Unknown"
            )
            
            self.logger.workflow_step(
                "Navigation", 
                "COMPLETED",
                final_url=current_url,
                page_title=page_title
            )
            
            return True
            
        except asyncio.TimeoutError:
            self.logger.error("Navigation timeout - page took too long to load")
            return False
        except Exception as e:
            self.logger.error("Navigation failed", exception=e)
            return False
    
    async def wait_for_page_stability(self, page: Page, timeout: int = 5000) -> bool:
        """
        Wait for page to become stable (no network activity).
        
        Args:
            page: Browser page instance
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if page became stable, False if timeout occurred
        """
        try:
            self.logger.debug(f"Waiting for page stability (timeout: {timeout}ms)")
            
            await page.wait_for_load_state('networkidle', timeout=timeout)
            await page.wait_for_timeout(1000)  # Additional buffer
            
            self.logger.debug("Page stability achieved")
            return True
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Page stability timeout after {timeout}ms")
            return False
        except Exception as e:
            self.logger.error("Error while waiting for page stability", exception=e)
            return False
    
    async def take_screenshot(self, page: Page, filename: str) -> Optional[str]:
        """
        Take a screenshot of the current page.
        
        Args:
            page: Browser page instance
            filename: Name for the screenshot file
            
        Returns:
            Path to the screenshot file if successful, None otherwise
        """
        try:
            screenshot_path = os.path.join(
                self.config.paths.logs_directory,
                f"screenshot_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            
            await page.screenshot(path=screenshot_path, full_page=True)
            
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            self.logger.error("Failed to take screenshot", exception=e)
            return None
