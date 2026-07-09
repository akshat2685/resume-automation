import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime, timedelta

# ============ CONFIGURATION ============
GITHUB_USERNAME = "akshat2685"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # For private repo access

# Directories to scan for local git repos
MONITORED_DIRS = [
    r"C:\Users\ijain\Desktop",
    r"C:\Users\ijain\Desktop\akshat",
    r"C:\Users\ijain\AKSHAT_software_engineer"
]

# LinkedIn profile
LINKEDIN_PROFILE_URL = "https://www.linkedin.com/in/akshat-jain-02530a26a"

# Certificate tracking - add your certification files/paths here
CERT_PATHS = [
    r"C:\Users\ijain\OneDrive\Desktop\certificates",
    r"C:\Users\ijain\Desktop\certificates",
]

# Activity log file (fed to update_agent.py on Saturday)
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
DAILY_LOGS_PATH = os.path.join(AGENT_DIR, "daily_logs.json")
DAEMON_LOG_PATH = os.path.join(AGENT_DIR, "daemon.log")

# Schedule: Every hour at minute 0, run for 15 minutes (poll at 0, 5, 10, 15 min marks)
POLL_INTERVAL_MINUTES = 5      # Check every 5 minutes during active window
ACTIVE_WINDOW_MINUTES = 15     # Active window per hour
DAILY_MAX_HOURS = 12           # Max hours to monitor per day

# ============ LOGGING ============
def log_message(message):
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] {message}\n"
    print(log_line.strip())
    with open(DAEMON_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_line)

# ============ DAILY LOGS ============
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

def add_log_entry(source, description, metadata=None):
    """Add a structured log entry."""
    logs = load_daily_logs()
    
    # Check for duplicate
    for entry in logs:
        if entry["source"] == source and entry["description"] == description:
            return
    
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "description": description,
        "metadata": metadata or {}
    }
    logs.append(new_entry)
    save_daily_logs(logs)
    log_message(f"Added ({source}): {description}")

def clear_daily_logs():
    """Clear logs after Saturday push."""
    save_daily_logs([])
    log_message("Daily logs cleared after weekly push.")

# ============ MONITORING SOURCES ============
def fetch_github_events():
    """Fetch recent GitHub activities (public + private with token)."""
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/events"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    log_message(f"Polling GitHub events for {GITHUB_USERNAME}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            events = response.json()
            for event in events[:20]:
                event_type = event.get("type")
                repo_name = event.get("repo", {}).get("name", "unknown")
                created_at = event.get("created_at")
                
                if event_type == "PushEvent":
                    commits = event.get("payload", {}).get("commits", [])
                    for commit in commits:
                        msg = commit.get("message", "")
                        if not msg.startswith("Merge branch") and len(msg) > 5:
                            add_log_entry("github", f"Pushed to {repo_name}: {msg}", 
                                        {"repo": repo_name, "event_type": "PushEvent", "time": created_at})
                elif event_type == "CreateEvent":
                    ref_type = event.get("payload", {}).get("ref_type")
                    if ref_type == "repository":
                        add_log_entry("github", f"Created repository: {repo_name}",
                                    {"repo": repo_name, "event_type": "CreateEvent", "time": created_at})
                elif event_type == "ReleaseEvent":
                    release = event.get("payload", {}).get("release", {})
                    tag = release.get("tag_name", "")
                    add_log_entry("github", f"Released {tag} in {repo_name}",
                                {"repo": repo_name, "event_type": "ReleaseEvent", "time": created_at})
        else:
            log_message(f"GitHub API: {response.status_code}")
    except Exception as e:
        log_message(f"GitHub fetch error: {e}")

def scan_local_git_repos():
    """Scan local directories for Git repos and recent commits."""
    log_message("Scanning local Git repositories...")
    found_repos = set()
    
    for base_dir in MONITORED_DIRS:
        if not os.path.exists(base_dir):
            continue
        try:
            for entry in os.listdir(base_dir):
                full_path = os.path.join(base_dir, entry)
                if os.path.isdir(full_path):
                    if os.path.isdir(os.path.join(full_path, ".git")):
                        found_repos.add(full_path)
                    # Check one level deeper
                    try:
                        for sub_entry in os.listdir(full_path):
                            sub_path = os.path.join(full_path, sub_entry)
                            if os.path.isdir(sub_path) and os.path.isdir(os.path.join(sub_path, ".git")):
                                found_repos.add(sub_path)
                    except Exception:
                        pass
        except Exception as e:
            log_message(f"Error scanning {base_dir}: {e}")

    for repo_path in found_repos:
        try:
            # Get commits from last 24 hours
            cmd = ["git", "log", "--since=24.hours.ago", "--pretty=format:%h|%s|%ad", "--date=iso"]
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=False)
            output = result.stdout.strip()
            if output:
                repo_name = os.path.basename(repo_path)
                for line in output.split("\n"):
                    if "|" in line:
                        parts = line.split("|", 2)
                        if len(parts) >= 2:
                            _, commit_msg, commit_date = parts[0], parts[1], parts[2] if len(parts) > 2 else ""
                            if not commit_msg.startswith("Merge branch") and len(commit_msg) > 5:
                                add_log_entry("local_git", f"Local commit in '{repo_name}': {commit_msg}",
                                            {"repo": repo_name, "commit_date": commit_date})
        except Exception:
            pass

