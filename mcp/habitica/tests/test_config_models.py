import pytest
from conftest import TAG_ID, TEST_ENV, USER_ID
from pydantic import ValidationError

from config import DEFAULT_INTERVAL_SECONDS, Settings
from models import TaskCreate, TaskUpdate


def test_configuration_does_not_expose_credential():
    settings = Settings.from_env(TEST_ENV)
    assert settings.api_token not in repr(settings)
    assert settings.interval_seconds == DEFAULT_INTERVAL_SECONDS


@pytest.mark.parametrize("client_id", [None, "", "  "])
def test_client_id_defaults_from_user_id(client_id):
    env = dict(TEST_ENV)
    if client_id is not None:
        env["HABITICA_CLIENT_ID"] = client_id
    assert Settings.from_env(env).client_id == f"{USER_ID}-eureka-habitica"


def test_explicit_client_id_override_is_preserved():
    client_id = f"{TAG_ID}-custom-app"
    assert (
        Settings.from_env({**TEST_ENV, "HABITICA_CLIENT_ID": client_id}).client_id
        == client_id
    )


@pytest.mark.parametrize("missing", TEST_ENV)
def test_missing_configuration_names_the_missing_variable(missing):
    env = {key: value for key, value in TEST_ENV.items() if key != missing}
    with pytest.raises(ValueError, match=missing):
        Settings.from_env(env)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("HABITICA_USER_ID", "invalid"),
        ("HABITICA_API_TOKEN", "private\ninjected-header"),
        ("HABITICA_CLIENT_ID", "no-author-user-id"),
        ("HABITICA_API_URL", "http://example.com/api/v3"),
        ("HABITICA_API_URL", "https://user:password@example.com/api/v3"),
        ("HABITICA_API_URL", "https://habitica.com/api/v3?key=hidden"),
        ("HABITICA_API_URL", "https://habitica.com:bad/api/v3"),
        ("HABITICA_TIMEOUT_SECONDS", "nan"),
        ("HABITICA_TIMEOUT_SECONDS", "0"),
        ("HABITICA_REQUEST_INTERVAL_SECONDS", "inf"),
        ("HABITICA_REQUEST_INTERVAL_SECONDS", "29"),
    ],
)
def test_invalid_configuration_fails_without_echoing_values(name, value):
    with pytest.raises(ValueError) as exc:
        Settings.from_env({**TEST_ENV, name: value})
    assert value not in str(exc.value)


def test_loopback_api_supported_for_local_development():
    settings = Settings.from_env(
        {**TEST_ENV, "HABITICA_API_URL": "http://127.0.0.1:8181/api/v3/"}
    )
    assert settings.api_url == "http://127.0.0.1:8181/api/v3"


def test_task_serialization_preserves_false_empty_values_and_aliases():
    daily = TaskCreate.model_validate(
        {
            "type": "daily",
            "text": "练琴",
            "frequency": "weekly",
            "everyX": 2,
            "repeat": {"m": False, "f": True},
            "startDate": "2026-10-09",
            "priority": 1.5,
            "tags": [TAG_ID],
            "checklist": [{"text": "音阶"}],
        }
    )
    body = daily.api_body()
    assert body["everyX"] == 2
    assert body["repeat"] == {"m": False, "f": True}
    assert body["startDate"] == "2026-10-09"
    assert body["priority"] == 1.5
    assert body["tags"] == [TAG_ID]
    assert body["checklist"] == [{"text": "音阶", "completed": False}]
    patch = TaskUpdate.model_validate(
        {"notes": "", "tags": [], "collapseChecklist": False}
    )
    assert patch.api_body() == {"notes": "", "tags": [], "collapseChecklist": False}
    assert TaskUpdate.model_validate({"date": None}).api_body() == {"date": None}


@pytest.mark.parametrize(
    "body",
    [
        {"type": "other", "text": "task"},
        {"type": "todo", "text": "  "},
        {"type": "todo", "text": "task", "priority": 3},
        {"type": "todo", "text": "task", "date": "bad-date"},
        {"type": "todo", "text": "task", "tags": ["not-uuid"]},
        {"type": "habit", "text": "task", "checklist": []},
        {"type": "habit", "text": "task", "up": False, "down": False},
        {"type": "daily", "text": "task", "everyX": 10000},
        {"type": "todo", "text": "task", "frequency": "weekly"},
        {"type": "reward", "text": "task", "value": -1},
        {"type": "todo", "text": "task", "completed": True},
    ],
)
def test_task_rejects_invalid_or_api_controlled_fields(body):
    with pytest.raises(ValidationError):
        TaskCreate.model_validate(body)


@pytest.mark.parametrize(
    "body", [{}, {"notes": None}, {"type": "todo"}, {"completed": True}]
)
def test_update_requires_meaningful_patch(body):
    with pytest.raises(ValidationError):
        TaskUpdate.model_validate(body)
