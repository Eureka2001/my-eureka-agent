from dataclasses import replace

import pytest

from config import Settings

USER_ID = "11111111-1111-4111-8111-111111111111"
TAG_ID = "22222222-2222-4222-8222-222222222222"
ITEM_ID = "33333333-3333-4333-8333-333333333333"
TEST_ENV = {
    "HABITICA_USER_ID": USER_ID,
    "HABITICA_API_TOKEN": "unit-test-credential",
}


@pytest.fixture
def settings():
    # Only the isolated mock transport uses zero delay. Real environment parsing
    # requires the official 30-second minimum.
    return replace(Settings.from_env(TEST_ENV), interval_seconds=0)
