# Jobauto – `final.ipynb` Notebook

This notebook automates job applications on Workday-powered portals (e.g., NVIDIA, Hitachi) using Playwright and OpenAI. It fills out sign-in/sign-up, personal info, experience, education, and other form sections by mapping your user profile data to the web form fields.

---

## Features

- **Automated browser navigation** using Playwright (async, Chromium)
- **Sign In / Sign Up**: Fills credentials from your profile
- **Dynamic field handling**: Text, radio, listbox, dropdown, textarea, etc.
- **AI-powered field mapping**: Uses OpenAI to select the best answers/options for each question based on your profile
- **Experience/Education panels**: Loops through your work/education history and fills each section
- **Logs progress** and prints detailed debug info for each step

---

## Requirements

- Python 3.8+
- [Playwright](https://playwright.dev/python/) (`pip install playwright`)
- [OpenAI Python SDK](https://github.com/openai/openai-python) (`pip install openai`)
- [python-dotenv](https://pypi.org/project/python-dotenv/) (`pip install python-dotenv`)
- A valid OpenAI API key (set in `.env` as `OPENAI_API_KEY`)
- User profile JSON at `data/user_profile.json` (see below for format)

---

## Usage

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **Set up your OpenAI API key:**
   - Create a `.env` file in the project root:
     ```
     OPENAI_API_KEY=sk-...
     ```

3. **Prepare your user profile:**
   - Edit `data/user_profile.json` with your info:
     ```json
     {
       "personal_information": {
         "email": "your@email.com",
         "password": "yourpassword",
         ...
       },
       "work_experience": [
         {
           "company": "...",
           "title": "...",
           ...
         }
       ],
       "education": [
         {
           "school": "...",
           "degree": "...",
           ...
         }
       ]
     }
     ```

4. **Run the notebook:**
   - Open `final.ipynb` in VS Code or Jupyter.
   - Run all cells in order.
   - Follow prompts in the terminal (choose sign-in or sign-up).
   - The browser will open and fill the application automatically.

---

## How It Works

- **Browser Automation:** Launches Chromium, navigates to the job application URL, and waits for the page to load.
- **Sign In/Up:** Prompts you to choose sign-in or sign-up, then fills credentials from your profile.
- **Form Filling:** For each page/section:
  - **Text, radio, dropdowns, listboxes:** Uses OpenAI to map your profile data to the best answer/option.
  - **Experience/Education:** Loops through your entries and fills each panel.
  - **Skills, prompts, and other fields:** Handles dynamically, selecting options or skipping as needed.
- **AI Mapping:** Prompts OpenAI with your profile and the field/question/options, and fills the field with the AI's response.
- **Debug Output:** Prints each step, field, and AI decision for transparency and troubleshooting.

---

## Notes

- **Supported Portals:** Designed for Workday-based job portals (tested on NVIDIA, Hitachi, Salesforce, etc.).
- **Extensibility:** You can adapt the selectors and logic for other portals or custom fields.
- **Safety:** No credentials or data are sent anywhere except to OpenAI for field mapping.

---

## Disclaimer

This notebook is for educational and personal automation purposes only. Use responsibly and at your own risk. Do not use for spamming or