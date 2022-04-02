from unittest import mock

import disnake
import pytest


@pytest.fixture
def inter():
    return mock.Mock(spec=disnake.MessageInteraction)
