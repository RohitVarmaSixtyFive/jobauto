# Job Application Automation System

A comprehensive, modular system for automating job applications on Workday-based platforms. This system handles authentication, form filling, and various application sections including personal information, work experience, education, skills, and voluntary disclosures.

## Features

- **Automated Authentication**: Support for both sign-in and sign-up processes
- **Personal Information Form**: Automatically fills personal details, address, contact information
- **Work Experience**: Handles multiple work experiences with add functionality
- **Education**: Manages education history with degree, institution, and date information
- **Skills Management**: Intelligent handling of skills and technologies with multi-select support
- **Voluntary Disclosures**: Proper handling of diversity and inclusion questions
- **Resume Upload**: Automatic resume file upload
- **AI-Powered Form Filling**: Uses OpenAI to intelligently map user data to form fields
- **Comprehensive Logging**: Detailed logs of all actions and form submissions
- **Modular Architecture**: Clean, maintainable code structure

## Supported Companies

The system currently supports job applications for:
- NVIDIA
- Salesforce
- Hitachi
- ICF
- Harris Computer

## Installation

1. Clone or download the repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   playwright install
   ```
4. Copy the environment file and add your OpenAI API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Configuration

### User Profile Setup

Edit `data/user_profile.json` with your personal information. The file should include:

```json
{
  "personal_information": {
    "name": "Your Name",
    "first_name": "Your First Name",
    "last_name": "Your Last Name",
    "email": "your.email@example.com",
    "password": "YourPassword",
    "phone": "1234567890",
    "address": {
      "street": "123 Main St",
      "city": "Your City",
      "state": "Your State",
      "postalCode": "12345",
      "country": "United States of America"
    }
  },
  "work_experience": [
    {
      "company": "Company Name",
      "location": "City, State",
      "jobTitle": "Your Job Title",
      "duration": "Jan 2020 – Present",
      "responsibilities": ["Responsibility 1", "Responsibility 2"]
    }
  ],
  "education": [
    {
      "degree": "Your Degree",
      "field_of_study": "Your Field",
      "institution": "University Name",
      "location": "City, State",
      "graduation_year": "2020"
    }
  ],
  "technical_skills": {
    "programming_languages": ["Python", "JavaScript", "Java"]
  },
  "documents": {
    "resume_path": "/path/to/your/resume.pdf"
  }
}
```

### Environment Variables

Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Basic Usage

Run the main script:
```bash
python final.py
```

The script will prompt you to:
1. Choose authentication method (1 for sign-in, 2 for sign-up)
2. Select the company to apply to

### Programmatic Usage

```python
import asyncio
from final import JobApplicationBot

async def apply_to_jobs():
    bot = JobApplicationBot()
    await bot.run_full_application(company="nvidia", auth_type=1)

asyncio.run(apply_to_jobs())
```

## Architecture

### Main Components

1. **JobApplicationBot**: Main orchestrator class
2. **Authentication Handler**: Manages sign-in/sign-up processes
3. **Form Processors**: Specialized handlers for different form sections
4. **AI Integration**: OpenAI-powered form field mapping
5. **Element Extractors**: DOM element analysis and information extraction
6. **Logging System**: Comprehensive action and result logging

### Key Methods

- `initialize_browser()`: Sets up Playwright browser instance
- `navigate_to_job()`: Navigates to the job application page
- `handle_authentication()`: Manages login/signup process
- `process_application_form()`: Main form processing orchestrator
- `_process_*_section()`: Specialized section processors
- `_get_ai_response_for_section()`: AI-powered form mapping
- `_fill_form_elements()`: Element filling logic

### Form Section Handlers

- **Personal Information**: Basic contact and address information
- **Work Experience**: Multiple work history entries with dates
- **Education**: Academic background and degrees
- **Skills**: Technical and soft skills with multi-select support
- **Application Questions**: Company-specific questions
- **Voluntary Disclosures**: Diversity and inclusion information
- **Resume Upload**: Document upload handling
- **Disability Disclosures**: Accessibility-related questions

## Advanced Features

### AI-Powered Form Mapping

The system uses OpenAI's GPT-4 to intelligently map user profile data to form fields. This includes:
- Context-aware field identification
- Option matching for dropdowns
- Date format handling
- Skills array processing
- Fallback handling for unknown fields

### Multi-Select Container Handling

Special handling for complex form elements like skills input:
- Automatic detection of multi-select containers
- Array-based skill addition
- Dynamic skill entry with keyboard interactions

### Comprehensive Error Handling

- Graceful degradation on element not found
- Detailed error logging
- Retry mechanisms for unstable elements
- Session recovery capabilities

### Logging and Debugging

The system creates detailed logs in the `logs/` directory:
- Action logs for each form section
- Element interaction records
- AI response mappings
- Error traces and debugging information

## Troubleshooting

### Common Issues

1. **Browser doesn't open**: Ensure Playwright is properly installed
2. **Elements not found**: Form structures may have changed; check selectors
3. **AI responses incorrect**: Verify OpenAI API key and model access
4. **File upload fails**: Check file paths and permissions

### Debug Mode

Run with additional logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Intervention

The system runs with `headless=False` by default, allowing you to:
- Monitor the automation process
- Manually intervene if needed
- Debug form interaction issues

## Security Considerations

- Store sensitive information securely
- Use environment variables for API keys
- Review logs before sharing
- Consider using separate test credentials

## Contributing

To extend the system:
1. Add new company URLs to `company_urls` dictionary
2. Create specialized section processors for unique form types
3. Extend the AI prompt for better field mapping
4. Add new element types to the form handlers

## License

This project is for educational and personal use. Please respect the terms of service of the job application platforms you use this with.

## Disclaimer

This tool is designed to assist with job applications by automating form filling. Users are responsible for:
- Ensuring accuracy of submitted information
- Complying with platform terms of service
- Respecting rate limits and usage policies
- Verifying all submitted applications
