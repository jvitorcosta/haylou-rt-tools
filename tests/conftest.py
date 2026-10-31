from pathlib import Path

import pytest

FONT = Path(__file__).parent / "data" / "nunito-black-latin1.ttf"


@pytest.fixture
def font():
    return FONT
