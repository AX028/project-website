import json
import urllib.error
from unittest.mock import patch

from project_website.github import GitHubProjectClient


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_github_data_is_sanitized_and_cached() -> None:
    calls = []

    def fake_open(request, timeout):
        calls.append(request.full_url)
        if request.full_url.endswith("/releases/latest"):
            return Response({"tag_name": "v1.0.0", "html_url": "https://example.test/release"})
        if "/commits?" in request.full_url:
            return Response(
                [
                    {
                        "commit": {
                            "message": "Ship v1\nbody",
                            "author": {"date": "2026-08-27"},
                        },
                        "html_url": "https://example.test/commit",
                    }
                ]
            )
        name = request.full_url.rsplit("/", 1)[-1]
        return Response(
            {
                "name": name,
                "description": "Public project",
                "html_url": "https://example.test/repo",
                "default_branch": "main",
                "open_issues_count": 2,
            }
        )

    client = GitHubProjectClient("secret", 600)
    with patch("urllib.request.urlopen", side_effect=fake_open):
        first = client.get_projects()
        second = client.get_projects()
    assert first.cache == second.cache == "fresh"
    assert len(first.projects) == 2
    assert first.projects[0]["latest_commit"]["message"] == "Ship v1"
    assert len(calls) == 6


def test_client_serves_stale_data_after_refresh_failure() -> None:
    client = GitHubProjectClient(ttl_seconds=30)
    client._projects = [{"name": "cached"}]
    client._fetched_at = 1
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
        snapshot = client.get_projects()
    assert snapshot.cache == "stale"
    assert snapshot.projects == [{"name": "cached"}]


def test_client_falls_back_to_latest_tag_when_no_release_exists() -> None:
    client = GitHubProjectClient(ttl_seconds=600)

    def fake_request(path):
        if path.endswith("/releases/latest"):
            raise urllib.error.HTTPError(path, 404, "missing", {}, None)
        if "/tags?" in path:
            return [{"name": "v1.0.0"}]
        if "/commits?" in path:
            return []
        return {"name": "project-simulation", "html_url": "https://example.test/repo"}

    with patch.object(client, "_request", side_effect=fake_request):
        project = client._fetch_repository("AX028/project-simulation")
    assert project["latest_release"]["tag"] == "v1.0.0"
    assert project["latest_release"]["url"].endswith("/releases/tag/v1.0.0")
