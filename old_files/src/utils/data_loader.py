"""
Data Loader Module

This module handles loading and validation of user data from configuration files.
It provides a clean interface for accessing user profile information and credentials.

Author: Job Automation Team
Date: July 23, 2025
"""

import json
import os
from typing import Dict, Any, Optional
from src.config import ApplicationConfig


class DataLoader:
    """
    Handles loading and validation of user data from JSON configuration files.
    
    This class provides methods to load user profile data, validate required fields,
    and handle various data loading scenarios.
    """
    
    def __init__(self):
        """Initialize the data loader with application configuration."""
        self.config = ApplicationConfig()
        self.paths = self.config.get_application_paths()
    
    def load_user_profile(self) -> Optional[Dict[str, Any]]:
        """
        Load user profile data from the JSON configuration file.
        
        Returns:
            Dictionary containing user profile data if successful, None otherwise
        """
        try:
            profile_file_path = self.paths.user_profile_file
            
            if not os.path.exists(profile_file_path):
                print(f"❌ User profile file not found: {profile_file_path}")
                return None
            
            print(f"📄 Loading user profile from: {profile_file_path}")
            
            with open(profile_file_path, 'r', encoding='utf-8') as file:
                user_data = json.load(file)
            
            # Validate the loaded data
            if self._validate_user_data(user_data):
                print("✅ User profile loaded and validated successfully")
                return user_data
            else:
                print("❌ User profile validation failed")
                return None
                
        except FileNotFoundError:
            print("❌ User profile file not found in data directory")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format in user profile file: {str(e)}")
            return None
        except PermissionError:
            print("❌ Permission denied while reading user profile file")
            return None
        except Exception as e:
            print(f"❌ Unexpected error while loading user profile: {str(e)}")
            return None
    
    def _validate_user_data(self, user_data: Dict[str, Any]) -> bool:
        """
        Validate that the user data contains all required fields.
        
        Args:
            user_data: Dictionary containing user profile data
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            # Check for required top-level structure
            if not isinstance(user_data, dict):
                print("❌ User data must be a JSON object")
                return False
            
            # Check for personal information section
            personal_info = user_data.get('personal_information')
            if not personal_info or not isinstance(personal_info, dict):
                print("❌ Missing or invalid 'personal_information' section")
                return False
            
            # Check for required credential fields
            required_fields = ['email', 'password', 'name']
            missing_fields = []
            
            for field in required_fields:
                value = personal_info.get(field)
                if not value or not isinstance(value, str) or not value.strip():
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing or empty required fields: {', '.join(missing_fields)}")
                return False
            
            # Validate email format (basic check)
            email = personal_info.get('email', '').strip()
            if '@' not in email or '.' not in email:
                print("❌ Invalid email format")
                return False
            
            # Check password strength (basic check)
            password = personal_info.get('password', '')
            if len(password) < 6:
                print("❌ Password must be at least 6 characters long")
                return False
            
            print("✅ User data validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Error during user data validation: {str(e)}")
            return False
    
    def get_user_credentials(self, user_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract user credentials from user data.
        
        Args:
            user_data: Complete user profile data
            
        Returns:
            Dictionary with email and password if successful, None otherwise
        """
        try:
            personal_info = user_data.get('personal_information', {})
            
            credentials = {
                'email': personal_info.get('email', '').strip(),
                'password': personal_info.get('password', ''),
                'name': personal_info.get('name', '').strip()
            }
            
            # Validate credentials
            if not credentials['email'] or not credentials['password']:
                print("❌ Missing email or password in user data")
                return None
            
            return credentials
            
        except Exception as e:
            print(f"❌ Error extracting user credentials: {str(e)}")
            return None
    
    def get_personal_information(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract personal information section from user data.
        
        Args:
            user_data: Complete user profile data
            
        Returns:
            Personal information dictionary if successful, None otherwise
        """
        try:
            personal_info = user_data.get('personal_information')
            
            if not personal_info or not isinstance(personal_info, dict):
                print("❌ Personal information section not found or invalid")
                return None
            
            return personal_info
            
        except Exception as e:
            print(f"❌ Error extracting personal information: {str(e)}")
            return None
    
    def create_sample_user_profile(self) -> bool:
        """
        Create a sample user profile file for reference.
        
        Returns:
            True if sample file created successfully, False otherwise
        """
        try:
            sample_data = {
                "personal_information": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "password": "SecurePassword123",
                    "phone": "+1-555-0123",
                    "address": {
                        "street": "123 Main Street",
                        "city": "New York",
                        "state": "NY",
                        "zipcode": "10001",
                        "country": "United States"
                    },
                    "professional_info": {
                        "current_position": "Software Engineer",
                        "years_of_experience": 5,
                        "skills": ["Python", "JavaScript", "React", "Node.js"],
                        "education": {
                            "degree": "Bachelor of Science in Computer Science",
                            "university": "Tech University",
                            "graduation_year": 2019
                        }
                    }
                },
                "preferences": {
                    "job_types": ["Full-time", "Remote"],
                    "salary_range": {
                        "min": 80000,
                        "max": 120000,
                        "currency": "USD"
                    }
                }
            }
            
            sample_file_path = os.path.join(
                self.paths.data_directory, 
                'user_profile_sample.json'
            )
            
            with open(sample_file_path, 'w', encoding='utf-8') as file:
                json.dump(sample_data, file, indent=2, ensure_ascii=False)
            
            print(f"✅ Sample user profile created: {sample_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating sample user profile: {str(e)}")
            return False
