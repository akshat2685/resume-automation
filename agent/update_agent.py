import os
import json
import requests
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Load local environment variables if .env file exists
load_dotenv()

# Configure APIs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("CLOUD_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = "akshat2685"

# File paths
PORTFOLIO_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "data", "portfolioData.json"))
ACTIVITY_INPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "activity_inputs.txt"))
DAILY_LOGS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "daily_logs.json"))

def load_current_data():
    if not os.path.exists(PORTFOLIO_DATA_PATH):
        raise FileNotFoundError(f"Portfolio data file not found at: {PORTFOLIO_DATA_PATH}")
    with open(PORTFOLIO_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(PORTFOLIO_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Portfolio data updated successfully.")

def read_daily_logs():
    if not os.path.exists(DAILY_LOGS_PATH):
        return []
    try:
        with open(DAILY_LOGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading daily logs: {e}")
        return []

def clean_daily_logs():
    try:
        with open(DAILY_LOGS_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        print("Daily logs cleared.")
    except Exception as e:
        print(f"Error clearing daily logs: {e}")

def fetch_github_data():
    print("Fetching GitHub activity...")
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # Fetch user repos
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?sort=updated&per_page=10"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch GitHub repos: {response.status_code} - {response.text}")
            return []
        repos = response.json()
        
        repo_data = []
        for r in repos:
            if r.get("fork"):
                continue
            # Get languages for this repo
            lang_url = r.get("languages_url")
            langs = []
            if lang_url:
                lang_res = requests.get(lang_url, headers=headers, timeout=5)
                if lang_res.status_code == 200:
                    langs = list(lang_res.json().keys())
            
            repo_data.append({
                "name": r.get("name"),
                "description": r.get("description") or "",
                "url": r.get("html_url"),
                "languages": langs,
                "updated_at": r.get("updated_at"),
                "stars": r.get("stargazers_count")
            })
        return repo_data
    except Exception as e:
        print(f"Error fetching GitHub data: {e}")
        return []

def read_local_activities():
    if not os.path.exists(ACTIVITY_INPUT_PATH):
        # Create empty template if not exists
        with open(ACTIVITY_INPUT_PATH, "w", encoding="utf-8") as f:
            f.write("# Write any manual activities (certifications, courses, LinkedIn updates) below.\n")
            f.write("# One entry per line. Example: Completed AWS Cloud Practitioner Certification\n")
        return ""
    
    with open(ACTIVITY_INPUT_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Filter comments and empty lines
    entries = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    return "\n".join(entries)

def clean_activity_file():
    # Keep the template but clear the entries after a successful run
    with open(ACTIVITY_INPUT_PATH, "w", encoding="utf-8") as f:
        f.write("# Write any manual activities (certifications, courses, LinkedIn updates) below.\n")
        f.write("# One entry per line. Example: Completed AWS Cloud Practitioner Certification\n")
    print("Activity input file cleared.")

def git_commit_and_push():
    print("Checking for portfolio data changes...")
    try:
        import subprocess
        # Check if portfolioData.json has changes
        status_res = subprocess.run(["git", "status", "--porcelain", PORTFOLIO_DATA_PATH], capture_output=True, text=True, check=True)
        if not status_res.stdout.strip():
            print("No changes in portfolio data. Skipping git commit and push.")
            return

        print("Committing and pushing changes to GitHub...")
        subprocess.run(["git", "add", PORTFOLIO_DATA_PATH], check=True)
        subprocess.run(["git", "commit", "-m", "chore: auto-update portfolio data with weekly activities"], check=True)
        
        if GITHUB_TOKEN:
            push_url = f"https://{GITHUB_TOKEN}@github.com/akshat2685/resume-automation.git"
            subprocess.run(["git", "push", push_url, "main"], check=True)
        else:
            subprocess.run(["git", "push", "origin", "main"], check=True)
        print("GitHub push completed successfully.")
    except Exception as e:
        print(f"Error during Git commit/push: {e}")

def run_agent():
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY environment variable is not set. Running in dry-run/mock mode.")
        return

    genai.configure(api_key=GEMINI_API_KEY)
    
    try:
        current_data = load_current_data()
    except Exception as e:
        print(f"Error loading current data: {e}")
        return

    github_data = fetch_github_data()
    local_activities = read_local_activities()
    daily_logs = read_daily_logs()
    
    if not github_data and not local_activities and not daily_logs:
        print("No new activity found. Portfolio is up to date.")
        return

    print("Analyzing updates with Gemini...")
    model = genai.GenerativeModel("gemini-3.5-flash")

    prompt = f"""
    You are an intelligent Resume and Portfolio updates agent for Akshat Jain.
    Your task is to review new technical activities and intelligently update the current portfolio data JSON structure.

    Current Portfolio Data:
    {json.dumps(current_data, indent=2)}

    New GitHub Repositories & Languages:
    {json.dumps(github_data, indent=2)}

    New Manual Activities (Certifications, LinkedIn Updates, etc.):
    {local_activities}

    New Continuous Monitoring Logs (Daily background checks):
    {json.dumps(daily_logs, indent=2)}

    Instructions:
    1. Look at the New GitHub Repositories and Continuous Monitoring Logs. If there is a new project or repository that represents a substantial tech effort (not a simple hello-world or fork), add it to the "projects" list. Generate a clean, professional description and tech tags (e.g. Python, OCR, etc.). Note: Do not add React/Next.js/SQL unless explicitly mentioned. Prefer Python, C++, Three.js, etc.
    2. Check the languages used in new repos and logs. If a new language or tool (like a Python library or Vite tool) is heavily used but not present in "skills", add it under the appropriate category in "skills".
    3. Look at New Manual Activities and Monitoring Logs. If a certification, course completion, or new skill is listed, add it to the "certifications" list or "skills" list.
    4. Maintain the exact same JSON keys and structure: "skills" (array of {{category, items}}), "services" (array of {{title, desc}}), "projects" (array of {{title, tech, desc, link, img}}), "certifications" (array of strings), "currentlyBuilding" (array of strings).
    5. Return ONLY the complete updated JSON payload. Do not include markdown code block formatting (no ```json or ``` wrapper), just return raw JSON text.
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Strip markdown if Gemini ignored instructions
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        updated_data = json.loads(response_text)
        
        # Verify structure
        required_keys = ["skills", "services", "projects", "certifications", "currentlyBuilding"]
        if all(key in updated_data for key in required_keys):
            save_data(updated_data)
            # Commit and push to GitHub
            git_commit_and_push()
            if local_activities:
                clean_activity_file()
            if daily_logs:
                clean_daily_logs()
        else:
            print("Error: Gemini returned JSON with missing structure keys.")
            print("Response:", response_text)
    except Exception as e:
        print(f"Error during AI reasoning or update: {e}")

if __name__ == "__main__":
    run_agent()
