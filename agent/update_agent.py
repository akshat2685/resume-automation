import os
import json
import subprocess
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

# Detect if running in CI (GitHub Actions)
IS_CI = os.getenv("CI", "").lower() == "true"

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
        json.dump(data, f, indent=2, ensure_ascii=False)
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
        with open(ACTIVITY_INPUT_PATH, "w", encoding="utf-8") as f:
            f.write("# Write any manual activities (certifications, courses, LinkedIn updates) below.\n")
            f.write("# One entry per line. Example: Completed AWS Cloud Practitioner Certification\n")
        return ""

    with open(ACTIVITY_INPUT_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    return "\n".join(entries)

def clean_activity_file():
    with open(ACTIVITY_INPUT_PATH, "w", encoding="utf-8") as f:
        f.write("# Write any manual activities (certifications, courses, LinkedIn updates) below.\n")
        f.write("# One entry per line. Example: Completed AWS Cloud Practitioner Certification\n")
    print("Activity input file cleared.")

def git_commit_and_push():
    """Commit and push portfolio data changes to GitHub."""
    print("Checking for portfolio data changes...")
    try:
        status_res = subprocess.run(
            ["git", "status", "--porcelain", PORTFOLIO_DATA_PATH],
            capture_output=True, text=True, check=True
        )
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
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
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
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""You are an intelligent Resume and Portfolio update agent for Akshat Jain.
Your task is to review new technical activities and intelligently MERGE them into the existing portfolio data.

CRITICAL RULES — follow these exactly:

## PLACEMENT RULES (do NOT just append to the end of arrays):

1. **skills** (array of objects with category + items):
   - If a new skill fits an EXISTING category, INSERT it into that category's items array (place it alongside related skills).
   - If a new skill does NOT fit any existing category, create a new category object and INSERT it in the logical position (e.g., a new language goes near the "Languages" category, not at the end).
   - NEVER duplicate a skill that already exists.
   - Keep each category to a maximum of 6 items.

2. **projects** (array of objects with title, tech, desc, link, img):
   - INSERT new projects at the BEGINNING of the array (index 0) so the most recent projects appear first.
   - Keep a maximum of 8 projects total. If adding a new one would exceed 8, remove the OLDEST project (last in the array).
   - For img, use an Unsplash URL with a relevant tech keyword: https://images.unsplash.com/photo-XXXXX?w=800&q=80 (use a real photo ID from common tech stock photos).

3. **certifications** (array of strings):
   - INSERT new certifications at the BEGINNING of the array (most recent first).
   - NEVER duplicate a certification that already exists.
   - Maximum 10 certifications. Remove the oldest if exceeded.

4. **currentlyBuilding** (array of strings):
   - INSERT new items at the BEGINNING (most active first).
   - If a currently-building item appears COMPLETED in the logs (e.g., "launched", "released", "deployed"), REMOVE it from this list.
   - NEVER duplicate.
   - Maximum 8 items.

5. **services** (array of objects with title + desc):
   - ONLY add a new service if it represents a genuinely NEW type of offering not covered by existing services.
   - INSERT in the logical position, NOT at the end.
   - NEVER duplicate.

## CONTENT RULES:
- Do NOT add React, Next.js, or SQL as tech tags unless the project explicitly uses them heavily. Prefer Python, C++, TypeScript, Docker, etc.
- Do NOT add hello-world repos, test repos, config repos, or forks as projects.
- Generate clean, professional descriptions (2-3 sentences max).
- Tech tags should reflect the actual stack used (max 4 tags per project).

## STRUCTURE RULES:
- Maintain the EXACT JSON structure: {{"skills": [...], "services": [...], "projects": [...], "certifications": [...], "currentlyBuilding": [...]}}
- Return ONLY valid JSON. No markdown code fences, no comments, no extra text.

CURRENT PORTFOLIO DATA:
{json.dumps(current_data, indent=2)}

NEW GITHUB REPOSITORIES & LANGUAGES:
{json.dumps(github_data, indent=2)}

NEW MANUAL ACTIVITIES (Certifications, Courses, LinkedIn Updates, etc.):
{local_activities if local_activities else "(none)"}

NEW CONTINUOUS MONITORING LOGS (Daily background checks):
{json.dumps(daily_logs, indent=2) if daily_logs else "(none)"}

Return the COMPLETE updated JSON payload now:"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Strip markdown code fences if Gemini added them anyway
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        updated_data = json.loads(response_text)

        # Verify structure
        required_keys = ["skills", "services", "projects", "certifications", "currentlyBuilding"]
        if not all(key in updated_data for key in required_keys):
            print("Error: Gemini returned JSON with missing structure keys.")
            print("Response:", response_text[:500])
            return

        save_data(updated_data)

        # Only push from local daemon, NOT from CI (GitHub Actions handles its own commit)
        if not IS_CI:
            git_commit_and_push()

        if local_activities:
            clean_activity_file()
        if daily_logs:
            clean_daily_logs()

        print("Portfolio update completed successfully.")

    except json.JSONDecodeError as e:
        print(f"Error: Gemini returned invalid JSON: {e}")
        print("Raw response (first 500 chars):", response_text[:500] if 'response_text' in dir() else "N/A")
    except Exception as e:
        print(f"Error during AI reasoning or update: {e}")

if __name__ == "__main__":
    run_agent()
