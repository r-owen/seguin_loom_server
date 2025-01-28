import asyncio
import contextlib

from seguin_loom_server import mock_loom
from seguin_loom_server.loom_constants import TERMINATOR
from seguin_loom_server.mock_loom import MockLoom, StreamReaderType, StreamWriterType

# Speed up tests
mock_loom.SHAFT_MOTION_DURATION = 0.1


@contextlib.asynccontextmanager
async def create_loom():
    """Create a MockLoom and read (and check) the initial replies."""
    async with MockLoom(verbose=True) as loom:
        for expected_reply in (
            "=s1",
            "=u0",
            "=c00000000",
        ):
            reader, writer = await loom.open_client_connection()
            async with asyncio.timeout(1):
                reply = await read_reply(reader)
                assert expected_reply == reply
        assert not loom.reply_writer.is_closing()
        assert not loom.command_reader.at_eof()
        yield loom, reader, writer


async def read_reply(reader: StreamReaderType, timeout: float = 1) -> str:
    async with asyncio.timeout(timeout):
        reply_bytes = await reader.readuntil(TERMINATOR)
        assert reply_bytes[-1:] == TERMINATOR
        return reply_bytes[:-1].decode()


async def write_command(
    writer: StreamWriterType, command: str, timeout: float = 1
) -> None:
    writer.write(command.encode() + TERMINATOR)
    async with asyncio.timeout(timeout):
        await writer.drain()


async def test_get_status() -> None:
    async with create_loom() as (loom, reader, writer):
        await write_command(writer, "=Q")
        reply = await read_reply(reader)
        assert reply == "=s1"
        assert not loom.done_task.done()


async def test_set_direction() -> None:
    async with create_loom() as (loom, reader, writer):
        for direction in (0, 1, 0, 1):
            await write_command(writer, f"=U{direction:d}")
            reply = await read_reply(reader)
            assert reply == f"=u{direction:d}"
        assert not loom.done_task.done()


async def test_raise_shafts() -> None:
    async with create_loom() as (loom, reader, writer):
        for shaftword in (0x0, 0x1, 0x5, 0xFE, 0xFF19, 0xFFFFFFFE, 0xFFFFFFFF):
            # Tell mock loom to request the next pick
            await write_command(writer, "=#n")
            reply = await read_reply(reader)
            assert reply == "=s5"
            # Send the requested shaft information
            await write_command(writer, f"=C{shaftword:08x}")
            for expected_reply in ("=s0", "=s1", f"=c{shaftword:08x}"):
                reply = await read_reply(reader)
                assert reply == expected_reply
        assert not loom.done_task.done()


async def test_oob_change_direction() -> None:
    async with create_loom() as (loom, reader, writer):
        for expected_direction in (1, 0, 1, 0, 1):
            cmdchar = "d"
            if expected_direction == 0:
                cmdchar = cmdchar.upper()
            await write_command(writer, f"=#{cmdchar}")
            reply = await read_reply(reader)
            assert reply == f"=u{expected_direction:d}"
        assert not loom.done_task.done()


async def test_oob_next_pick() -> None:
    async with create_loom() as (loom, reader, writer):
        for i in range(4):
            cmdchar = "n"
            if i == 0:
                cmdchar = cmdchar.upper()
            await write_command(writer, f"=#{cmdchar}")
            reply = await read_reply(reader)
            assert reply == "=s5"
        assert not loom.done_task.done()


async def test_oob_toggle_error() -> None:
    async with create_loom() as (loom, reader, writer):
        for i in range(1, 5):
            expected_error = bool(i % 2)
            expected_status_word = 0x01 | (0x08 if expected_error else 0)
            cmdchar = "e"
            if i == 0:
                cmdchar = cmdchar.upper()
            await write_command(writer, f"=#{cmdchar}")
            await asyncio.sleep(0)
            assert loom.error_flag == expected_error
            reply = await read_reply(reader)
            assert reply == f"=s{expected_status_word:x}"
        assert not loom.done_task.done()


async def test_oob_close_connection() -> None:
    async with create_loom() as (loom, reader, writer):
        await write_command(writer, "=#c")
        async with asyncio.timeout(1):
            await loom.done_task
        assert loom.reply_writer.is_closing()
        assert loom.command_reader.at_eof()
