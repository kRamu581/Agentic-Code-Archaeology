"""Keep test fixture writes in the workspace (including managed Windows sandboxes)."""
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path():
    # Default pytest mode-0700 temp roots can be inaccessible under Windows ACLs.
    # Use inherited workspace permissions; fixtures never touch the source .git.
    path = Path(__file__).parent / ".tmp" / uuid.uuid4().hex
    path.mkdir(parents=True)
    return path
