import io
import re
import zipfile
from typing import Optional

import requests

GITHUB_API = "https://api.github.com"

def parse_github_repo_url(repo_url: str) -> tuple[str, str]:
    match = re.match(
        r"^https?://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$",
        repo_url.strip(),
    )
    if not match:
        raise ValueError("Enter a valid URL such as https://github.com/owner/repository")
    return match.group(1), match.group(2)

def github_headers(token: Optional[str] = None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PipelineGuard-AI",
    }
    if token:
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers

def _error(response: requests.Response) -> str:
    if response.status_code == 401:
        return "Authentication failed. Check the GitHub token."
    if response.status_code == 403:
        return "GitHub denied the request. Check Actions read permission or API rate limits."
    if response.status_code == 404:
        return "Repository or workflow logs were not found. Private repositories require Actions read permission."
    try:
        message = response.json().get("message", response.text)
    except ValueError:
        message = response.text
    return f"GitHub API error {response.status_code}: {message}"

def get_workflow_runs(owner: str, repository: str, token: Optional[str]) -> list[dict]:
    response = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repository}/actions/runs",
        headers=github_headers(token),
        params={"per_page": 20},
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(_error(response))
    return response.json().get("workflow_runs", [])

def download_workflow_logs(owner: str, repository: str, run_id: int, token: Optional[str]) -> list[str]:
    response = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repository}/actions/runs/{run_id}/logs",
        headers=github_headers(token),
        timeout=45,
        allow_redirects=True,
    )
    if not response.ok:
        raise RuntimeError(_error(response))
    try:
        archive = zipfile.ZipFile(io.BytesIO(response.content))
    except zipfile.BadZipFile as exc:
        raise RuntimeError("GitHub did not return a valid log archive. Select a completed run.") from exc

    lines = []
    for filename in archive.namelist():
        if filename.lower().endswith((".txt", ".log")):
            content = archive.read(filename).decode("utf-8", errors="ignore")
            lines.extend(f"[{filename}] {line}" for line in content.splitlines())
    return lines
