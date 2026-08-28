from unittest.mock import patch

from project_website import create_app
from project_website.github import ProjectSnapshot


def _disable_network(app) -> None:
    app.extensions["github_projects"].get_projects = lambda: ProjectSnapshot(
        [], "unavailable", None
    )


def test_home_renders_portfolio_and_fallback(app, client) -> None:
    _disable_network(app)
    response = client.get("/")
    assert response.status_code == 200
    assert b"A fantasy world" in response.data
    assert b"Barbarian" in response.data
    assert b"Ancient Dragon" in response.data
    assert b"Activity temporarily unavailable" in response.data


def test_health_and_public_api(app, client) -> None:
    _disable_network(app)
    assert client.get("/healthz").get_json() == {"status": "ok"}
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert response.get_json() == {
        "cache": "unavailable",
        "fetched_at": None,
        "projects": [],
    }


def test_home_displays_latest_release(app, client) -> None:
    app.extensions["github_projects"].get_projects = lambda: ProjectSnapshot(
        [
            {
                "name": "project-simulation",
                "description": "Framework",
                "url": "https://example.test/repo",
                "default_branch": "main",
                "open_issues": 0,
                "latest_commit": {"message": "Ship v1"},
                "latest_release": {"tag": "v1.0.0", "url": "https://example.test/v1"},
            }
        ],
        "fresh",
        "2026-08-27",
    )
    response = client.get("/")
    assert b"Latest release" in response.data
    assert b"v1.0.0" in response.data


def test_security_headers(app, client) -> None:
    _disable_network(app)
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_invalid_contact_is_not_sent(app, client) -> None:
    _disable_network(app)
    with patch("project_website.routes.send_contact") as sender:
        response = client.post(
            "/contact",
            data={"name": "A", "email": "wrong", "subject": "Hi", "message": "short"},
        )
    assert response.status_code == 400
    sender.assert_not_called()
    assert b"Please correct" in response.data


def test_valid_contact_uses_prg_without_persistence(app, client, caplog) -> None:
    _disable_network(app)
    with patch("project_website.routes.send_contact") as sender:
        response = client.post(
            "/contact",
            data={
                "name": "Ada Example",
                "email": "ada@example.com",
                "subject": "Framework question",
                "message": "This message is long enough to validate.",
                "company": "",
            },
        )
    assert response.status_code == 303
    sender.assert_called_once()
    assert "ada@example.com" not in caplog.text
    assert "This message" not in caplog.text


def test_mail_failure_has_friendly_message_without_pii(app, client, caplog) -> None:
    _disable_network(app)
    with patch("project_website.routes.send_contact", side_effect=OSError("provider unavailable")):
        response = client.post(
            "/contact",
            data={
                "name": "Private Person",
                "email": "private@example.com",
                "subject": "Delivery test",
                "message": "Sensitive text that must not be logged.",
                "company": "",
            },
            follow_redirects=True,
        )
    assert b"Delivery is temporarily unavailable" in response.data
    assert "private@example.com" not in caplog.text
    assert "Sensitive text" not in caplog.text


def test_contact_requires_csrf() -> None:
    app = create_app({"TESTING": True, "SECRET_KEY": "csrf-test", "RATELIMIT_ENABLED": False})
    client = app.test_client()
    response = client.post(
        "/contact",
        data={
            "name": "Ada Example",
            "email": "ada@example.com",
            "subject": "Framework question",
            "message": "This request intentionally has no CSRF token.",
        },
    )
    assert response.status_code == 400


def test_contact_is_rate_limited() -> None:
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "rate-test",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": True,
            "RATELIMIT_STORAGE_URI": "memory://",
        }
    )
    app.extensions["github_projects"].get_projects = lambda: ProjectSnapshot(
        [], "unavailable", None
    )
    client = app.test_client()
    form = {
        "name": "Ada Example",
        "email": "ada@example.com",
        "subject": "Framework question",
        "message": "This message is long enough to validate.",
        "company": "",
    }
    with patch("project_website.routes.send_contact"):
        responses = [client.post("/contact", data=form) for _ in range(6)]
    assert [response.status_code for response in responses[:5]] == [303] * 5
    assert responses[5].status_code == 429
