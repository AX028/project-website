"""Small GitHub API client with fresh, stale, and unavailable states."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class ProjectSnapshot:
    projects: list[dict[str, Any]]
    cache: str
    fetched_at: str | None


class GitHubProjectClient:
    repositories = ("AX028/project-simulation", "AX028/project-website")

    def __init__(self, token: str | None = None, ttl_seconds: int = 600) -> None:
        self.token = token
        self.ttl_seconds = max(30, ttl_seconds)
        self._projects: list[dict[str, Any]] = []
        self._fetched_at: float | None = None
        self._lock = threading.Lock()

    def get_projects(self) -> ProjectSnapshot:
        with self._lock:
            now = time.time()
            if self._fetched_at and now - self._fetched_at < self.ttl_seconds:
                return self._snapshot("fresh")
            try:
                projects = [self._fetch_repository(name) for name in self.repositories]
            except (OSError, ValueError, urllib.error.URLError):
                return self._snapshot("stale" if self._projects else "unavailable")
            self._projects = projects
            self._fetched_at = now
            return self._snapshot("fresh")

    def _snapshot(self, status: str) -> ProjectSnapshot:
        fetched = (
            datetime.fromtimestamp(self._fetched_at, UTC).isoformat()
            if self._fetched_at is not None
            else None
        )
        return ProjectSnapshot(list(self._projects), status, fetched)

    def _fetch_repository(self, full_name: str) -> dict[str, Any]:
        repository = self._request(f"/repos/{full_name}")
        commits = self._request(f"/repos/{full_name}/commits?per_page=1")
        try:
            release = self._request(f"/repos/{full_name}/releases/latest")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            release = None
        latest = commits[0] if commits else {}
        commit = latest.get("commit", {})
        return {
            "name": str(repository.get("name", full_name.split("/")[-1])),
            "description": str(repository.get("description") or "Project source and documentation"),
            "url": str(repository.get("html_url", f"https://github.com/{full_name}")),
            "default_branch": str(repository.get("default_branch", "main")),
            "open_issues": int(repository.get("open_issues_count", 0)),
            "latest_commit": {
                "message": str(commit.get("message", "No commit available")).splitlines()[0][:120],
                "timestamp": commit.get("author", {}).get("date"),
                "url": latest.get("html_url"),
            },
            "latest_release": (
                {"tag": release.get("tag_name"), "url": release.get("html_url")}
                if release
                else None
            ),
        }

    def _request(self, path: str) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "project-website/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
        with urllib.request.urlopen(request, timeout=4) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
