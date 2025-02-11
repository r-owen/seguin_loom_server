from __future__ import annotations

__all__ = ["LoomServer"]

import pathlib

from base_loom_server.base_loom_server import BaseLoomServer
from base_loom_server.client_replies import MessageSeverityEnum, ShaftStateEnum

from .mock_loom import MockLoom


class LoomServer(BaseLoomServer):
    """Communicate with the client software and the loom.

    Parameters
    ----------
    serial_port : str
        The name of the serial port, e.g. "/dev/tty0".
        If the name is "mock" then use a mock loom.
    translation_dict : dict[str, str]
        Translation dict.
    reset_db : bool
        If True, delete the old database and create a new one.
        A rescue aid, in case the database gets corrupted.
    verbose : bool
        If True, log diagnostic information.
    name : str
        User-assigned loom name.
    db_path : pathlib.Path
        Path to pattern database.
        Intended for unit tests, to avoid stomping on the real database.
    """

    def __init__(
        self,
        serial_port: str,
        translation_dict: dict[str, str],
        reset_db: bool,
        verbose: bool,
        name: str = "séguin",
        db_path: pathlib.Path | None = None,
    ) -> None:
        super().__init__(
            mock_loom_type=MockLoom,
            serial_port=serial_port,
            translation_dict=translation_dict,
            reset_db=reset_db,
            verbose=verbose,
            name=name,
            db_path=db_path,
        )

    async def write_shafts_to_loom(self, shaft_word: int) -> None:
        """Send a shaft_word to the loom"""
        await self.write_to_loom(f"=C{shaft_word:08x}")

    async def handle_loom_reply(self, reply_bytes: bytes) -> None:
        """Read and process replies from the loom."""
        reply = reply_bytes.decode().strip()
        if len(reply) < 2:
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
                    self.weave_forward = True
                elif reply_data == "1":
                    self.weave_forward = False
                else:
                    message = (
                        f"invalid loom reply {reply!r}: " "direction must be 0 or 1"
                    )
                    self.log.warning(f"LoomServer: {message}")
                    await self.report_command_problem(
                        message=message, severity=MessageSeverityEnum.WARNING
                    )
                    return
                await self.report_weave_direction()
            case "s":
                # Loom status (may include a request for the next pick)
                state_word = int(reply_data, base=16)

                # Set and report shaft state
                old_shaft_state = self.shaft_state  # type: ignore
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
