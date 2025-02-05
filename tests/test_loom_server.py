from base_loom_server.testutils import BaseTestLoomServer

from seguin_loom_server.main import app
from seguin_loom_server.mock_loom import MockLoom

# Speed up tests
MockLoom.motion_duration = 0.1


class TestLoomServer(BaseTestLoomServer):
    app = app
