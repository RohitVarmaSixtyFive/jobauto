# Jobauto

Jobauto is an automated job application tool that fills out and submits job applications on the NVIDIA Workday portal using user profile data. It leverages browser automation to complete each step of the application process, logging progress and results for each page.

## Features
- Automated browser-based job application workflow
- Modular page handlers for each step (sign-in, information, application, education, skills, resume, disclosures, etc.)
- User profile and logs stored as JSON
- Easily configurable and extensible

## Usage
1. **Install dependencies** (requires Python 3.8+):
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure your user profile** in `data/user_profile.json`.
3. **Run the main script:**
   ```bash
   python main.py
   ```
4. Logs and page data will be saved in the `logs/` directory.

## Project Structure
- `main.py` / `main.ipynb`: Entry points for running the automation
- `data/`: User profile data
- `logs/`: Application run logs and page data
- `src/`: Core modules for each application page and utilities

## Disclaimer
This project is for educational and personal automation purposes only. Use responsibly and at your own risk.
