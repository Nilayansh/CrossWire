from __future__ import annotations

import os
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_without_exceptions(monkeypatch):
    """Smoke test ensuring the entire Streamlit dashboard renders cleanly without exceptions."""
    monkeypatch.setenv("USE_MOCK_API", "1")
    script_path = (Path(__file__).resolve().parent.parent.parent / "ui" / "streamlit_app.py").resolve()
    at = AppTest.from_file(str(script_path), default_timeout=25)
    at.run()

    # Verify no uncaught exceptions occurred during rendering
    assert not at.exception, f"App execution raised exceptions: {at.exception}"

    # Verify sidebar and main tabs rendered
    assert len(at.tabs) >= 4
    # Verify title text or main header appears
    markdown_texts = [m.value for m in at.markdown]
    has_nammantwin = any("NammaTwin v2" in text for text in markdown_texts)
    assert has_nammantwin, "Expected NammaTwin title in markdown elements"
