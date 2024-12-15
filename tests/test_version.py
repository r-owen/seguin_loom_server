def test_version() -> None:
    try:
        import seguin_loom_server.version
    except ImportError:
        raise AssertionError("version file not found")

    assert seguin_loom_server.version.__all__ == ["__version__"]
    assert isinstance(seguin_loom_server.version.__version__, str)
