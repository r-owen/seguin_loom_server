from __future__ import annotations

__all__ = ["MockLoom"]

import asyncio
import logging
from types import TracebackType
from typing import Type

from .loom_constants import LOG_NAME, TERMINATOR
from .mock_streams import (
    MockStreamReader,
    MockStreamWriter,
    StreamReaderType,
    StreamWriterType,
    open_mock_connection,
)

SHAFT_MOTION_DURATION: float = 1  # seconds for shafts to move
DIRECTION_NAMES = {True: "weave", False: "unweave"}


class MockLoom:
    """Simulate a Seguin dobby loom.

    Parameters
    ----------
    verbose : bool
        If True, log diagnostic information.

    The user controls this loom by:

    * Call command_reader.create_writer() to create a command writer.
    * Call reply_writer.create_reader() to create a reply reader.
    * Read replies from the reply reader.
    * Write commands to the command writer.
    """

    def __init__(self, verbose: bool = True) -> None:
        self.log = logging.getLogger(LOG_NAME)
        self.verbose = verbose
        self.weave_forward = True
        self.reply_writer: StreamWriterType | None = None
        self.command_reader: StreamReaderType | None = None
        self.done_task: asyncio.Future = asyncio.Future()
        self.error_flag = False
        self.shaft_word = 0
        self.shed_fully_closed = True
        self.pick_wanted = False
        self.report_shafts_done_task: asyncio.Future = asyncio.Future()
        self.start_task = asyncio.create_task(self.start())

    async def start(self) -> None:
        self.report_shafts_done_task.cancel()
        self.command_reader, self.reply_writer = open_mock_connection(
            terminator=TERMINATOR
        )
        self.read_commands_task = asyncio.create_task(self.handle_commands_loop())
        await self.report_state()
        await self.report_direction()
        await self.report_shafts()

    async def close(self) -> None:
        self.report_shafts_done_task.cancel()
        self.read_commands_task.cancel()
        if self.reply_writer is not None:
            self.reply_writer.close()
            await self.reply_writer.wait_closed()
        if not self.done_task.done():
            self.done_task.set_result(None)

    async def open_client_connection(self) -> tuple[StreamReaderType, StreamWriterType]:
        await self.start_task
        assert self.reply_writer is not None
        assert self.command_reader is not None
        # The isinstance tests make mypy happy, and might catch
        # a future bug if I figure out how to use virtual serial ports.
        if isinstance(self.reply_writer, MockStreamWriter) and isinstance(
            self.command_reader, MockStreamReader
        ):
            return (
                self.reply_writer.create_reader(),
                self.command_reader.create_writer(),
            )
        else:
            raise RuntimeError(
                f"Bug: {self.command_reader=} and {self.reply_writer=} must both be mock streams"
            )

    @classmethod
    async def amain(cls, verbose: bool = True) -> None:
        loom = cls(verbose=verbose)
        await loom.done_task

    def connected(self) -> bool:
        return (
            self.command_reader is not None
            and self.reply_writer is not None
            and not self.command_reader.at_eof()
            and not self.reply_writer.is_closing()
        )

    async def handle_commands_loop(self) -> None:
        self.report_shafts_done_task.cancel()
        while self.connected():
            assert self.command_reader is not None  # make mypy happy
            cmdbytes = await self.command_reader.readuntil(TERMINATOR)
            if not cmdbytes:
                # Connection has closed
                asyncio.create_task(self.close())
            cmd = cmdbytes.decode().rstrip()
            if self.verbose:
                self.log.info(f"MockLoom: process client command {cmd!r}")
            if not cmd:
                continue
            if cmd[0:1] != "=":
                self.log.warning(
                    f"MockLoom: invalid command {cmd!r}: must begin with '='"
                )
                continue
            if len(cmd) < 2:
                self.log.warning(
                    f"MockLoom: invalid command {cmd!r}: must be at least 2 characters"
                )
                continue
            cmd_char = cmd[1]
            cmd_data = cmd[2:]
            match cmd_char:
                case "C":
                    # Specify which shafts to raise as a hex value
                    try:
                        self.shaft_word = int(cmd_data, base=16)
                    except Exception:
                        self.log.warning(
                            f"MockLoom: invalid command {cmd!r}: data after =C not a hex value"
                        )
                        continue
                    if self.error_flag:
                        continue
                    if not self.pick_wanted:
                        # Ignore the command unless a pick is wanted
                        continue
                    self.shed_fully_closed = False
                    self.pick_wanted = False
                    self.report_shafts_done_task.cancel()
                    if self.verbose:
                        self.log.info(f"MockLoom: raise shafts {self.shaft_word:08x}")
                    await self.report_state()
                    self.report_shafts_done_task = asyncio.create_task(
                        self.report_shafts_done()
                    )
                case "U":
                    # Client commands unweave on/off
                    # (as opposed to the user pushing the button on the loom,
                    # in which case the loom changes it and reports it
                    # to the client).
                    if self.error_flag:
                        continue
                    if cmd_data == "0":
                        self.weave_forward = True
                        if self.verbose:
                            self.log.info(
                                "MockLoom: weave forward, commanded by software"
                            )
                    elif cmd_data == "1":
                        self.weave_forward = False
                        if self.verbose:
                            self.log.info(
                                "MockLoom: weave backwards, commanded by software"
                            )
                    else:
                        self.log.warning(
                            f"MockLoom: invalid command {cmd!r}: arg nmust be 0 or 1"
                        )
                        continue
                    await self.report_direction()
                case "V":
                    if self.verbose:
                        self.log.info("MockLoom: get version")
                    await self.reply("=v001")
                case "Q":
                    if self.verbose:
                        self.log.info("MockLoom: get state")
                    await self.report_state()
                case "#":
                    # Out of band command specific to the mock loom.
                    # Cast to lowercase becase uppercase is default on iOS.
                    if self.error_flag and cmd_data.lower() not in ("e", "c"):
                        continue
                    match cmd_data.lower():
                        case "c":
                            if self.verbose:
                                self.log.info("MockLoom: oob close command")
                            asyncio.create_task(self.close())
                            return
                        case "d":
                            self.weave_forward = not self.weave_forward
                            await self.report_direction()
                            if self.verbose:
                                self.log.info(
                                    "MockLoom: oob toggle weave direction: "
                                    f"{DIRECTION_NAMES[self.weave_forward]}"
                                )
                        case "e":
                            self.error_flag = not self.error_flag
                            if self.verbose:
                                self.log.info(
                                    f"MockLoom: oob toggle loom error flag to {self.error_flag}"
                                )
                            await self.report_state()
                        case "n":
                            if self.verbose:
                                self.log.info("MockLoom: oob request next pick")
                            self.pick_wanted = True
                            await self.report_state()
                        case _:
                            self.log.warning(
                                f"MockLoom: unrecognized oob command: {cmd_data!r}"
                            )

    async def reply(self, reply: str) -> None:
        """Issue the specified reply, which should not be terminated"""
        if self.verbose:
            self.log.info(f"MockLoom: send reply {reply!r}")
        if self.connected():
            assert self.reply_writer is not None
            self.reply_writer.write(reply.encode() + TERMINATOR)
            await self.reply_writer.drain()

    async def report_direction(self) -> None:
        await self.reply(f"=u{int(not self.weave_forward)}")

    async def report_shafts(self) -> None:
        await self.reply(f"=c{self.shaft_word:08x}")

    async def report_shafts_done(self) -> None:
        await asyncio.sleep(SHAFT_MOTION_DURATION)
        self.shed_fully_closed = True
        await self.report_state()
        await self.report_shafts()

    async def report_state(self) -> None:
        bitmask = 0
        if self.shed_fully_closed:
            bitmask += 1
        if self.pick_wanted:
            bitmask += 4
        if self.error_flag:
            bitmask += 8
        await self.reply(f"=s{bitmask:01x}")

    async def __aenter__(self) -> MockLoom:
        await self.start()
        return self

    async def __aexit__(
        self,
        type: Type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
