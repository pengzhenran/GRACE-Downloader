"""Write the standalone 使用说明 HTML into a target help_docs folder.

Used by ``build_release.bat``: the packaged app regenerates this file on first
use, but shipping it means the installer's 开始菜单 shortcut works immediately
and the guide can be opened from the release folder without running the app.

The screenshots must already be present in the target folder (the build script
copies them from ``docs/screenshots``).  No GUI is created — this only renders
the HTML template that lives in the application module.

Usage:
    python make_help_html.py <target_help_docs_folder>
"""
from __future__ import annotations

import sys
from pathlib import Path

import grace_downloader_gui_release as g


def main(argv: list[str]) -> int:
    out_dir = Path(argv[1]) if len(argv) > 1 else Path(__file__).parent / "help_docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    shots = {stem: True for stem, _cn, _en in g.HELP_SHOTS}
    html = g.build_help_html(shots)
    out_path = out_dir / g.HELP_HTML_NAME
    out_path.write_text(html, encoding="utf-8")

    missing = [s for s in shots if not (out_dir / f"{s}.png").is_file()]
    print(f"[make_help_html] wrote {out_path} ({out_path.stat().st_size} bytes)")
    if missing:
        print("[make_help_html] WARNING missing screenshots: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
