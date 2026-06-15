import json
import logging
import os
import re
import subprocess
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional dependency
    genai = None

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("CLOUD_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = "akshat2685"

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
PORTFOLIO_DATA_PATH = REPO_ROOT / "src" / "data" / "portfolioData.json"
ACTIVITY_INPUT_PATH = BASE_DIR / "activity_inputs.txt"
DAILY_LOGS_PATH = BASE_DIR / "daily_logs.json"

DEFAULT_PORTFOLIO = {
    "skills": [],
    "services": [],
    "projects": [],
    "certifications": [],
    "currentlyBuilding": [],
}

PROJECT_IMAGE_POOL = {
    "ai": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=900&q=80",
    "automation": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=900&q=80",
    "data": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=900&q=80",
    "3d": "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?w=900&q=80",
    "mobile": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=900&q=80",
    "default": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=900&q=80",
}

KEYWORD_SKILL_MAP = [
    ("AI & Automation", "OpenAI API", ["openai", "gpt", "chatgpt"]),
    ("AI & Automation", "Gemini API", ["gemini"]),
    ("AI & Automation", "AI Agents", ["agent", "agents"]),
    ("AI & Automation", "Workflow Automation", ["automation", "workflow", "orchestration"]),
    ("AI & Automation", "Prompt Engineering", ["prompt"]),
    ("AI & Automation", "OCR Solutions", ["ocr"]),
    ("3D & Creative", "Three.js / R3F", ["three.js", "r3f", "three js"]),
    ("3D & Creative", "GLTF/GLB Assets", ["gltf", "glb"]),
    ("Languages", "Python", ["python"]),
    ("Languages", "TypeScript", ["typescript"]),
    ("Languages", "JavaScript", ["javascript", "node.js", "nodejs"]),
    ("Languages", "C++", ["c++", "cpp"]),
    ("Languages", "Kotlin", ["kotlin"]),
    ("Languages", "HTML/CSS", ["html", "css"]),
    ("Languages", "SQL", ["sql", "postgres", "database"]),
    ("Tools", "GitHub Actions", ["github actions", "actions workflow"]),
    ("Tools", "Vercel", ["vercel"]),
    ("Tools", "Docker", ["docker"]),
    ("Tools", "Playwright", ["playwright"]),
    ("Tools", "Vite", ["vite"]),
]


def load_json_file(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return deepcopy(default)
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse %s: %s", path, exc)
        return deepcopy(default)


def save_json_file(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_text(value).lower())


def unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        text = normalize_text(value)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(text)
    return ordered


def truncate(text: str, limit: int) -> str:
    clean = normalize_text(text)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


def title_case_repo_name(name: str) -> str:
    cleaned = normalize_text(name).replace("_", " ").replace("-", " ")
    return " ".join(part.capitalize() if not part.isupper() else part for part in cleaned.split())


def load_current_data() -> Dict[str, Any]:
    data = load_json_file(PORTFOLIO_DATA_PATH, DEFAULT_PORTFOLIO)
    merged = deepcopy(DEFAULT_PORTFOLIO)
    if isinstance(data, dict):
        for key in merged:
            if key in data and isinstance(data[key], list):
                merged[key] = data[key]
    return merged


def read_daily_logs() -> List[Dict[str, Any]]:
    logs = load_json_file(DAILY_LOGS_PATH, [])
    return logs if isinstance(logs, list) else []


def read_local_activities() -> List[str]:
    if not ACTIVITY_INPUT_PATH.exists():
        ACTIVITY_INPUT_PATH.write_text(
            "# Write any manual activities (certifications, courses, LinkedIn updates) below.\n"
            "# One entry per line. Example: Completed AWS Cloud Practitioner Certification\n"
            "# Lines starting with '#' are ignored.\n",
            encoding="utf-8",
        )
        return []

    lines = ACTIVITY_INPUT_PATH.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def fetch_github_data() -> Dict[str, Any]:
    logger.info("Fetching GitHub activity...")
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    repos_url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?sort=updated&per_page=20"
    events_url = f"https://api.github.com/users/{GITHUB_USERNAME}/events/public?per_page=20"

    try:
        repos_response = requests.get(repos_url, headers=headers, timeout=15)
        repos_response.raise_for_status()
        repos = repos_response.json()

        events_response = requests.get(events_url, headers=headers, timeout=15)
        events_response.raise_for_status()
        events = events_response.json()
    except Exception as exc:
        logger.warning("Failed to fetch GitHub activity: %s", exc)
        return {}

    repo_data: List[Dict[str, Any]] = []
    total_stars = 0
    languages_used = set()

    for repo in repos:
        if repo.get("fork"):
            continue

        langs: List[str] = []
        lang_url = repo.get("languages_url")
        if lang_url:
            try:
                lang_res = requests.get(lang_url, headers=headers, timeout=10)
                if lang_res.ok:
                    langs = list(lang_res.json().keys())
            except Exception:
                pass

        repo_data.append(
            {
                "name": repo.get("name") or "",
                "description": normalize_text(repo.get("description")),
                "stars": int(repo.get("stargazers_count") or 0),
                "language": repo.get("language") or "",
                "languages": langs,
                "updated_at": repo.get("updated_at") or "",
                "url": repo.get("html_url") or "",
                "homepage": normalize_text(repo.get("homepage")),
            }
        )
        total_stars += int(repo.get("stargazers_count") or 0)
        if repo.get("language"):
            languages_used.add(repo["language"])
        for lang in langs:
            languages_used.add(lang)

    repo_data.sort(key=lambda item: item["updated_at"], reverse=True)

    activity_data = {
        "repositories": repo_data,
        "total_stars": total_stars,
        "languages_used": sorted(languages_used),
        "recent_events": [
            {
                "type": event.get("type", ""),
                "repo": event.get("repo", {}).get("name", "Unknown"),
                "created_at": event.get("created_at", ""),
            }
            for event in events[:10]
        ],
        "last_updated": datetime.now().isoformat(),
    }

    logger.info("Fetched %d repositories and %d stars", len(repo_data), total_stars)
    return activity_data


def keyword_matches(text: str, keywords: List[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def pick_project_image(text: str) -> str:
    lowered = text.lower()
    if keyword_matches(lowered, ["ocr", "invoice", "document", "pipeline"]):
        return PROJECT_IMAGE_POOL["data"]
    if keyword_matches(lowered, ["3d", "three.js", "glb", "gltf", "blender"]):
        return PROJECT_IMAGE_POOL["3d"]
    if keyword_matches(lowered, ["mobile", "android", "kotlin"]):
        return PROJECT_IMAGE_POOL["mobile"]
    if keyword_matches(lowered, ["agent", "automation", "workflow", "bot", "ai", "openai", "gemini"]):
        return PROJECT_IMAGE_POOL["automation"]
    return PROJECT_IMAGE_POOL["default"]


def is_meaningful_repo(repo: Dict[str, Any]) -> bool:
    text = f"{repo.get('name', '')} {repo.get('description', '')} {' '.join(repo.get('languages', []))}".lower()
    if not repo.get("name"):
        return False
    if repo.get("stars", 0) > 0 or normalize_text(repo.get("homepage")):
        return True
    return keyword_matches(
        text,
        [
            "ai",
            "agent",
            "automation",
            "ocr",
            "portfolio",
            "resume",
            "software",
            "engineer",
            "pipeline",
            "chat",
            "3d",
            "android",
            "kotlin",
            "docker",
            "playwright",
            "vercel",
            "github actions",
            "openai",
            "gemini",
        ],
    )


def repo_to_project(repo: Dict[str, Any]) -> Dict[str, Any]:
    text = f"{repo.get('name', '')} {repo.get('description', '')} {' '.join(repo.get('languages', []))}"
    repo_name = normalize_text(repo.get("name", "Project"))
    tech = unique_preserve_order(
        list(repo.get("languages", []))
        + [repo.get("language", "")] 
        + [tag for _, tag, keywords in KEYWORD_SKILL_MAP if keyword_matches(text, keywords)]
    )
    description = repo.get("description") or ""
    if not description:
        lowered_name = repo_name.lower()
        if "resume-automation" in lowered_name:
            description = "A live portfolio automation platform that summarizes technical activity and syncs updates to the website."
        elif "software_engineer" in lowered_name or "software engineer" in lowered_name:
            description = "A personal software engineering portfolio focused on projects, skills, and automation work."
        elif "lead-agent" in lowered_name:
            description = "An autonomous lead qualification and routing system built for intelligent outreach workflows."
        elif "sales_agent" in lowered_name:
            description = "An AI sales automation project designed for outreach, demos, and customer handling."
        else:
            description = f"A focused software project built around {', '.join(tech[:3]) or 'modern development'}."
    description = truncate(description, 180)
    return {
        "title": title_case_repo_name(repo_name),
        "tech": tech[:4],
        "desc": description,
        "link": repo.get("homepage") or repo.get("url") or "",
        "img": pick_project_image(text),
    }


def extract_skill_updates(github_data: Dict[str, Any], activity_texts: List[str]) -> List[Dict[str, Any]]:
    additions: Dict[str, List[str]] = {}

    for item in github_data.get("languages_used", []):
        text = normalize_text(item)
        for category, skill_item, keywords in KEYWORD_SKILL_MAP:
            if category == "Languages" and keyword_matches(text, keywords):
                additions.setdefault(category, []).append(skill_item)

    for text in activity_texts:
        for category, skill_item, keywords in KEYWORD_SKILL_MAP:
            if keyword_matches(text, keywords):
                additions.setdefault(category, []).append(skill_item)

    cleaned: List[Dict[str, Any]] = []
    for category, items in additions.items():
        category_items = unique_preserve_order(items)
        if category_items:
            cleaned.append({"category": category, "items": category_items})
    return cleaned


def extract_certifications(activity_texts: List[str]) -> List[str]:
    certs: List[str] = []
    for text in activity_texts:
        lowered = text.lower()
        if any(keyword in lowered for keyword in ["certification", "certificate", "course", "training", "workshop", "bootcamp", "simulation"]):
            certs.append(truncate(text, 120))
    return unique_preserve_order(certs)


def extract_currently_building(activity_texts: List[str], github_data: Dict[str, Any]) -> List[str]:
    items: List[str] = []
    for text in activity_texts:
        lowered = text.lower()
        if any(keyword in lowered for keyword in ["building", "working on", "developing", "creating", "launching", "shipping"]):
            items.append(truncate(text, 90))

    for repo in github_data.get("repositories", [])[:5]:
        repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
        if keyword_matches(repo_text, ["ai", "agent", "automation", "portfolio", "resume"]):
            items.append(f"{title_case_repo_name(repo.get('name', 'Project'))} improvements")

    return unique_preserve_order(items)


def build_deterministic_patch(
    current_data: Dict[str, Any],
    github_data: Dict[str, Any],
    manual_activities: List[str],
    daily_logs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    del current_data
    activity_texts = manual_activities + [entry.get("description", "") for entry in daily_logs]
    repo_projects = [repo_to_project(repo) for repo in github_data.get("repositories", []) if is_meaningful_repo(repo)]

    return {
        "skills": extract_skill_updates(github_data, activity_texts),
        "projects": repo_projects[:8],
        "certifications": extract_certifications(activity_texts),
        "currentlyBuilding": extract_currently_building(activity_texts, github_data),
    }


def build_ai_patch(
    current_data: Dict[str, Any],
    github_data: Dict[str, Any],
    manual_activities: List[str],
    daily_logs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not GEMINI_API_KEY or genai is None:
        return {}

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-3.5-flash")
    except Exception as exc:
        logger.warning("Gemini setup failed, using deterministic updates: %s", exc)
        return {}

    prompt = f"""
You maintain a portfolio website data file for Akshat Jain.
Return ONLY raw JSON with these keys:
- skills: array of {{category, items}}
- projects: array of {{title, tech, desc, link, img}}
- certifications: array of strings
- currentlyBuilding: array of strings

Rules:
1. Only suggest additions or clean refinements that fit the existing sections.
2. Keep descriptions concise and professional.
3. Do not change the overall schema.
4. Prefer projects that represent substantial AI, automation, or software work.
5. Do not repeat items already present in the current portfolio.

Current portfolio:
{json.dumps(current_data, indent=2)}

GitHub activity:
{json.dumps(github_data, indent=2)}

Manual activity notes:
{json.dumps(manual_activities, indent=2)}

Historical daily logs:
{json.dumps(daily_logs, indent=2)}
"""

    try:
        response = model.generate_content(prompt)
        response_text = normalize_text(response.text)
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        parsed = json.loads(response_text.strip())
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        logger.warning("Gemini patch generation failed, falling back to heuristics: %s", exc)
    return {}


def merge_lists(existing: List[Any], additions: List[Any], key_fn=None) -> List[Any]:
    result = deepcopy(existing)
    seen = set()
    if key_fn is None:
        key_fn = lambda item: normalize_text(item).lower()

    for item in result:
        seen.add(key_fn(item))

    for item in additions:
        token = key_fn(item)
        if token in seen:
            continue
        seen.add(token)
        result.append(item)
    return result


def merge_skill_sections(existing: List[Dict[str, Any]], additions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged = deepcopy(existing)
    index = {normalize_text(group.get("category")).lower(): group for group in merged if isinstance(group, dict)}

    for group in additions:
        if not isinstance(group, dict):
            continue
        category = normalize_text(group.get("category"))
        if not category:
            continue
        items = [normalize_text(item) for item in group.get("items", []) if normalize_text(item)]
        if not items:
            continue
        target = index.get(category.lower())
        if target is None:
            target = {"category": category, "items": []}
            merged.append(target)
            index[category.lower()] = target
        target["items"] = merge_lists(target.get("items", []), items)
    return merged


def merge_projects(existing: List[Dict[str, Any]], additions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged = deepcopy(existing)
    existing_keys = {
        normalize_key(project.get("link") or project.get("title"))
        for project in merged
        if isinstance(project, dict)
    }

    for project in additions:
        if not isinstance(project, dict):
            continue
        title = normalize_text(project.get("title"))
        link = normalize_text(project.get("link"))
        desc = normalize_text(project.get("desc"))
        tech = [normalize_text(item) for item in project.get("tech", []) if normalize_text(item)]
        img = normalize_text(project.get("img")) or PROJECT_IMAGE_POOL["default"]
        if not title or not link:
            continue
        key = normalize_key(link or title)
        if key in existing_keys:
            continue
        existing_keys.add(key)
        merged.append(
            {
                "title": title,
                "tech": unique_preserve_order(tech)[:4],
                "desc": truncate(desc or f"A project centered on {', '.join(tech[:3]) or 'software development'}.", 180),
                "link": link,
                "img": img,
            }
        )
    return merged


def merge_strings(existing: List[str], additions: List[str]) -> List[str]:
    return merge_lists(existing, [normalize_text(item) for item in additions if normalize_text(item)])


def merge_portfolio_data(current_data: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(current_data)
    result["skills"] = merge_skill_sections(result.get("skills", []), patch.get("skills", []))
    result["projects"] = merge_projects(result.get("projects", []), patch.get("projects", []))
    result["certifications"] = merge_strings(result.get("certifications", []), patch.get("certifications", []))
    result["currentlyBuilding"] = merge_strings(result.get("currentlyBuilding", []), patch.get("currentlyBuilding", []))
    for key in DEFAULT_PORTFOLIO:
        result.setdefault(key, deepcopy(DEFAULT_PORTFOLIO[key]))
    return result


def git_commit_and_push() -> bool:
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--quiet", "--", str(PORTFOLIO_DATA_PATH)],
            cwd=REPO_ROOT,
            check=False,
        )
        if diff_result.returncode == 0:
            logger.info("No portfolio data changes detected.")
            return False

        logger.info("Committing portfolio data update...")
        subprocess.run(["git", "add", str(PORTFOLIO_DATA_PATH)], cwd=REPO_ROOT, check=True)
        subprocess.run(
            ["git", "commit", "-m", "chore: auto-update portfolio data"],
            cwd=REPO_ROOT,
            check=True,
        )

        push_cmd = ["git", "push", "origin", "main"]
        if GITHUB_TOKEN:
            push_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/resume-automation.git"
            push_cmd = ["git", "push", push_url, "main"]
        subprocess.run(push_cmd, cwd=REPO_ROOT, check=True)
        logger.info("Portfolio data pushed successfully.")
        return True
    except Exception as exc:
        logger.error("Git commit/push failed: %s", exc)
        return False


def run_agent() -> None:
    current_data = load_current_data()
    github_data = fetch_github_data()
    manual_activities = read_local_activities()
    daily_logs = read_daily_logs()

    if not github_data and not manual_activities and not daily_logs:
        logger.info("No activity found. Portfolio remains unchanged.")
        return

    ai_patch = build_ai_patch(current_data, github_data, manual_activities, daily_logs)
    fallback_patch = build_deterministic_patch(current_data, github_data, manual_activities, daily_logs)

    patch = deepcopy(fallback_patch)
    if ai_patch:
        patch["skills"] = merge_skill_sections(patch.get("skills", []), ai_patch.get("skills", []))
        patch["projects"] = merge_projects(patch.get("projects", []), ai_patch.get("projects", []))
        patch["certifications"] = merge_strings(patch.get("certifications", []), ai_patch.get("certifications", []))
        patch["currentlyBuilding"] = merge_strings(
            patch.get("currentlyBuilding", []),
            ai_patch.get("currentlyBuilding", []),
        )

    updated_data = merge_portfolio_data(current_data, patch)

    if updated_data != current_data:
        save_json_file(PORTFOLIO_DATA_PATH, updated_data)
        logger.info("Portfolio data updated successfully.")
        git_commit_and_push()
    else:
        logger.info("No schema-safe updates were produced.")


if __name__ == "__main__":
    run_agent()
