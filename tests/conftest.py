import pytest

from project_website import create_app


@pytest.fixture
def app():
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()