def scan_certificates():
    """Scan for new certificate files."""
    log_message("Scanning for certificates...")
    known_extensions = (".pdf", ".png", ".jpg", ".jpeg", ".cer", ".crt")
    cert_keywords = ["certificate", "cert", "diploma", "badge", "credential", "completion", "achievement"]
    
    for cert_dir in CERT_PATHS:
        if not os.path.exists(cert_dir):
            continue
        try:
            for root, dirs, files in os.walk(cert_dir):
                for f in files:
                    if f.lower().endswith(known_extensions):
                        f_lower = f.lower()
                        if any(kw in f_lower for kw in cert_keywords):
                            full_path = os.path.join(root, f)
                            # Check if modified recently (last 24h)
                            mod_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                            if datetime.now() - mod_time < timedelta(hours=24):
                                add_log_entry("certificate", f"New certificate found: {f}",
                                            {"path": full_path, "date": mod_time.isoformat()})
        except Exception as e:
            log_message(f"Certificate scan error: {e}")

def copy_browser_profile(src_dir, dest_dir):
    """Copy minimal browser profile files (Local State and Cookies) for LinkedIn auth."""
    import shutil
    if not os.path.exists(src_dir):
        return False
    try:
        os.makedirs(dest_dir, exist_ok=True)
        # Essential files list relative to src_dir
        essential_files = [
            "Local State",
            os.path.join("Default", "Cookies"),
            os.path.join("Default", "Network", "Cookies")
        ]
        copied_any = False
        for rel_path in essential_files:
            src_file = os.path.join(src_dir, rel_path)
            if os.path.exists(src_file) and os.path.isfile(src_file):
                dst_file = os.path.join(dest_dir, rel_path)
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                try:
                    # Using shutil.copy2 to copy file data and metadata
                    shutil.copy2(src_file, dst_file)
                    copied_any = True
                except Exception as e:
                    log_message(f"Could not copy {rel_path} (possibly locked/in-use): {e}")
        return copied_any
    except Exception as e:
        log_message(f"Profile copy error: {e}")
        return False

