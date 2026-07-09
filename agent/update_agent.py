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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = "akshat2685"

# NVIDIA NIM configuration (fallback provider)
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.1-8b-instruct"

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
            # Prevent printing the GITHUB_TOKEN in traceback/stdout by capturing output and handling failure manually
            res = subprocess.run(["git", "push", push_url, "main"], capture_output=True, text=True)
            if res.returncode != 0:
                # Sanitize token from output/error message
                err_msg = res.stderr or ""
                if GITHUB_TOKEN in err_msg:
                    err_msg = err_msg.replace(GITHUB_TOKEN, "********")
                print(f"Git push failed (exit code {res.returncode}): {err_msg.strip()}")
                raise Exception("Git push failed. Token hidden for security.")
        else:
            subprocess.run(["git", "push", "origin", "main"], check=True)
        print("GitHub push completed successfully.")
    except subprocess.CalledProcessError as e:
        # Clean up token from exception message if it got raised elsewhere
        cmd_str = str(e.cmd)
        if GITHUB_TOKEN and GITHUB_TOKEN in cmd_str:
            cmd_str = cmd_str.replace(GITHUB_TOKEN, "********")
        print(f"Git command failed: cmd={cmd_str}, returncode={e.returncode}")
    except Exception as e:
        err_str = str(e)
        if GITHUB_TOKEN and GITHUB_TOKEN in err_str:
            err_str = err_str.replace(GITHUB_TOKEN, "********")
        print(f"Error during Git commit/push: {err_str}")

def call_gemini(prompt: str) -> str:
    """Call Gemini API. Raises on any error (quota, auth, etc.) so caller can fall back."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

def call_nvidia_nim(prompt: str) -> str:
    """Call NVIDIA NIM API as fallback. Raises on any error."""
    if not NVIDIA_API_KEY:
        raise ValueError("NVIDIA_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4000,
    }
    response = requests.post(
        f"{NVIDIA_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    if response.status_code != 200:
        raise Exception(f"NVIDIA NIM API error: {response.status_code} - {response.text}")
    return response.json()["choices"][0]["message"]["content"].strip()

def call_llm(prompt: str) -> tuple[str, str]:
    """Try Gemini first; fall back to NVIDIA NIM on quota/auth/any error.

    Uses whichever provider has available quota. Falls back gracefully so the
    weekly Saturday update never silently fails due to one provider's limits.
    """
    # Provider 1: Gemini (preferred)
    if GEMINI_API_KEY:
        try:
            print("Trying Gemini (gemini-2.0-flash)...")
            result = call_gemini(prompt)
            print("Gemini succeeded.")
            return result, "gemini-2.0-flash"
        except Exception as e:
            print(f"Gemini failed ({type(e).__name__}): {e}")
            print("Falling back to NVIDIA NIM...")
    else:
        print("GEMINI_API_KEY not set. Using NVIDIA NIM.")

    # Provider 2: NVIDIA NIM (fallback)
    if not NVIDIA_API_KEY:
        raise ValueError("No LLM provider available: both GEMINI_API_KEY and NVIDIA_API_KEY are missing/failed.")
    result = call_nvidia_nim(prompt)
    print("NVIDIA NIM succeeded.")
    return result, NVIDIA_MODEL

def run_agent():
    if not GEMINI_API_KEY and not NVIDIA_API_KEY:
        print("Warning: Neither GEMINI_API_KEY nor NVIDIA_API_KEY is set. Running in dry-run/mock mode.")
        return

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
        response_text, model_used = call_llm(prompt)
        raw_response = response_text  # Keep a copy for error reporting

        # Strip markdown code fences if the model added them anyway
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Extract JSON from response (handles extra trailing text)
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start >= 0 and end > start:
            response_text = response_text[start:end]

        updated_data = json.loads(response_text)

        # Verify structure
        required_keys = ["skills", "services", "projects", "certifications", "currentlyBuilding"]
        if not all(key in updated_data for key in required_keys):
            print(f"Error: {model_used} returned JSON with missing structure keys.")
            print("Response:", response_text[:500])
            return

        save_data(updated_data)
        print(f"Portfolio data updated using {model_used}.")

        # Only push from local daemon, NOT from CI (GitHub Actions handles its own commit)
        if not IS_CI:
            git_commit_and_push()

        if local_activities:
            clean_activity_file()
        if daily_logs:
            clean_daily_logs()

        print("Portfolio update completed successfully.")

    except json.JSONDecodeError as e:
        print(f"Error: LLM returned invalid JSON: {e}")
        print("Raw response (first 500 chars):", raw_response[:500] if 'raw_response' in dir() else "N/A")
    except Exception as e:
        print(f"Error during AI reasoning or update: {e}")

if __name__ == "__main__":
    run_agent()
