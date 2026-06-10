import os
import sys
import time
import json
import subprocess
import requests
import ctypes
from datetime import datetime

# Windows ctypes structure to check idle time
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

# Configuration
GITHUB_USERNAME = "akshat2685"
MONITORED_DIRS = [
    r"C:\Users\ijain\Desktop",
    r"C:\Users\ijain\Desktop\akshat",
    r"C:\Users\ijain\AKSHAT_software_engineer"
]
LINKEDIN_PROFILE_URL = "https://www.linkedin.com/in/akshat-jain-02530a26a" # Default or customizable

# Logs path
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
DAILY_LOGS_PATH = os.path.join(AGENT_DIR, "daily_logs.json")
DAEMON_LOG_PATH = os.path.join(AGENT_DIR, "daemon.log")

def log_message(message):
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] {message}\n"
    print(log_line.strip())
    with open(DAEMON_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line)

def get_idle_duration():
    """Returns the idle time of the user in seconds."""
    if sys.platform != "win32":
        return 0.0
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(lii)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    return 0.0

def load_daily_logs():
    if not os.path.exists(DAILY_LOGS_PATH):
        return []
    try:
        with open(DAILY_LOGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_message(f"Error loading daily logs JSON: {e}")
        return []

def save_daily_logs(logs):
    try:
        with open(DAILY_LOGS_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        log_message(f"Error saving daily logs JSON: {e}")

def add_log_entry(source, description):
    logs = load_daily_logs()
    
    # Check if duplicate entry already exists in current logs
    for entry in logs:
        if entry["source"] == source and entry["description"] == description:
            return
            
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "description": description
    }
    logs.append(new_entry)
    save_daily_logs(logs)
    log_message(f"Added new event ({source}): {description}")

def fetch_github_events():
    """Fetch recent GitHub activities for the user."""
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/events/public"
    log_message(f"Polling GitHub public events for {GITHUB_USERNAME}...")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            events = response.json()
            for event in events[:10]: # Check last 10 events
                event_type = event.get("type")
                repo_name = event.get("repo", {}).get("name")
                
                if event_type == "PushEvent":
                    commits = event.get("payload", {}).get("commits", [])
                    for commit in commits:
                        message = commit.get("message", "")
                        # Filter out merge commits or trivial commits
                        if not message.startswith("Merge branch") and len(message) > 5:
                            add_log_entry("github", f"Committed to {repo_name}: {message}")
                elif event_type == "CreateEvent":
                    ref_type = event.get("payload", {}).get("ref_type")
                    if ref_type == "repository":
                        add_log_entry("github", f"Created repository: {repo_name}")
        else:
            log_message(f"GitHub API returned status code {response.status_code}")
    except Exception as e:
        log_message(f"Error fetching GitHub events: {e}")

def scan_local_git_repos():
    """Scans local directories for Git repositories and fetches recent commits."""
    log_message("Scanning local Git repositories...")
    found_repos = set()
    
    for base_dir in MONITORED_DIRS:
        if not os.path.exists(base_dir):
            continue
        try:
            # List immediate subdirectories
            for entry in os.listdir(base_dir):
                full_path = os.path.join(base_dir, entry)
                if os.path.isdir(full_path):
                    git_dir = os.path.join(full_path, ".git")
                    if os.path.isdir(git_dir):
                        found_repos.add(full_path)
                    # Support one layer deeper (e.g. C:\Users\ijain\Desktop\akshat\my-repo)
                    try:
                        for sub_entry in os.listdir(full_path):
                            sub_path = os.path.join(full_path, sub_entry)
                            if os.path.isdir(sub_path):
                                sub_git_dir = os.path.join(sub_path, ".git")
                                if os.path.isdir(sub_git_dir):
                                    found_repos.add(sub_path)
                    except Exception:
                        pass
        except Exception as e:
            log_message(f"Error scanning directory {base_dir}: {e}")

    for repo_path in found_repos:
        try:
            # Query commits in last 24 hours
            # Format: hash|message
            cmd = ["git", "log", "--since=24.hours.ago", "--pretty=format:%h|%s"]
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            if output:
                repo_name = os.path.basename(repo_path)
                lines = output.split("\n")
                for line in lines:
                    if "|" in line:
                        _, commit_msg = line.split("|", 1)
                        if not commit_msg.startswith("Merge branch") and len(commit_msg) > 5:
                            add_log_entry("local_git", f"Local commit in '{repo_name}': {commit_msg}")
        except Exception as e:
            # Silent fallback if git fails or directory changes
            pass

def copy_profile_safely(src_dir, dest_dir):
    import shutil
    if not os.path.exists(src_dir):
        return False
    try:
        os.makedirs(dest_dir, exist_ok=True)
        # Copy Local State
        local_state_src = os.path.join(src_dir, "Local State")
        if os.path.exists(local_state_src):
            try:
                shutil.copy2(local_state_src, os.path.join(dest_dir, "Local State"))
            except Exception:
                pass
        # Copy Default directory structure selectively
        default_src = os.path.join(src_dir, "Default")
        default_dest = os.path.join(dest_dir, "Default")
        if os.path.exists(default_src):
            os.makedirs(default_dest, exist_ok=True)
            to_copy = [
                ("Preferences", False),
                ("Secure Preferences", False),
                ("Network", True),
                ("Local Storage", True),
            ]
            for name, is_dir in to_copy:
                item_src = os.path.join(default_src, name)
                item_dest = os.path.join(default_dest, name)
                if os.path.exists(item_src):
                    try:
                        if is_dir:
                            shutil.copytree(item_src, item_dest, dirs_exist_ok=True,
                                            ignore=shutil.ignore_patterns("Cache*", "*cache*", "*Log*", "*.ldb"))
                        else:
                            shutil.copy2(item_src, item_dest)
                    except Exception:
                        pass
        return True
    except Exception as e:
        log_message(f"Error copying profile for persistent context: {e}")
        return False

def scrape_linkedin_activity():
    """Launches Playwright using copied user profile to bypass authwall."""
    log_message("Polling LinkedIn profile activity...")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log_message("Playwright not installed, skipping LinkedIn scan.")
        return

    # Check potential profile directories
    profiles = [
        (r"C:\Users\ijain\AppData\Local\Google\Chrome\User Data", "chrome"),
        (r"C:\Users\ijain\AppData\Local\Microsoft\Edge\User Data", "msedge")
    ]

    temp_profile_dir = os.path.join(AGENT_DIR, "linkedin_profile_temp")
    used_persistent = False
    browser_channel = "chrome"

    # Try copying profile
    for path, channel in profiles:
        if os.path.exists(path):
            log_message(f"Attempting to copy browser profile for {channel} from {path}...")
            if copy_profile_safely(path, temp_profile_dir):
                used_persistent = True
                browser_channel = channel
                break

    try:
        with sync_playwright() as p:
            if used_persistent:
                log_message(f"Launching persistent context using {browser_channel} copy...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=temp_profile_dir,
                    channel=browser_channel,
                    headless=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            else:
                log_message("No browser profile copied. Launching clean context...")
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

            page = context.new_page()
            activity_url = LINKEDIN_PROFILE_URL.rstrip("/") + "/recent-activity/all/"
            log_message(f"Navigating to {activity_url}...")
            try:
                page.goto(activity_url, wait_until="domcontentloaded", timeout=20000)
            except Exception as e:
                log_message(f"Navigation timeout/error: {e}")
            
            # Wait 3 seconds for client-side redirects to settle
            page.wait_for_timeout(3000)
            stable_url = page.url
            log_message(f"Stable URL reached: {stable_url}")
            
            # Check if we were redirected to login/authwall
            parsed_url = stable_url.lower()
            if "login" in parsed_url or "signup" in parsed_url or "authwall" in parsed_url:
                log_message("LinkedIn requested login. Skipping LinkedIn updates.")
            else:
                try:
                    # Try to locate posts (supporting both recent-activity and main profile pages)
                    selectors = [
                        ".feed-shared-update-v2__description", 
                        ".feed-shared-text",
                        ".description-profile-section"
                    ]
                    posts = []
                    for sel in selectors:
                        elements = page.locator(sel).all_text_contents()
                        if elements:
                            posts = elements
                            break
                            
                    for post in posts[:3]:
                        cleaned_post = post.strip()
                        if len(cleaned_post) > 10:
                            snippet = cleaned_post[:150] + "..." if len(cleaned_post) > 150 else cleaned_post
                            add_log_entry("linkedin", f"Posted on LinkedIn: {snippet}")
                except Exception as eval_err:
                    log_message(f"Error extracting posts from page: {eval_err}")
            
            context.close()
    except Exception as e:
        log_message(f"Error scraping LinkedIn: {e}")
    finally:
        # Clean up copied directory
        if used_persistent and os.path.exists(temp_profile_dir):
            import shutil
            try:
                shutil.rmtree(temp_profile_dir)
                log_message("Cleaned up temporary profile directory.")
            except Exception as e:
                log_message(f"Warning: Could not clean up temp profile directory: {e}")

def run_daemon_loop():
    log_message("Starting Portfolio Continuous Monitoring Daemon...")
    active_minutes_today = 0
    last_date = datetime.now().date()
    last_weekly_update_date = None
    
    while True:
        current_time = datetime.now()
        current_date = current_time.date()
        
        # Saturday 8:00 PM IST (Hour 20) Weekly Update Trigger
        if current_time.weekday() == 5 and current_time.hour == 20 and last_weekly_update_date != current_date:
            log_message("It is Saturday 8:00 PM IST. Triggering weekly portfolio integration...")
            try:
                update_script = os.path.join(AGENT_DIR, "update_agent.py")
                python_exe = sys.executable
                log_message(f"Running weekly update: {python_exe} {update_script}")
                subprocess.run([python_exe, update_script], check=True)
                last_weekly_update_date = current_date
                log_message("Weekly portfolio integration completed successfully.")
            except Exception as e:
                log_message(f"Error during weekly portfolio integration: {e}")
        
        # Reset daily active counter if date changes
        if current_date != last_date:
            active_minutes_today = 0
            last_date = current_date
            log_message("New day started. Active monitor counter reset.")
            
        idle_time = get_idle_duration()
        is_active = idle_time < 300 # User active in the last 5 minutes
        
        # If user is active and we haven't exceeded 5 hours of monitoring today (300 minutes)
        if is_active and active_minutes_today < 300:
            active_minutes_today += 5
            log_message(f"User is active. Monitoring time today: {active_minutes_today}/300 minutes.")
            
            # Poll activities once every hour (or every 12 check-loops since check-loop runs every 5 minutes)
            if active_minutes_today % 60 == 0 or active_minutes_today == 5:
                log_message("Performing periodic polling of all sources...")
                fetch_github_events()
                scan_local_git_repos()
                scrape_linkedin_activity()
        elif not is_active:
            # Idle, do nothing
            pass
        else:
            # We already monitored 5 hours today, sleep until next check
            pass
            
        # Sleep for 5 minutes before checking active status again
        time.sleep(300)

if __name__ == "__main__":
    try:
        # Create empty logs file if not exists
        if not os.path.exists(DAILY_LOGS_PATH):
            save_daily_logs([])
        run_daemon_loop()
    except KeyboardInterrupt:
        log_message("Daemon stopped by user.")
    except Exception as e:
        log_message(f"Fatal daemon error: {e}")