def scrape_linkedin_activity():
    """Scrape LinkedIn activity using Playwright with browser profile."""
    log_message("Polling LinkedIn activity...")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log_message("Playwright not installed.")
        return

    # Browser profile locations
    profiles = [
        (r"C:\Users\ijain\AppData\Local\Google\Chrome\User Data", "chrome"),
        (r"C:\Users\ijain\AppData\Local\Microsoft\Edge\User Data", "msedge"),
    ]

    temp_profile = os.path.join(AGENT_DIR, "linkedin_profile_temp")
    used_persistent = False
    browser_ch = "chrome"

    for path, ch in profiles:
        if os.path.exists(path):
            log_message(f"Copying {ch} profile...")
            if copy_browser_profile(path, temp_profile):
                used_persistent = True
                browser_ch = ch
                break

    try:
        with sync_playwright() as p:
            if used_persistent:
                log_message(f"Launching {browser_ch} with profile...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=temp_profile,
                    channel=browser_ch,
                    headless=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
            else:
                log_message("Launching clean browser...")
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

            page = context.new_page()
            activity_url = LINKEDIN_PROFILE_URL.rstrip("/") + "/recent-activity/all/"
            log_message(f"Navigating to LinkedIn...")
            
            try:
                page.goto(activity_url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                log_message(f"Navigation error: {e}")

            page.wait_for_timeout(5000)
            current_url = page.url.lower()
            
            if any(x in current_url for x in ["login", "signup", "authwall", "challenge"]):
                log_message("LinkedIn auth required - skipping")
            else:
                # Try multiple selectors for posts
                selectors = [
                    "[data-urn*='activity'] .feed-shared-update-v2__description",
                    ".feed-shared-text",
                    ".update-components-text",
                    "[data-test-feed-shared-text]",
                ]
                posts = []
                for sel in selectors:
                    try:
                        elements = page.locator(sel).all_text_contents()
                        if elements:
                            posts = elements
                            break
                    except Exception:
                        continue
                
                for post in posts[:5]:
                    cleaned = post.strip()
                    if len(cleaned) > 20:
                        snippet = cleaned[:200] + "..." if len(cleaned) > 200 else cleaned
                        add_log_entry("linkedin", f"LinkedIn post: {snippet}")
                
                log_message(f"Captured {len(posts)} LinkedIn posts")

            context.close()
    except Exception as e:
        log_message(f"LinkedIn scrape error: {e}")
    finally:
        # Cleanup
        if used_persistent and os.path.exists(temp_profile):
            import shutil
            try:
                shutil.rmtree(temp_profile)
            except Exception:
                pass

def run_all_polls():
    """Run all monitoring polls once."""
    log_message("=== Starting monitoring cycle ===")
    fetch_github_events()
    scan_local_git_repos()
    scan_certificates()
    scrape_linkedin_activity()
    log_message("=== Monitoring cycle complete ===")

# ============ MAIN DAEMON LOOP ============
def run_daemon():
    log_message("=" * 50)
    log_message("Portfolio Monitor Daemon Started")
    log_message(f"Schedule: Every hour at :00, active for {ACTIVE_WINDOW_MINUTES} min, polls every {POLL_INTERVAL_MINUTES} min")
    log_message(f"Weekly push: Saturday 8:00 PM IST")
    log_message("=" * 50)

    # Ensure logs exist
    if not os.path.exists(DAILY_LOGS_PATH):
        save_daily_logs([])

    daily_polls = 0
    last_date = datetime.now().date()
    last_hour = -1
    last_weekly_push = None

    while True:
        now = datetime.now()
        current_date = now.date()
        current_hour = now.hour
        current_minute = now.minute

        # --- Daily reset ---
        if current_date != last_date:
            daily_polls = 0
            last_date = current_date
            log_message(f"New day: {current_date}. Poll counter reset.")

        # --- Saturday 8 PM IST Weekly Push ---
        # Note: Running on local machine, so use local time (IST = UTC+5:30)
        # If your system is in IST, hour 20 = 8 PM
        is_saturday = now.weekday() == 5
        is_eight_pm = now.hour == 20 and now.minute < 15
        
        if is_saturday and is_eight_pm and last_weekly_push != current_date:
            log_message("🔔 SATURDAY 8 PM - Triggering weekly portfolio update...")
            try:
                update_script = os.path.join(AGENT_DIR, "update_agent.py")
                python_exe = sys.executable
                log_message(f"Running: {python_exe} {update_script}")
                result = subprocess.run([python_exe, update_script], capture_output=True, text=True, timeout=300)
                log_message(f"Exit code: {result.returncode}")
                if result.stdout:
                    log_message(f"Output: {result.stdout[-500:]}")
                if result.stderr:
                    log_message(f"Error: {result.stderr[-500:]}")
                if result.returncode == 0:
                    clear_daily_logs()
                    log_message("✅ Weekly update successful - logs cleared")
                else:
                    log_message("⚠️ Weekly update had issues - logs preserved")
                last_weekly_push = current_date
            except subprocess.TimeoutExpired:
                log_message("❌ Weekly update timed out")
            except Exception as e:
                log_message(f"❌ Weekly update error: {e}")

        # --- Hourly Active Window ---
        # At the start of each hour (minute 0), begin 15-minute active window
        if current_minute == 0 and current_hour != last_hour:
            last_hour = current_hour
            log_message(f"Hour {current_hour}:00 - Starting {ACTIVE_WINDOW_MINUTES}-minute active window")

        # Check if we're in the active window (first 15 minutes of the hour)
        in_active_window = current_minute < ACTIVE_WINDOW_MINUTES
        
        # Also respect daily max hours (convert to approximate poll count)
        max_polls_per_day = (DAILY_MAX_HOURS * 60) // POLL_INTERVAL_MINUTES

        if in_active_window and daily_polls < max_polls_per_day:
            # Poll at intervals during active window
            if current_minute % POLL_INTERVAL_MINUTES == 0:
                run_all_polls()
                daily_polls += 1

        # Sleep until next minute
        time.sleep(60 - now.second)

if __name__ == "__main__":
    try:
        run_daemon()
    except KeyboardInterrupt:
        log_message("Daemon stopped by user (Ctrl+C)")
    except Exception as e:
        log_message(f"Fatal error: {e}")
        import traceback
        log_message(traceback.format_exc())