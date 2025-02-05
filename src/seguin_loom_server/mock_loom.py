from __future__ import annotations

__all__ = ["MockLoom"]

from base_loom_server.base_mock_loom import BaseMockLoom


class MockLoom(BaseMockLoom):
    """Simulate a Seguin dobby loom.

    Parameters
    ----------
    verbose : bool
        If True, log diagnostic information.

    Notes
    -----
    Standard loom commands and replies are of the form "=<cmdchar><data>":

    * cmdchar is uppercase for a command and lowercase for a reply,
      and many commands have matching replies, such as
      "=U<unweave?>" and "=C<shaft_word>".

    * The loom reports status with ``=s<status_word>``,
      where status_word is a hex string whose bits are:

        * 0: shed fully closed.
        * 1: not used
        * 2: next pick (=C command) requested
        * 3: error (as of 2025-01 this is not implemented
             by Séguin, but is reserved for future use)

    * The loom reports nothing during a 2-cycle pick.

    * The loom silently ignores "=C<shaft_word>" if not requesting a pick.

    Out of band commands begin with "#" (the default in base_loom_server).

    Warning: I have assumed that bit 0 of status "shed fully closed"
    is set to 1 when moving to the requested shed is done, 0 otherwise.
    If this is wrong, and not simply inverted, then this loom
    does not report shaft motion, and I should change the code.
    See toika_loom_server for an example of a loom that does not
    report motion state.
    """

    terminator = b"\r"

    def __init__(self, verbose: bool = True) -> None:
        super().__init__(verbose=verbose)
        self.error_flag = False

    async def handle_read_bytes(self, read_bytes: bytes) -> None:
        """Handle one command from the web server."""
        cmd = read_bytes.decode().rstrip()
        if self.verbose:
            self.log.info(f"MockLoom: process client command {cmd!r}")
        if not cmd:
            return
        if len(cmd) < 2:
            self.log.warning(
                f"MockLoom: invalid command {cmd!r}: must be at least 2 characters"
            )
            return
        if cmd[0] == "#":
            # Out of band command
            await self.oob_command(cmd[1:])
            return

        if cmd[0] != "=":
            self.log.warning(
                f"MockLoom: invalid command {cmd!r}: must begin with '=' or '#'"
            )
            return
        cmd_char = cmd[1]
        cmd_data = cmd[2:]
        match cmd_char:
            case "C":
                # Specify which shafts to raise as a hex value
                try:
                    shaft_word = int(cmd_data, base=16)
                except Exception:
                    self.log.warning(
                        f"MockLoom: invalid command {cmd!r}: data after =C not a hex value"
                    )
                    return
                if self.error_flag:
                    return
                await self.set_shaft_word(shaft_word)
            case "U":
                # Client commands unweave on/off
                # (as opposed to user pushing UNW button on the loom,
                # in which case the loom changes it and reports it
                # to the client).
                if self.error_flag:
                    return
                if cmd_data not in {"0", "1"}:
                    self.log.warning(
                        f"{self}: invalid command {cmd!r}: arg must be 0 or 1"
                    )
                    return
                await self.set_weave_forward(weave_forward=cmd_data == "0")
            case "V":
                if self.verbose:
                    self.log.info("MockLoom: get version")
                await self.write("=v001")
            case "Q":
                if self.verbose:
                    self.log.info("MockLoom: get state")
                await self.report_motion_state()
            case "#":
                # Out of band command to the mock loom.
                await self.oob_command(cmd_data)
            case _:
                self.log.warning(f"MockLoom: unrecognized command: {cmd!r}")

    async def oob_command_e(self, cmd: str):
        """Toggle error flag"""
        self.error_flag = not self.error_flag
        await self.report_motion_state()
        if self.verbose:
            self.log.info(f"{self}: oob toggle error_flag to: {self.error_flag}")

    async def report_direction(self) -> None:
        await self.write(f"=u{int(not self.weave_forward)}")

    async def report_motion_state(self) -> None:
        # Assume that shed_fully_closed = not moving
        # If there is no correlation between loom =s state and whether
        # shafts are moving, then this class cannot report motion state
        # and needs some work.
        bitmask = 0
        if not self.moving:
            bitmask += 1  # called "Shed fully closed" in Seguin docs
        if self.pick_wanted:
            bitmask += 4
        if self.error_flag:
            bitmask += 8
        await self.write(f"=s{bitmask:01x}")

    async def report_pick_wanted(self) -> None:
        if self.pick_wanted:
            await self.report_motion_state()

    async def report_shafts(self) -> None:
        await self.write(f"=c{self.shaft_word:08x}")
