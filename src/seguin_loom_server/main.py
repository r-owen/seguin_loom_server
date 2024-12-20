import argparse
import pathlib
import pkgutil
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, Response

from .loom_server import DEFAULT_DATABASE_PATH, LoomServer

# Avoid warnings about no event loop in unit tests
# by constructing when the server starts
loom_server: LoomServer | None = None


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "serial_port",
        help="Serial port connected to the loom, "
        "typically of the form /dev/tty... "
        "Specify 'mock' to run a mock (simulated) loom",
    )
    parser.add_argument(
        "-r",
        "--reset-db",
        action="store_true",
        help="reset pattern database?",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print diagnostic information to stdout",
    )
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DATABASE_PATH,
        type=pathlib.Path,
        help="Path for pattern database. "
        "Settable so unit tests can avoid changing the real database.",
    )
    return parser


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, FastAPI]:
    global loom_server
    parser = create_argument_parser()
    args = parser.parse_args()

    async with LoomServer(**vars(args)) as loom_server:
        yield


app = FastAPI(lifespan=lifespan)


def get_file(filename: str) -> str:
    """Get the contents of text file from src/seguin_loom_driver"""
    bindata = pkgutil.get_data(package="seguin_loom_server", resource=filename)
    assert bindata is not None
    return bindata.decode()


@app.get("/")
async def get() -> HTMLResponse:
    display_html_template = get_file("display.html_template")

    display_css = get_file("display.css")

    display_js = get_file("display.js")

    assert loom_server is not None
    is_mock = loom_server.mock_loom is not None
    display_debug_controls = "block" if is_mock else "none"

    display_html = display_html_template.format(
        display_css=display_css,
        display_js=display_js,
        display_debug_controls=display_debug_controls,
    )

    return HTMLResponse(display_html)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    bindata = pkgutil.get_data(
        package="seguin_loom_server", resource="favicon-32x32.png"
    )
    assert bindata is not None
    return Response(content=bindata, media_type="image/x-icon")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    global loom_server
    assert loom_server is not None
    await loom_server.run_client(websocket=websocket)


def run_seguin_loom() -> None:
    # Handle the help argument and also catch parsing errors right away
    parser = create_argument_parser()
    parser.parse_args()

    uvicorn.run(
        "seguin_loom_server.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
    )
