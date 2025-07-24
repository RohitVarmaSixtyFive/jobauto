"""
Authentication Manager Module

This module handles user authentication choices and provides a clean interface
for managing authentication workflows.

Author: Job Automation Team
Date: July 23, 2025
"""

import asyncio
from typing import Literal
from src.utils.logger import ApplicationLogger


AuthenticationType = Literal["signin", "signup"]


class AuthenticationManager:
    """
    Manages authentication workflow decisions and user interactions.
    
    This class provides methods for getting user authentication preferences
    and managing authentication flow decisions.
    """
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.logger = ApplicationLogger("AuthenticationManager")
    
    async def get_user_authentication_choice(self) -> AuthenticationType:
        """
        Get user's choice between sign-in and sign-up.
        
        This method prompts the user to choose their preferred authentication method
        and validates the input.
        
        Returns:
            Either "signin" or "signup" based on user choice
        """
        self.logger.info("Requesting user authentication method selection...")
        
        print("\n" + "=" * 50)
        print("🔐 AUTHENTICATION METHOD SELECTION")
        print("=" * 50)
        print("Please choose your authentication method:")
        print("1. Sign In (existing account)")
        print("2. Sign Up (create new account)")
        print("-" * 50)
        
        while True:
            try:
                choice = input("Enter your choice (1 or 2): ").strip()
                
                if choice == "1":
                    self.logger.info("User selected: Sign In (existing account)")
                    print("✅ Selected: Sign In with existing account")
                    return "signin"
                elif choice == "2":
                    self.logger.info("User selected: Sign Up (create new account)")
                    print("✅ Selected: Sign Up to create new account")
                    return "signup"
                else:
                    print("❌ Invalid choice. Please enter 1 or 2.")
                    continue
                    
            except KeyboardInterrupt:
                print("\n⚠️  Authentication selection cancelled by user.")
                self.logger.warning("Authentication selection cancelled by user")
                # Default to signin if cancelled
                return "signin"
            except Exception as e:
                self.logger.error("Error during authentication choice selection", exception=e)
                print("❌ Error occurred. Please try again.")
                continue
    
    def validate_authentication_type(self, auth_type: str) -> bool:
        """
        Validate that the authentication type is supported.
        
        Args:
            auth_type: Authentication type to validate
            
        Returns:
            True if valid, False otherwise
        """
        valid_types = ["signin", "signup"]
        is_valid = auth_type.lower() in valid_types
        
        if not is_valid:
            self.logger.error(f"Invalid authentication type: {auth_type}")
        
        return is_valid
    
    def get_authentication_display_name(self, auth_type: AuthenticationType) -> str:
        """
        Get user-friendly display name for authentication type.
        
        Args:
            auth_type: Authentication type
            
        Returns:
            Human-readable display name
        """
        display_names = {
            "signin": "Sign In",
            "signup": "Sign Up"
        }
        
        return display_names.get(auth_type, auth_type.title())
