from __future__ import annotations

__all__ = ["LoomServer"]

from base_loom_server.base_loom_server import BaseLoomServer
from base_loom_server.enums import MessageSeverityEnum, ShaftStateEnum

from .mock_loom import MockLoom


class LoomServer(BaseLoomServer):
    """Communicate with the client software and the loom."""

    mock_loom_type = MockLoom
    default_name = "seguin"

    async def write_shafts_to_loom(self, shaft_word: int) -> None:
        """Send a shaft_word to the loom."""
        await self.write_to_loom(f"=C{shaft_word:08x}")

    async def handle_loom_reply(self, reply_bytes: bytes) -> None:
        """Read and process replies from the loom."""
        reply = reply_bytes.decode().strip()
        if len(reply) < 2:  # noqa: PLR2004
            message = f"invalid loom reply {reply!r}: less than 2 chars"
            self.log.warning(f"LoomServer: {message}")
            await self.report_command_problem(
                message=message,
                severity=MessageSeverityEnum.WARNING,
            )
            return
        if reply[0] != "=":
            message = f"invalid loom reply {reply!r}: no leading '='"
            self.log.warning(f"LoomServer: {message}")
            await self.report_command_problem(
                message=message,
                severity=MessageSeverityEnum.WARNING,
            )
            return
        reply_char = reply[1]
        reply_data = reply[2:]
        match reply_char:
            case "c":
                # Shafts that are up
                self.shaft_word = int(reply_data, base=16)
                await self.report_shaft_state()
            case "u":
                # Weave direction
                # The loom expects a new pick, as a result
                if reply_data == "0":
                    self.direction_forward = True
                elif reply_data == "1":
                    self.direction_forward = False
                else:
                    message = f"invalid loom reply {reply!r}: direction must be 0 or 1"
                    self.log.warning(f"LoomServer: {message}")
                    await self.report_command_problem(message=message, severity=MessageSeverityEnum.WARNING)
                    return
                await self.report_direction()
            case "s":
                # Loom status (may include a request for the next pick)
                state_word = int(reply_data, base=16)

                # Set and report shaft state
                # Note: type:ignore needed when running mypy from pre-commit.
                old_shaft_state = self.shaft_state  # type: ignore[has-type]
                if bool(state_word & 0x8):
                    self.shaft_state = ShaftStateEnum.ERROR
                elif bool(state_word & 0x1):
                    self.shaft_state = ShaftStateEnum.DONE
                else:
                    self.shaft_state = ShaftStateEnum.MOVING
                if self.shaft_state != old_shaft_state:
                    await self.report_shaft_state()

                # If next pick wanted, send it
                if bool(state_word & 0x4):
                    await self.handle_next_pick_request()
