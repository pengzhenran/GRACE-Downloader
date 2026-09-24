"""
GRACE & GRACE-FO Level-2  Spherical Harmonics  Downloader  —  GUI  v1.0  (RELEASE)
==================================================================================
Frozen release build.  This file is the distributable source of the published
v1.0 release: the interface is final, the user guide (使用说明) is already
generated under help_docs/, and the help dialog therefore carries only a Close
button — the in-app "refresh screenshots" / "open folder" / "save as HTML"
buttons of the development build are intentionally gone.

PyQt5 graphical interface for downloading GSM monthly gravity-field solutions
from NASA Earthdata (PODAAC), at degree 60 (BA01) or degree 96 (BB01).

Also downloads the latest GRACE Technical Notes (TN-13/14 — the C20/C30 SLR
and degree-1 geocenter correction files used by sh_to_grid.py).  Those are
public files on the PODAAC archive and need no Earthdata login.

Features
--------
* Author / affiliation / contact information in a menu entry and in a dedicated
  "关于 / About" dialog.
* WeChat official-account QR code (地球重力与人类生活 TVGG) available from the
  menu bar.
* "记住账号" and "记住密码" as two independent options, stored in a small local
  credentials file (see CREDENTIAL_FILENAME) so they survive a restart.
* "Register an Earthdata account" button that opens the official NASA sign-up
  page, together with an in-app registration guide (username / password rules
  are the live requirements of urs.earthdata.nasa.gov).
* "📂 打开文件夹" buttons that reveal the download / Technical-Notes directory
  in Explorer (Finder on macOS), with a clear message when it does not exist.
* "📘 使用说明": a screenshot-based HTML guide rendered in a scrollable popup
  (帮助 → 使用说明, or F1).  The screenshots ship with the release; if they are
  missing, the program regenerates them from its own interface on first open.
* Two configuration groups (account / download parameters) so no single form is
  crowded, and a window sized to fit comfortably on a 1080p screen.

Run
---
    python grace_downloader_gui_release.py          # from source

Packaged release
----------------
    pyinstaller --clean --noconfirm grace_downloader_release.spec
    -> dist/GRACE_Downloader_v1.0/GRACE_Downloader.exe

Requirements
------------
    pip install earthaccess PyQt5

Author : 彭桢燃 (Zhenran Peng)  <zhenran.peng@cug.edu.cn>
         China University of Geosciences (Wuhan) 中国地质大学（武汉）
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple

# ── earthaccess ────────────────────────────────────────────────────────────────
try:
    import earthaccess
except ImportError:
    sys.exit(
        "earthaccess is not installed.\n"
        "Please run:  pip install earthaccess\n"
        "Then re-run this script."
    )

# ── PyQt5 ──────────────────────────────────────────────────────────────────────
try:
    from PyQt5.QtCore import (
        QObject,
        QSettings,
        QThread,
        QSize,
        Qt,
        QTimer,
        QUrl,
        pyqtSignal,
    )
    from PyQt5.QtGui import (
        QDesktopServices,
        QFont,
        QIcon,
        QPixmap,
        QTextCursor,
    )
    from PyQt5.QtWidgets import (
        QAction,
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QTextBrowser,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    sys.exit(
        "PyQt5 is not installed.\n"
        "Please run:  pip install PyQt5\n"
        "Then re-run this script."
    )


# =============================================================================
#    Constants  (overridable from GUI)
# =============================================================================

DEFAULT_BASE_DIR = Path(
    r"D:\myds\1_Joe Science Data\1_1_GRACE\1_data\2_Level-2\2_unzipped\SH"
)

# ── Technical Notes (low-degree correction files) ─────────────────────────────
# Public documentation files on the PODAAC archive — no Earthdata login needed.
DEFAULT_TN_DIR = Path(
    r"D:\myds\1_Joe Science Data\1_1_GRACE\3_Technical Notes"
)

# ── Application identity / author information ─────────────────────────────────
APP_NAME = "GRACE & GRACE-FO Level-2 Downloader"
APP_VERSION = "1.0.1"

# Public repository: source code, releases and the issue tracker.
PROJECT_URL = "https://github.com/pengzhenran/GRACE-Downloader"
PROJECT_URL_LABEL = "GitHub · pengzhenran/GRACE-Downloader"

AUTHOR_NAME_CN = "彭桢燃"
AUTHOR_NAME_EN = "Zhenran Peng"
AUTHOR_EMAIL = "zhenran.peng@cug.edu.cn"
AUTHOR_PHONE = "15927402265"
AUTHOR_AFFILIATION_CN = "中国地质大学（武汉）"
AUTHOR_AFFILIATION_EN = "China University of Geosciences (Wuhan)"

WECHAT_ACCOUNT = "地球重力与人类生活"
WECHAT_ACCOUNT_EN = "TVGG"
WECHAT_QR_FILENAME = "地球重力与人类生活TVGG.jpg"
WECHAT_QR_CAPTION = f"课题组公众号：{WECHAT_ACCOUNT}  ({WECHAT_ACCOUNT_EN})"

# ── NASA Earthdata account registration ──────────────────────────────────────
EARTHDATA_REGISTER_URL = "https://urs.earthdata.nasa.gov/users/new"
EARTHDATA_HOME_URL = "https://urs.earthdata.nasa.gov/"
EARTHDATA_PROFILE_URL = "https://urs.earthdata.nasa.gov/profile"

# Username / password rules, quoted from the live registration page.
EARTHDATA_USERNAME_RULES = [
    "至少 4 个字符，最多 30 个字符",
    "只能使用小写字母、数字、英文句点 . 和下划线 _",
    "必须含有至少一个字母，不能有空格",
    "不能以 . 或 _ 开头 / 结尾，也不能出现连续两个 . 或 _",
]
EARTHDATA_PASSWORD_RULES = [
    "至少 12 个字符",
    "至少一个大写字母",
    "至少一个小写字母",
    "至少一个数字",
    "至少一个特殊字符（如 ! @ # $ % 等）",
]

# ── Help / documentation (screenshots + the standalone HTML guide) ───────────
# The in-app "使用说明" is generated from screenshots of this program's own
# widgets, and it is also written out as a self-contained HTML file here.
DOCS_DIRNAME = "help_docs"
HELP_HTML_NAME = "使用说明.html"

# (filename stem, Chinese caption, English caption) for every guide screenshot
HELP_SHOTS = [
    ("full_window", "整体界面", "The whole window"),
    ("account", "① 账号区：用户名、密码、记住账号 / 记住密码、注册账号",
     "1. Account: username, password, remember options, sign-up"),
    ("params", "② 下载参数区：目标目录、SH Degree、线程与重试",
     "2. Download settings: target folder, SH degree, threads / retries"),
    ("datasets", "③ 数据源选择：CSR / JPL / GFZ × GRACE / GRACE-FO",
     "3. Datasets: CSR / JPL / GFZ x GRACE / GRACE-FO"),
    ("progress", "④ 进度区：进度条、状态与汇总表",
     "4. Progress: bar, status and summary table"),
    ("log", "⑤ 日志区：下载过程与最终统计",
     "5. Log: download trace and final summary"),
    ("tn", "⑥ Technical Notes 区：低阶项改正数据",
     "6. Technical Notes: low-degree correction files"),
    ("actions", "⑦ 底部按钮：开始下载 / 取消 / 清空日志 / 保存日志 / 关于",
     "7. Action buttons: start / cancel / clear / save / about"),
]

# ── Declaration / credits  (shown on first run + in the docs) ────────────────
# Single source of truth: DECLARATION_HTML feeds the first-run dialog, the HTML
# user guide and (as plain text) the Word versions, so the wording cannot drift.
DECLARATION_TITLE = "声明与致谢  /  Declaration & Credits"

DECLARATION_HTML = """
<h3>一、开发技术</h3>
<table>
  <tr><th style="width:34%">组件</th><th>版本 / 说明</th></tr>
  <tr><td>语言</td><td>Python 3.13</td></tr>
  <tr><td><b>图形界面</b></td><td><b>PyQt5 5.15.11</b>（绑定 Qt 5.15.2，Qt 公司）<br>
      <b>本软件使用 PyQt5，不是 PySide6。</b></td></tr>
  <tr><td>sip 绑定</td><td>PyQt5-sip 12.19.0</td></tr>
  <tr><td>数据访问</td><td>earthaccess 0.19.0（含 fsspec、s3fs、requests、python-cmr）</td></tr>
  <tr><td>打包</td><td>PyInstaller 6.22.2；安装程序用 Inno Setup 6.7.3</td></tr>
  <tr><td>文档生成</td><td>python-docx 1.2.0、lxml 6.1.3（仅用于生成说明书 / 公众号文档）</td></tr>
</table>

<h3>二、数据来源</h3>
<p>GRACE 与 GRACE-FO Level-2 GSM 月重力场解算数据（CSR / JPL / GFZ，RL06 与
RL06.3）以及 GRACE Technical Notes（TN-13 / TN-14），均来自
<b>NASA PO.DAAC</b>（<a href="https://podaac.jpl.nasa.gov/">podaac.jpl.nasa.gov</a>）。
数据版权归 NASA 及其数据生产机构所有，使用请遵守 NASA Earthdata 数据使用条款；
本软件仅做下载与整理，不改动原始数据。</p>

<h3>三、许可与免责</h3>
<p>本软件为作者个人开发的科研辅助工具，<b>仅供科研与教学免费使用</b>。
由于使用了 PyQt5（GPL v3），本程序整体按 <b>GPL v3</b> 分发：
您可以自由使用与再分发，但需保留本声明，再分发时须一并提供源代码。</p>
<p>软件按“现状”提供，作者不对使用结果作任何明示或暗示担保；因使用本软件造成的
数据错误、下载失败或其它损失，作者不承担责任。请在使用前自行核对数据版本与完整性。</p>

<h3>四、联系方式</h3>
<p>作者：{AUTHOR_NAME_CN}（{AUTHOR_NAME_EN}），{AUTHOR_AFFILIATION_CN}<br>
邮箱：{AUTHOR_EMAIL}　电话：{AUTHOR_PHONE}<br>
源码 / 发行版 / 问题反馈：<a href="{PROJECT_URL}">{PROJECT_URL_LABEL}</a><br>
课题组公众号：{WECHAT_QR_CAPTION}<br>
使用中如发现问题或有功能建议，欢迎联系反馈。</p>
""".replace("{AUTHOR_NAME_CN}", AUTHOR_NAME_CN) \
   .replace("{AUTHOR_NAME_EN}", AUTHOR_NAME_EN) \
   .replace("{AUTHOR_AFFILIATION_CN}", AUTHOR_AFFILIATION_CN) \
   .replace("{AUTHOR_EMAIL}", AUTHOR_EMAIL) \
   .replace("{AUTHOR_PHONE}", AUTHOR_PHONE) \
   .replace("{PROJECT_URL_LABEL}", PROJECT_URL_LABEL) \
   .replace("{PROJECT_URL}", PROJECT_URL) \
   .replace("{WECHAT_QR_CAPTION}", WECHAT_QR_CAPTION)


def declaration_text(prefix: str = "") -> str:
    """Plain-text form of the declaration (for Word / console output).

    Loads the same HTML, so the wording is identical everywhere.
    """
    try:
        import lxml.html

        root = lxml.html.fromstring(f"<div>{DECLARATION_HTML}</div>")
        lines = []
        for node in root.iter():
            tag = node.tag if isinstance(node.tag, str) else ""
            if tag in ("h3", "h4"):
                lines.append("")
                lines.append(prefix + node.text_content().strip())
            elif tag in ("p", "li"):
                lines.append(prefix + node.text_content().strip())
            elif tag == "tr":
                cells = [c.text_content().strip() for c in node]
                if cells:
                    lines.append(prefix + "  ".join(cells))
        return "\n".join(lines).strip()
    except Exception:
        return DECLARATION_HTML

# App icon (multi-size .ico next to this script; bundled by the spec)
ICON_PATH = Path(__file__).resolve().parent / "grace_icon.ico"
TN_BASE_URL = (
    "https://archive.podaac.earthdata.nasa.gov/"
    "podaac-ops-cumulus-docs/grace/open/docs/"
)
TN_FILES = [
    "TN-14_C30_C20_GSFC_SLR.txt",    # C20 + C30 SLR  (used by sh_to_grid.py)
    "TN-13_GEOC_CSR_RL0603.txt",     # degree-1 geocenter — all 3 centres
    "TN-13_GEOC_GFZ_RL0603.txt",
    "TN-13_GEOC_JPL_RL0603.txt",
]

CENTERS = ["CSR", "JPL", "GFZ"]
MISSIONS = ["GRACE", "GRACE-FO"]

# Spherical-harmonic truncation marker inside the GSM filename:
#   BA01 → degree 60,  BB01 → degree 96  (same PODAAC collections).
DEGREE_MARKERS = {60: "BA01", 96: "BB01"}
DEFAULT_DEGREE = 60
CMR_PAGE_SIZE = 2000

DATASETS: Dict[Tuple[str, str], dict] = {
    ("CSR", "GRACE"): {
        "short_name": "GRACE_GSM_L2_GRAV_CSR_RL06",
        "version": "RL06",
    },
    ("JPL", "GRACE"): {
        "short_name": "GRACE_GSM_L2_GRAV_JPL_RL06",
        "version": "RL06",
    },
    ("GFZ", "GRACE"): {
        "short_name": "GRACE_GSM_L2_GRAV_GFZ_RL06",
        "version": "RL06",
    },
    ("CSR", "GRACE-FO"): {
        "short_name": "GRACEFO_L2_CSR_MONTHLY_0063",
        "version": "RL06.3",
    },
    ("JPL", "GRACE-FO"): {
        "short_name": "GRACEFO_L2_JPL_MONTHLY_0063",
        "version": "RL06.3",
    },
    ("GFZ", "GRACE-FO"): {
        "short_name": "GRACEFO_L2_GFZ_MONTHLY_0063",
        "version": "RL06.3",
    },
}


# =============================================================================
#    Resource helpers  (work both from source and from a PyInstaller bundle)
# =============================================================================

def resource_base_dir() -> Path:
    """Directory that holds loose resource files (icon, QR image).

    Reads from the bundle when frozen (icon / QR image ship inside it).
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def data_root_dir() -> Path:
    """Writable directory for data this program creates at run time.

    Frozen builds must NOT write into the PyInstaller extraction folder (it may
    be read-only and is unknown to the user), so the help guide, the screenshots
    and the saved credentials live next to the .exe instead.  When run from
    source this is simply the folder containing this script.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def docs_dir() -> Path:
    """Folder that holds the help screenshots and the standalone HTML guide."""
    return data_root_dir() / DOCS_DIRNAME


def help_html_path() -> Path:
    """Path of the standalone HTML 使用说明."""
    return docs_dir() / HELP_HTML_NAME


def folder_url(path: Path) -> QUrl:
    """A QUrl that opens *path* in the system file manager."""
    return QUrl.fromLocalFile(str(Path(path).resolve()))


def open_folder(path: Path, parent: QWidget | None = None) -> bool:
    """Reveal *path* in the OS file manager (Explorer / Finder / xdg-open).

    Returns True when the request was handed to the desktop.  A missing folder
    is reported instead of silently doing nothing.
    """
    target = Path(str(path).strip().strip('"'))
    if not str(target):
        if parent is not None:
            QMessageBox.warning(parent, "打开文件夹", "路径为空。")
        return False
    if not target.exists():
        if parent is not None:
            QMessageBox.warning(
                parent, "打开文件夹",
                f"文件夹不存在：\n{target}\n\n"
                "请先在界面上选择正确的目录，或先创建该目录。",
            )
        return False
    return bool(QDesktopServices.openUrl(folder_url(target)))


def wechat_qr_path() -> Path | None:
    """Return the path of the WeChat QR image if it can be found locally."""
    base = resource_base_dir()
    candidates = [
        base / WECHAT_QR_FILENAME,
        Path(__file__).resolve().parent / WECHAT_QR_FILENAME,
        Path.cwd() / WECHAT_QR_FILENAME,
    ]
    for cand in candidates:
        try:
            if cand.is_file():
                return cand
        except OSError:
            continue
    return None


# =============================================================================
#    Credential storage helpers
# =============================================================================
# NOTE — plaintext-on-disk honesty:
#   "记住账号" / "记住密码" are two INDEPENDENT options.  Everything they store
#   goes into one small JSON file next to this script:
#
#       .grace_credentials.json
#
#   The account name is stored as-is; the password is base64-obfuscated so it is
#   not directly readable at a glance.  THIS IS NOT ENCRYPTION — anyone who can
#   read that file can recover the password.  The file is used instead of the
#   Windows registry because it is registry-independent (works on locked-down
#   lab PCs where HKCU writes are denied), visible, easy to inspect or delete,
#   and it travels with a portable copy of the program.  Do not reuse this
#   password elsewhere, and leave "记住密码" unchecked on a shared computer.

CREDENTIAL_FILENAME = ".grace_credentials.json"
_PW_PREFIX = "b64:"


def credentials_file_path() -> Path:
    """Path of the local credentials file."""
    return data_root_dir() / CREDENTIAL_FILENAME


def _encode_password(plain: str) -> str:
    return _PW_PREFIX + base64.b64encode(plain.encode("utf-8")).decode("ascii")


def _decode_password(stored: str) -> str:
    if not stored:
        return ""
    if stored.startswith(_PW_PREFIX):
        try:
            return base64.b64decode(
                stored[len(_PW_PREFIX):].encode("ascii")
            ).decode("utf-8")
        except Exception:
            return ""
    # Legacy / hand-edited plaintext value
    return stored


def load_credentials() -> Dict[str, str]:
    """Read the stored state; a missing/corrupt file yields {}.

    Recognised keys: ``remember_username``, ``remember_password`` (the two
    independent switches), plus ``username`` and ``password``.
    """
    path = credentials_file_path()
    try:
        if not path.is_file():
            return {}
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        return {str(k): str(v) for k, v in data.items()}
    except Exception:
        return {}


def save_credentials(
    remember_username: bool,
    username: str | None,
    remember_password: bool,
    password: str | None,
) -> None:
    """Persist the two independent remember options and their values.

    A value whose switch is off is dropped, and when both switches are off the
    file is deleted — unchecking really removes the stored secret from disk
    rather than only clearing the input box.
    """
    data: Dict[str, str] = {}
    if remember_username:
        data["remember_username"] = "true"
        if username:
            data["username"] = username
    if remember_password:
        data["remember_password"] = "true"
        if password:
            data["password"] = _encode_password(password)

    path = credentials_file_path()
    try:
        if not data:
            if path.is_file():
                path.unlink()
            return
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        # Never let a read-only folder break the download itself.
        pass


def open_url(url: str, parent: QWidget | None = None) -> bool:
    """Open *url* in the user's default browser."""
    ok = QDesktopServices.openUrl(QUrl(url))
    if not ok and parent is not None:
        QMessageBox.warning(
            parent, "无法打开浏览器",
            "未能自动打开浏览器，请手动复制下面的网址访问：\n\n" + url,
        )
    return bool(ok)


# =============================================================================
#    Help guide  —  screenshots of this program + rendered HTML
# =============================================================================
# The in-app guide is generated from the program's OWN widgets: the main
# window captures a screenshot of itself (whole window + each section), writes
# the PNGs next to the script under help_docs/, and renders an HTML page that
# embeds them.  Nothing is hand-drawn, so the pictures always match the real
# interface of this version.

_HELP_CSS = """
<style>
  body   { font-family: "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
           font-size: 13px; color: #222; margin: 12px 16px; }
  h1     { font-size: 20px; color: #14425e; margin: 0 0 4px 0; }
  h2     { font-size: 16px; color: #14425e; margin: 18px 0 6px 0;
           border-left: 4px solid #2e7d32; padding-left: 8px; }
  h3     { font-size: 14px; color: #333; margin: 12px 0 4px 0; }
  p, li  { line-height: 165%; }
  .meta  { color: #666; font-size: 12px; margin-bottom: 10px; }
  .shot  { margin: 8px 0 4px 0; }
  .cap   { color: #666; font-size: 12px; margin: 2px 0 14px 2px; }
  .miss  { color: #b00; font-size: 12px; border: 1px dashed #c99;
           background: #fdf6f6; padding: 6px 8px; }
  table  { border-collapse: collapse; margin: 6px 0 12px 0; }
  th, td { border: 1px solid #cfd8dc; padding: 5px 9px; font-size: 12px;
           vertical-align: top; }
  th     { background: #eef3f6; text-align: left; }
  code   { background: #f2f4f5; padding: 1px 4px; font-family: Consolas, monospace; }
  .tip   { background: #f1f8e9; border-left: 4px solid #7cb342;
           padding: 6px 10px; margin: 8px 0; }
  .warn  { background: #fff8e1; border-left: 4px solid #ffb300;
           padding: 6px 10px; margin: 8px 0; }
</style>
"""


def capture_widget_png(
    widget: QWidget,
    filename: str,
    max_height: int | None = None,
) -> Path | None:
    """Screenshot *widget* into help_docs/<filename>.

    *max_height* crops to the widget's preferred height, so a section that
    currently fills a tall window is not captured together with a large empty
    area.  Returns the written path, or None when the capture failed.
    """
    try:
        pixmap = widget.grab()
        if pixmap.isNull():
            return None
        if max_height is not None and pixmap.height() > max_height:
            pixmap = pixmap.copy(0, 0, pixmap.width(), max_height)
        out_dir = docs_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename
        if not pixmap.save(str(out_path), "PNG"):
            return None
        return out_path
    except Exception:
        return None


def build_help_html(shots: Dict[str, bool], width_px: int | None = None) -> str:
    """Render the full 使用说明 HTML document.

    *shots* maps a screenshot stem to whether its PNG was written, so the page
    states honestly when a picture is unavailable instead of showing a broken
    image.  *width_px* pins image widths in pixels: Qt's rich-text engine does
    not honour percentage widths, so an explicit width is what keeps the page
    free of horizontal scrolling.  Returns a complete document suitable for
    QTextBrowser.setHtml() (relative image paths resolve via setSearchPaths).
    """
    # Fixed sizes, used when the caller knows the viewport width.
    fixed: Dict[str, int] = {}
    if width_px and width_px > 120:
        usable = width_px - 28
        for stem, _, _ in HELP_SHOTS:
            if stem == "full_window":
                # The whole window is captured at window size: scale it to a
                # slightly smaller footprint so the section shots stay legible.
                fixed[stem] = min(int(usable * 0.72), usable)
            else:
                fixed[stem] = usable

    def shot(stem: str, width: str = "100%") -> str:
        if not shots.get(stem):
            return (
                '<div class="miss">（本机未能生成该截图，'
                f'可运行 make_help_shots.py 重新生成到 {DOCS_DIRNAME}/）</div>'
            )
        caption = next(
            (f"{cn} / {en}" for s, cn, en in HELP_SHOTS if s == stem), stem
        )
        width_attr = (
            f' width="{fixed[stem]}"' if stem in fixed else f' width="{width}"'
        )
        return (
            f'<div class="shot"><img src="{stem}.png"{width_attr}></div>'
            f'<div class="cap">{caption}</div>'
        )

    rows = "".join(
        f"<tr><td><code>{name}</code></td><td>{meaning}</td></tr>"
        for name, meaning in (
            ("<i>unzipped</i>/SH/CSR", "degree-60 的 CSR 月重力场解算文件（.gz）"),
            ("<i>unzipped</i>/SH/JPL", "degree-60 的 JPL 文件"),
            ("<i>unzipped</i>/SH/GFZ", "degree-60 的 GFZ 文件"),
            ("<i>unzipped</i>/SH/deg96/CSR",
             "选择 Degree 96 (BB01) 时改存到 <code>deg96/</code> 子目录，与 60 阶互不覆盖"),
        )
    )

    return f"""<html><head><meta charset="utf-8">{_HELP_CSS}</head><body>

<h1>GRACE &amp; GRACE-FO Level-2 下载器 · 使用说明</h1>
<div class="meta">
  版本 v{APP_VERSION} &nbsp;|&nbsp; 作者 {AUTHOR_NAME_CN}（{AUTHOR_NAME_EN}）
  &nbsp;|&nbsp; {AUTHOR_AFFILIATION_CN}<br>
  {AUTHOR_EMAIL} &nbsp;|&nbsp; {AUTHOR_PHONE} &nbsp;|&nbsp; {WECHAT_QR_CAPTION}<br>
  源码与更新：<a href="{PROJECT_URL}">{PROJECT_URL}</a>
</div>
<p>本说明中的插图是程序运行时对本软件界面的自动截图，与您当前看到的界面一致；图片文件位于程序目录下的 <code>{DOCS_DIRNAME}</code>，本页也可以直接用浏览器打开。</p>

<h2>一、整体界面</h2>
<p>窗口从上到下分为 7 个区域，底部按钮行固定不动，其余区域可滚动：</p>
{shot("full_window")}

<h2>二、配置账号（🔑 Account）</h2>
{shot("account")}
<table>
  <tr><th style="width:150px">控件</th><th>说明</th></tr>
  <tr><td>Username</td><td>NASA Earthdata 用户名（不是邮箱）</td></tr>
  <tr><td>Password</td><td>Earthdata 密码；点 <b>👁</b> 可临时显示密码内容</td></tr>
  <tr><td>记住账号</td><td>勾选后，下次打开软件自动填入用户名</td></tr>
  <tr><td>记住密码</td><td>勾选后，下次打开软件自动填入密码</td></tr>
  <tr><td>注册账号</td><td>用浏览器打开 NASA Earthdata 官方注册页面</td></tr>
  <tr><td>注册说明</td><td>弹出注册步骤与用户名 / 密码规则</td></tr>
</table>
<div class="tip"><b>两个记忆开关互相独立</b>：可以只记账号、只记密码或都记。
取消勾选会立刻删除磁盘上保存的内容。保存位置是本程序目录下的
<code>{CREDENTIAL_FILENAME}</code>，密码只做 Base64 混淆（<b>不是加密</b>），
公用电脑建议不要勾选“记住密码”。</div>
<div class="warn">还没有账号？点击 <b>🆕 注册账号</b>。用户名需 4–30 位小写字母、
数字、<code>.</code> 或 <code>_</code>；密码需 ≥12 位且含大小写字母、数字和特殊字符。
注册后要到邮箱点激活链接才能下载。</div>

<h2>三、设置下载参数（⚙️ Download Settings）</h2>
{shot("params")}
<table>
  <tr><th style="width:150px">控件</th><th>说明</th></tr>
  <tr><td>Target Directory</td><td>数据保存的根目录；<b>…</b> 选择目录，
      <b>📂 打开文件夹</b> 直接在资源管理器里打开该目录</td></tr>
  <tr><td>SH Degree</td><td>球谐截断阶数：Degree 60（BA01，默认）或
      Degree 96（BB01）。96 阶文件存到 <code>deg96/</code> 子目录</td></tr>
  <tr><td>Threads</td><td>并行下载线程数，网络好可适当调大（建议 4–8）</td></tr>
  <tr><td>Retries</td><td>单个数据集失败后的重试次数</td></tr>
</table>
<p>下载完成后的目录结构：</p>
<table><tr><th>路径</th><th>内容</th></tr>{rows}</table>

<h2>四、选择数据源（📡 Datasets to Download）</h2>
{shot("datasets")}
<p>按“中心 × 任务”勾选：<b>CSR / JPL / GFZ</b> 三家的 <b>GRACE</b>
（RL06）与 <b>GRACE-FO</b>（RL06.3）月重力场解算文件。
<b>Select All</b> 全选，<b>Deselect All</b> 全不选；至少勾选一个才能开始下载。</p>

<h2>五、技术说明文件（📋 Technical Notes）</h2>
{shot("tn")}
<p>下载 <code>sh_to_grid.py</code> 需要用到的低阶项改正数据：TN-14（C20 / C30
SLR 改正）与 TN-13（一阶项地心改正，CSR / JPL / GFZ 三家）。这些是公开文件，
<b>不需要 Earthdata 账号</b>，可独立于重力场数据单独下载或更新。
点 <b>📂 打开文件夹</b> 可直接查看已下载的 TN 文件。</p>

<h2>六、查看进度与日志</h2>
{shot("progress")}
{shot("log")}
<p><b>Progress</b> 区显示整体进度条、当前状态和每个数据集的汇总表
（Found / Deg60 / Have / New / Got 分别为搜到的文件数、匹配当前阶数的文件数、
本地已有、本次待下载、本次已下载）。
<b>Log</b> 区输出下载全过程；<b>🗘 清空日志</b> 清屏，<b>💾 保存日志</b>
导出为 txt（文件末尾会自动附上作者信息）。</p>

<h2>七、底部按钮</h2>
{shot("actions")}
<table>
  <tr><th style="width:150px">按钮</th><th>说明</th></tr>
  <tr><td>▶ Start Download</td><td>开始下载（会先校验账号、目录与数据源选择）</td></tr>
  <tr><td>■ Cancel</td><td>请求取消，当前步骤结束后停止</td></tr>
  <tr><td>🗘 Clear Log</td><td>清空日志</td></tr>
  <tr><td>💾 Save Log</td><td>把日志保存为文本文件</td></tr>
  <tr><td>ℹ️ About / 作者</td><td>查看作者、单位、联系方式与公众号</td></tr>
</table>

<h2>八、菜单栏</h2>
<table>
  <tr><th style="width:150px">菜单</th><th>功能</th></tr>
  <tr><td>文件 → 注册 Earthdata 账号</td><td>打开官方注册页面</td></tr>
  <tr><td>文件 → 打开我的 Earthdata 主页</td><td>打开 urs.earthdata.nasa.gov/profile</td></tr>
  <tr><td>运行 → 开始下载 / 取消下载</td><td>等同底部按钮</td></tr>
  <tr><td>运行 → 下载 Technical Notes</td><td>等同 TN 区按钮</td></tr>
  <tr><td>帮助 → 使用说明</td><td>打开本说明</td></tr>
  <tr><td>帮助 → 关于 / 作者信息</td><td>作者与联系方式</td></tr>
  <tr><td>帮助 → 课题组公众号二维码</td><td>{WECHAT_QR_CAPTION}</td></tr>
  <tr><td>帮助 → 如何注册账号</td><td>注册步骤与账号规则</td></tr>
</table>

<h2>九、常见问题</h2>
<h3>1. 提示认证失败（Authentication failed）</h3>
<p>确认用户名 / 密码正确、邮箱已验证激活；Earthdata 账号是<b>用户名</b>而非邮箱。
新注册用户首次登录有时需要在浏览器里完成一次授权。</p>
<h3>2. 找不到任何文件（No granules found）</h3>
<p>检查网络能否访问 CMR / PODAAC，或换一个数据源尝试；
某些月份只有部分中心发布了产品。</p>
<h3>3. 下载中断或数量为 0</h3>
<p>把 <b>Threads</b> 调小（如 2）后重新点击 Start：程序会跳过本地已存在的文件，
只补下缺失的部分，可以放心重复运行。</p>
<h3>4. 只想更新低阶项改正数据</h3>
<p>不需要账号，直接点 <b>⬇️ Download Latest Technical Notes</b> 即可。</p>

<p class="meta">—— 本页由程序自动生成（截图 + HTML），转载或引用请注明作者。</p>

<h2>十、声明与致谢</h2>
{DECLARATION_HTML}

</body></html>"""


def write_help_html(shots: Dict[str, bool]) -> Path:
    """Write the 使用说明 as a standalone HTML file under help_docs/."""
    out_dir = docs_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = help_html_path()
    out_path.write_text(build_help_html(shots), encoding="utf-8")
    return out_path


# =============================================================================
#    Core download logic  (same as CLI version, but configurable via params)
# =============================================================================

def granule_basenames(granule) -> List[str]:
    """Extract the base file-name(s) from a granule's download URLs."""
    try:
        links = granule.data_links()
    except Exception:
        links = []
    return [url.rstrip("/").split("/")[-1] for url in links if url.strip()]


def granule_has_marker(granule, marker: str) -> bool:
    """Return True if any data-link or ProducerGranuleId contains *marker*."""
    try:
        for url in granule.data_links():
            if marker in url:
                return True
    except Exception:
        pass
    try:
        pid = granule["umm"]["ProducerGranuleId"]
        if marker in pid:
            return True
    except (KeyError, TypeError):
        pass
    return False


def granule_is_downloaded(granule, target_dir: Path) -> bool:
    """Return True if ALL files of *granule* already exist in *target_dir*."""
    names = granule_basenames(granule)
    if not names:
        return False
    return all((target_dir / name).exists() for name in names)


def file_md5(filepath: Path) -> str:
    """Return the MD5 hex digest of a local file."""
    h = hashlib.md5()
    with open(filepath, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_directories(base_dir: Path):
    """Create one sub-directory per centre under *base_dir*."""
    print("\n📂  Checking directory structure …")
    for center in CENTERS:
        d = base_dir / center
        d.mkdir(parents=True, exist_ok=True)
        marker = "✓" if d.exists() else "✗"
        print(f"    {marker}  {d}")
    print()


def login_earthdata(username: str, password: str) -> earthaccess.Auth:
    """Authenticate with NASA Earthdata."""
    print("🔐  Authenticating with NASA Earthdata …")
    os.environ["EARTHDATA_USERNAME"] = username
    os.environ["EARTHDATA_PASSWORD"] = password
    auth = earthaccess.login(strategy="environment")
    if not auth.authenticated:
        raise RuntimeError("Authentication failed. Check your credentials.")
    print(f"    ✅  Authenticated as  {username}\n")
    return auth


def download_tn_file(
    url: str,
    dest: Path,
    timeout: int = 60,
    retries: int = 5,
    retry_delay: float = 2.0,
) -> None:
    """Download one Technical-Note text file (public; redirects followed).

    The PODAAC→CloudFront link intermittently drops TLS handshakes, so retry
    with exponential backoff.  Raises if the result is too small to be a real
    TN file, so a failed or truncated download never overwrites an existing
    good file on disk.
    """
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (GRACE-TN-updater; +PyQt5)"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            if len(data) < 500:
                raise RuntimeError(
                    f"Download too small ({len(data)} B) — not a TN file?"
                )
            dest.write_bytes(data)
            return
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(retry_delay * 2 ** (attempt - 1))
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("download failed")


def process_dataset(
    center: str,
    mission: str,
    ds_info: dict,
    base_dir: Path,
    degree: int = DEFAULT_DEGREE,
    max_workers: int = 4,
    max_retries: int = 3,
    retry_delay: int = 10,
    cancel_event: threading.Event | None = None,
) -> dict:
    """Download one dataset → *base_dir* / *center* /.

    Non-default degrees (e.g. 96) land in *base_dir* / deg96 / *center* /
    so degree-60 and degree-96 products stay cleanly separated.
    """
    short_name = ds_info["short_name"]
    version = ds_info.get("version", "")
    sub = "" if degree == DEFAULT_DEGREE else f"deg{degree}"
    target_dir = base_dir / sub / center
    target_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "short_name": short_name,
        "center": center,
        "mission": mission,
        "version": version,
        "degree": degree,
        "found": 0,
        "matched": 0,
        "already_have": 0,
        "to_download": 0,
        "downloaded": 0,
        "failed": 0,
    }

    print(f"{'─' * 62}")
    print(f"📡  [{center}]  {mission}  ({version})")
    print(f"    Short name : {short_name}")
    print(f"    Target     : {target_dir}")

    if cancel_event and cancel_event.is_set():
        stats["failed"] = -1
        return stats

    # ── 1. Search CMR ────────────────────────────────────────────────────
    print("    🔍  Searching CMR …", end=" ", flush=True)
    try:
        results = earthaccess.search_data(
            short_name=short_name,
            count=CMR_PAGE_SIZE,
        )
    except Exception as exc:
        print(f"\n    ⚠️   CMR search error: {exc}")
        stats["failed"] = -1
        return stats

    if not results:
        print("\n    ⚠️   No granules found (dataset may not exist on CMR).")
        return stats

    stats["found"] = len(results)
    print(f"{len(results)} granules")

    # ── 2. Filter to the requested truncation ────────────────────────────
    marker = DEGREE_MARKERS[degree]
    matched = [g for g in results if granule_has_marker(g, marker)]
    stats["matched"] = len(matched)
    print(f"    🎯  Degree-{degree} (\"{marker}\"):  {len(matched)}  granules")

    if not matched:
        print(f"    ⚠️   No degree-{degree} granules after filtering.")
        return stats

    # ── 3. Separate already-downloaded vs new ────────────────────────────
    new_granules = []
    for g in matched:
        if granule_is_downloaded(g, target_dir):
            stats["already_have"] += 1
        else:
            new_granules.append(g)

    stats["to_download"] = len(new_granules)
    print(f"    📁  Already on disk : {stats['already_have']}")
    print(f"    🆕  To download     : {stats['to_download']}")

    if not new_granules:
        print("    ✅  Up-to-date — nothing to download.")
        return stats

    # ── 4. Download ──────────────────────────────────────────────────────
    print(f"    ⬇️   Downloading {len(new_granules)} granule(s) …")

    downloaded_paths: list = []
    for attempt in range(1, max_retries + 1):
        if cancel_event and cancel_event.is_set():
            print("    ⚠️   Cancelled by user.")
            stats["failed"] = stats["to_download"]
            return stats

        try:
            downloaded_paths = earthaccess.download(
                new_granules,
                local_path=str(target_dir),
                threads=max_workers,
            )
        except Exception as exc:
            print(f"    ⚠️   Attempt {attempt}/{max_retries} failed: {exc}")
            if attempt < max_retries:
                print(f"         Retrying in {retry_delay} s …")
                time.sleep(retry_delay)
            else:
                print("    ❌  All retries exhausted.")
                stats["failed"] = stats["to_download"]
                return stats
        else:
            if not downloaded_paths:
                print(f"    ⚠️   Download returned 0 files (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    print(f"         Retrying in {retry_delay} s …")
                    time.sleep(retry_delay)
                    continue
                else:
                    print("    ❌  All retries exhausted (empty result).")
                    stats["failed"] = stats["to_download"]
                    return stats
            break

    stats["downloaded"] = len(downloaded_paths)
    print(f"    ✅  Downloaded {stats['downloaded']} file(s) → {target_dir}")
    return stats


# =============================================================================
#    Qt Stream Redirector  —  captures print() → pyqtSignal
# =============================================================================

class _StreamEmitter(QObject):
    """A write-only stream that emits each complete line as a Qt signal."""

    line_written = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._buffer = ""

    def write(self, text: str) -> int:
        if not text:
            return 0
        self._buffer += text
        if "\n" in self._buffer:
            lines = self._buffer.split("\n")
            self._buffer = lines.pop()  # trailing partial line
            for line in lines:
                self.line_written.emit(line)
        return len(text)

    def flush(self) -> None:
        if self._buffer:
            self.line_written.emit(self._buffer)
            self._buffer = ""


# =============================================================================
#    Download Worker  —  runs in a QThread
# =============================================================================

class DownloadWorker(QObject):
    """QObject that executes the download pipeline in a background thread."""

    # Signals emitted to the GUI thread
    log_line = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)       # current, total, status
    dataset_completed = pyqtSignal(int, dict)   # index, stats
    all_finished = pyqtSignal(list)             # list of all stats dicts
    error_fatal = pyqtSignal(str)

    def __init__(
        self,
        username: str,
        password: str,
        base_dir: Path,
        selected_datasets: List[Tuple[str, str]],
        degree: int = DEFAULT_DEGREE,
        max_workers: int = 4,
        max_retries: int = 3,
        retry_delay: int = 10,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._username = username
        self._password = password
        self._base_dir = base_dir
        self._selected = selected_datasets
        self._degree = degree
        self._max_workers = max_workers
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._cancel = threading.Event()

    def cancel(self) -> None:
        """Signal the worker to stop at the next checkpoint."""
        self._cancel.set()
        self.log_line.emit("⚠️  Cancel requested — finishing current step …")

    def run(self) -> None:
        """Main entry point executed in the worker thread."""
        # ── Redirect stdout to the Qt signal ─────────────────────────────
        stream = _StreamEmitter()
        stream.line_written.connect(self.log_line)
        old_stdout = sys.stdout
        sys.stdout = stream  # type: ignore[assignment]

        all_stats: list = []
        try:
            # 1. Scaffolding
            ensure_directories(self._base_dir)
            if self._cancel.is_set():
                self.all_finished.emit(all_stats)
                return

            # 2. Authenticate
            login_earthdata(self._username, self._password)
            if self._cancel.is_set():
                self.all_finished.emit(all_stats)
                return

            # 3. Process each selected dataset
            total = len(self._selected)
            for idx, (center, mission) in enumerate(self._selected):
                ds_info = DATASETS.get((center, mission))
                if ds_info is None:
                    self.log_line.emit(
                        f"⚠️   Unknown dataset: ({center}, {mission}) — skipping"
                    )
                    continue

                self.progress.emit(
                    idx, total,
                    f"Processing [{center}] {mission} …",
                )

                stats = process_dataset(
                    center=center,
                    mission=mission,
                    ds_info=ds_info,
                    base_dir=self._base_dir,
                    degree=self._degree,
                    max_workers=self._max_workers,
                    max_retries=self._max_retries,
                    retry_delay=self._retry_delay,
                    cancel_event=self._cancel,
                )
                all_stats.append(stats)
                self.dataset_completed.emit(idx, stats)

                if self._cancel.is_set():
                    break

            self.progress.emit(total, total, "Done.")
            self.all_finished.emit(all_stats)

        except Exception as exc:
            self.error_fatal.emit(f"{type(exc).__name__}: {exc}")
            self.all_finished.emit(all_stats)
        finally:
            # Restore stdout
            sys.stdout = old_stdout
            # Flush any remaining buffered lines
            stream.flush()


class TNNotesWorker(QObject):
    """Download the latest GRACE Technical-Note files in a background thread.

    Runs independently of the GSM download (public files, no login needed).
    """

    log_line = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)   # current, total, status
    all_finished = pyqtSignal(list)        # list of (filename, ok)
    error_fatal = pyqtSignal(str)

    def __init__(
        self,
        tn_dir: Path,
        files: List[str],
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._tn_dir = tn_dir
        self._files = files

    def run(self) -> None:
        # Redirect stdout to the Qt signal (same pattern as DownloadWorker)
        stream = _StreamEmitter()
        stream.line_written.connect(self.log_line)
        old_stdout = sys.stdout
        sys.stdout = stream  # type: ignore[assignment]

        results: List[Tuple[str, bool]] = []
        try:
            self._tn_dir.mkdir(parents=True, exist_ok=True)
            print("📋  Downloading latest GRACE Technical Notes …")
            print(f"    Target : {self._tn_dir}")
            print(f"    Source : {TN_BASE_URL}")

            total = len(self._files)
            for i, name in enumerate(self._files):
                self.progress.emit(i, total, f"Downloading {name} …")
                dest = self._tn_dir / name
                url = TN_BASE_URL + name
                try:
                    download_tn_file(url, dest)
                    kb = dest.stat().st_size / 1024
                    print(f"    ✅  {name}  ({kb:.1f} KB)")
                    results.append((name, True))
                except Exception as exc:
                    print(f"    ❌  {name}  —  {exc}")
                    results.append((name, False))

            self.progress.emit(total, total, "Done.")

        except Exception as exc:
            self.error_fatal.emit(f"{type(exc).__name__}: {exc}")
        finally:
            sys.stdout = old_stdout
            stream.flush()
            self.all_finished.emit(results)


# =============================================================================
#    Earthdata  —  registration guide dialog
# =============================================================================

class EarthdataRegisterDialog(QDialog):
    """Show the official sign-up link plus the current account rules."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("🆕  Register a NASA Earthdata account  —  注册账号")
        self.setMinimumSize(660, 560)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        title = QLabel("<h3>注册 NASA Earthdata 账号</h3>")
        root.addWidget(title)

        intro = QLabel(
            "下载 GRACE / GRACE-FO Level-2 数据需要 NASA Earthdata 账号（免费）。"
            "注册完成后请到邮箱点击激活链接，然后回到本软件用同一账号密码登录。"
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        # ── Link row ─────────────────────────────────────────────────────
        link_group = QGroupBox("① 打开注册页面")
        link_layout = QVBoxLayout(link_group)

        self._edit_url = QLineEdit(EARTHDATA_REGISTER_URL)
        self._edit_url.setReadOnly(True)
        link_layout.addWidget(self._edit_url)

        link_btns = QHBoxLayout()
        btn_open = QPushButton("🌐  Open registration page  (打开注册网址)")
        btn_open.setMinimumHeight(34)
        btn_open.clicked.connect(
            lambda: open_url(EARTHDATA_REGISTER_URL, self)
        )
        btn_copy = QPushButton("📋  Copy link")
        btn_copy.setMinimumHeight(34)
        btn_copy.clicked.connect(self._copy_link)
        link_btns.addWidget(btn_open, stretch=2)
        link_btns.addWidget(btn_copy, stretch=1)
        link_layout.addLayout(link_btns)
        root.addWidget(link_group)

        # ── Rules ────────────────────────────────────────────────────────
        rules_group = QGroupBox("② 账号规则  (以注册页面为准)")
        rules_layout = QVBoxLayout(rules_group)

        for heading, rules in (
            ("Username 用户名必须：", EARTHDATA_USERNAME_RULES),
            ("Password 密码必须：", EARTHDATA_PASSWORD_RULES),
        ):
            lbl = QLabel(f"<b>{heading}</b>")
            rules_layout.addWidget(lbl)
            for rule in rules:
                item = QLabel(f"&nbsp;&nbsp;• {rule}")
                item.setWordWrap(True)
                rules_layout.addWidget(item)
            rules_layout.addSpacing(6)

        root.addWidget(rules_group)

        # ── Steps ────────────────────────────────────────────────────────
        steps = QLabel(
            "<b>③ 注册流程</b><br>"
            "1. 点击上面的按钮，在浏览器中打开注册页面；<br>"
            "2. 填写 Username / Password / 姓名 / 邮箱 / 国家（选 China），"
            "并通过人机验证；<br>"
            "3. 到邮箱点击 Earthdata 发来的激活链接；<br>"
            "4. 回到本软件：填入 Username 与 Password，点击 “▶ Start Download”。"
        )
        steps.setWordWrap(True)
        root.addWidget(steps)

        root.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)

    def _copy_link(self) -> None:
        QApplication.clipboard().setText(EARTHDATA_REGISTER_URL)
        QMessageBox.information(self, "已复制", "注册网址已复制到剪贴板。")


# =============================================================================
#    Author  —  WeChat QR / About dialogs
# =============================================================================

class WeChatQRDialog(QDialog):
    """Show the group WeChat official-account QR code."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"📱  {WECHAT_QR_CAPTION}")
        self.setMinimumSize(460, 620)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        caption = QLabel(f"<h3>{WECHAT_QR_CAPTION}</h3>")
        caption.setAlignment(Qt.AlignCenter)
        root.addWidget(caption)

        hint = QLabel("微信扫一扫，关注课题组公众号。")
        hint.setAlignment(Qt.AlignCenter)
        root.addWidget(hint)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumSize(400, 460)

        qr_path = wechat_qr_path()
        if qr_path is None:
            image_label.setText(
                "❌  未找到二维码图片\n\n"
                f"请把  {WECHAT_QR_FILENAME}\n"
                "放到本程序所在目录后重新打开。"
            )
            image_label.setWordWrap(True)
        else:
            pixmap = QPixmap(str(qr_path))
            if pixmap.isNull():
                image_label.setText(f"❌  无法读取图片：\n{qr_path}")
                image_label.setWordWrap(True)
            else:
                scaled = pixmap.scaled(
                    QSize(400, 460),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                image_label.setPixmap(scaled)
                image_label.setToolTip(str(qr_path))

        root.addWidget(image_label, stretch=1)

        if qr_path is not None:
            path_label = QLabel(f"<small>{qr_path}</small>")
            path_label.setAlignment(Qt.AlignCenter)
            path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            root.addWidget(path_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)


class AboutDialog(QDialog):
    """Container for everything about the author and the program."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("ℹ️  关于 / About")
        self.setMinimumSize(600, 480)
        self.resize(640, 520)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(18, 16, 18, 16)

        # ── Program header ───────────────────────────────────────────────
        header = QLabel(
            f"<h2>{APP_NAME}</h2>"
            f"<p>版本 Version {APP_VERSION}  ·  "
            f"支持 Degree 60 (BA01) / Degree 96 (BB01)</p>"
        )
        header.setWordWrap(True)
        root.addWidget(header)

        # ── Author info ──────────────────────────────────────────────────
        author_group = QGroupBox("作者信息  /  Author")
        grid = QGridLayout(author_group)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)

        rows = [
            ("作者  Author", f"{AUTHOR_NAME_CN}  ({AUTHOR_NAME_EN})"),
            ("单位  Affiliation",
             f"{AUTHOR_AFFILIATION_CN}<br>{AUTHOR_AFFILIATION_EN}"),
            ("邮箱  E-mail", AUTHOR_EMAIL),
            ("公众号  WeChat", f"{WECHAT_ACCOUNT}  ({WECHAT_ACCOUNT_EN})"),
            ("源码仓库  Source",
             f'<a href="{PROJECT_URL}">{PROJECT_URL_LABEL}</a>'),
            ("软件  Version", f"v{APP_VERSION}"),
        ]
        for r, (key, value) in enumerate(rows):
            key_label = QLabel(f"<b>{key}</b>")
            key_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            val_label = QLabel(value)
            val_label.setWordWrap(True)
            val_label.setOpenExternalLinks(True)
            val_label.setTextInteractionFlags(
                Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse
            )
            grid.addWidget(key_label, r, 0)
            grid.addWidget(val_label, r, 1)
        grid.setColumnStretch(1, 1)

        author_btns = QHBoxLayout()
        btn_mail = QPushButton("✉️  发邮件  (E-mail)")
        btn_mail.setMinimumHeight(32)
        btn_mail.clicked.connect(lambda: open_url(f"mailto:{AUTHOR_EMAIL}", self))
        author_btns.addWidget(btn_mail)
        btn_repo = QPushButton("🌐  GitHub 仓库  (Source & Releases)")
        btn_repo.setMinimumHeight(32)
        btn_repo.clicked.connect(lambda: open_url(PROJECT_URL, self))
        author_btns.addWidget(btn_repo)
        author_btns.addStretch()

        grid.addLayout(author_btns, len(rows) + 1, 0, 1, 2)
        root.addWidget(author_group)

        # ── Data / acknowledgement ───────────────────────────────────────
        credit = QLabel(
            "<small>数据来源：NASA PODAAC（GRACE / GRACE-FO Level-2 GSM，"
            "CSR / JPL / GFZ RL06 &amp; RL06.3）与 GRACE Technical Notes。"
            "本软件仅供科研与教学使用。<br>"
            "账号记忆：“记住账号 / 记住密码”为两个独立开关，保存内容写入本程序目录下的 "
            f"{CREDENTIAL_FILENAME}（Base64 混淆，非加密），取消勾选即删除该文件中的对应内容。"
            "</small>"
        )
        credit.setWordWrap(True)
        root.addWidget(credit)

        root.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)


# =============================================================================
#    Declaration dialog  —  shown once on first run, also in 帮助
# =============================================================================

class DeclarationDialog(QDialog):
    """Development stack, data source, licence and disclaimer.

    Shown automatically the first time the program runs (and reachable later
    from the 帮助 menu), so the notice travels with the distributed .exe.
    """

    def __init__(self, parent: QWidget | None = None, first_run: bool = False):
        super().__init__(parent)
        self.setWindowTitle(
            "📄  " + ("首次运行声明  /  First-run notice"
                      if first_run else DECLARATION_TITLE)
        )
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)

        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        if avail is not None:
            self.resize(max(620, min(860, avail.width() - 80)),
                        max(480, min(760, avail.height() - 80)))
        else:
            self.resize(820, 700)
        self.setMinimumSize(560, 420)

        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 10, 12, 10)

        header = QLabel(
            f"<b>{APP_NAME} v{APP_VERSION}</b>　"
            f"{AUTHOR_NAME_CN}（{AUTHOR_NAME_EN}）· {AUTHOR_AFFILIATION_CN}"
        )
        header.setWordWrap(True)
        root.addWidget(header)

        view = QTextBrowser()
        view.setOpenExternalLinks(True)
        view.setFrameShape(QFrame.StyledPanel)
        view.setHtml(f"<html><head><meta charset='utf-8'>{_HELP_CSS}"
                     f"</head><body>{DECLARATION_HTML}</body></html>")
        root.addWidget(view, stretch=1)

        row = QHBoxLayout()
        self._check_hide = QCheckBox("下次不再显示  /  Don't show again")
        self._check_hide.setToolTip(
            "勾选后不再在启动时弹出；随时可在 帮助 → 声明与致谢 中查看。"
        )
        row.addWidget(self._check_hide)
        row.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.accept)
        row.addWidget(buttons)
        root.addLayout(row)

    def hide_requested(self) -> bool:
        return self._check_hide.isChecked()


# =============================================================================
#    Help dialog  —  HTML 使用说明 rendered in a popup
# =============================================================================

class HelpDialog(QDialog):
    """Render the 使用说明 HTML inside a scrollable popup window.

    The page is generated from screenshots of this program's own widgets, so it
    always describes the interface the user is actually looking at.

    RELEASE build: the interface is frozen and the screenshots ship with the
    program, so this dialog deliberately carries a single Close button — there
    is no "refresh screenshots" / "open folder" / "save as HTML" action row.
    If a screenshot is missing, the program regenerates the set silently the
    first time the guide is opened.
    """

    def __init__(self, parent: "GraceDownloaderGUI | None" = None):
        super().__init__(parent)
        self._parent_window = parent
        self._shots: Dict[str, bool] = {}
        self._shown = False

        self.setWindowTitle("📘  使用说明  /  User Guide")
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)

        # Fit the popup to the screen without ever overflowing it.
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        if avail is not None:
            width = max(720, min(1000, avail.width() - 60))
            height = max(520, min(900, avail.height() - 60))
        else:
            width, height = 980, 860
        self.resize(width, height)
        self.setMinimumSize(640, 480)

        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 10, 12, 10)

        # ── Viewer ───────────────────────────────────────────────────────
        self._view = QTextBrowser()
        self._view.setOpenExternalLinks(True)
        self._view.setFrameShape(QFrame.StyledPanel)
        root.addWidget(self._view, stretch=1)

        # ── Status line ──────────────────────────────────────────────────
        self._status = QLabel("")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        # ── Single Close button (release build) ──────────────────────────
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        row.addWidget(buttons)
        root.addLayout(row)

        # ── First render ─────────────────────────────────────────────────
        self.refresh(regenerate_screenshots=False)

    # ── Rendering ───────────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        """Re-render once at the real viewport width (keeps images fitting)."""
        super().showEvent(event)
        if not self._shown:
            self._shown = True
            QTimer.singleShot(0, lambda: self.refresh(
                regenerate_screenshots=False))

    def refresh(self, regenerate_screenshots: bool = False) -> None:
        """Re-capture (optionally) and re-render the guide."""
        if regenerate_screenshots and self._parent_window is not None:
            self._shots = self._parent_window.capture_help_screenshots()
        else:
            self._shots = {
                stem: (docs_dir() / f"{stem}.png").is_file()
                for stem, _, _ in HELP_SHOTS
            }

        try:
            self._view.setSearchPaths([str(docs_dir())])
        except Exception:
            pass
        # Pin image widths to the real viewport so nothing overflows sideways.
        width_px = max(320, self._view.viewport().width())
        if self._view.verticalScrollBar().isVisible():
            width_px -= self._view.verticalScrollBar().width()
        self._view.setHtml(build_help_html(self._shots, width_px=width_px))

        ok = sum(1 for good in self._shots.values() if good)
        total = len(self._shots)
        if ok == total:
            state = f"已包含 {ok}/{total} 张界面截图"
        elif ok:
            state = f"仅 {ok}/{total} 张截图可用（其余未能生成）"
        else:
            state = "本机尚未生成截图"
        self._status.setText(f"{state}    （在本窗口内滚动阅读）")


# =============================================================================
#    Main GUI Window
# =============================================================================

class GraceDownloaderGUI(QMainWindow):
    """Main window for the GRACE Level-2 downloader GUI."""

    _SETTINGS_ORG = "GRACE-Downloader"
    _SETTINGS_APP = "GUI"

    def __init__(self):
        super().__init__()

        self._worker: DownloadWorker | None = None
        self._thread: QThread | None = None
        self._all_stats: list = []

        # ── Window ───────────────────────────────────────────────────────
        self.setWindowTitle(
            f"🌍  GRACE & GRACE-FO  Level-2  Downloader  (Degree 60 / 96)"
            f"    —    v{APP_VERSION}"
        )
        if ICON_PATH.is_file():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        # Sized to fit a 1080p screen with room to spare.  The config/dataset
        # body lives in a scroll area and the log area absorbs extra height, so
        # a short screen scrolls instead of clipping anything.
        self.setMinimumSize(1020, 640)
        self.resize(1280, 860)

        # ── Central widget ───────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)
        outer_layout.setSpacing(8)
        outer_layout.setContentsMargins(12, 10, 12, 10)

        # ── Menu bar ─────────────────────────────────────────────────────
        self._build_menu_bar()

        # ── Scrollable body (all configuration + log sections) ───────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        body = QWidget()
        root_layout = QVBoxLayout(body)
        root_layout.setSpacing(10)
        root_layout.setContentsMargins(0, 0, 6, 0)

        # ── Build sections ───────────────────────────────────────────────
        self._build_account_section(root_layout)
        self._build_params_section(root_layout)
        self._build_tn_section(root_layout)
        self._build_dataset_section(root_layout)
        self._build_progress_section(root_layout)
        self._build_log_section(root_layout)

        scroll.setWidget(body)
        self._scroll = scroll
        outer_layout.addWidget(scroll, stretch=1)

        # ── Action row stays pinned below the scroll area ────────────────
        self._build_button_row(outer_layout)

        # ── Restore saved settings ───────────────────────────────────────
        self._restore_settings()

        # ── Make sure the help/documentation folder exists ────────────────
        try:
            docs_dir().mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # ── Status bar ───────────────────────────────────────────────────
        self.statusBar().showMessage(
            f"Ready.  Select datasets and click Start.    "
            f"v{APP_VERSION}  ·  {AUTHOR_NAME_CN}  ·  {AUTHOR_EMAIL}"
        )

    # =========================================================================
    #    First-run declaration
    # =========================================================================

    def maybe_show_first_run_notice(self) -> None:
        """Show the declaration/credit notice the first time the program runs.

        The choice is remembered in QSettings; a failed write (locked-down
        machine) simply means the notice appears again next time.
        """
        try:
            settings = QSettings(self._SETTINGS_ORG, self._SETTINGS_APP)
            if str(settings.value("declaration_seen", "false")) == "true":
                return
        except Exception:
            pass

        dlg = DeclarationDialog(self, first_run=True)
        dlg.exec_()

        if dlg.hide_requested():
            try:
                settings = QSettings(self._SETTINGS_ORG, self._SETTINGS_APP)
                settings.setValue("declaration_seen", "true")
                settings.sync()
            except Exception:
                pass

    # =========================================================================
    #    UI construction helpers
    # =========================================================================

    def _build_menu_bar(self) -> None:
        bar = self.menuBar()

        file_menu = bar.addMenu("文件(&F)")
        act_register = QAction("🆕 注册 Earthdata 账号 …", self)
        act_register.triggered.connect(self._show_register_dialog)
        file_menu.addAction(act_register)
        act_profile = QAction("👤 打开我的 Earthdata 主页", self)
        act_profile.triggered.connect(lambda: open_url(EARTHDATA_PROFILE_URL, self))
        file_menu.addAction(act_profile)
        file_menu.addSeparator()
        act_quit = QAction("退出(&Q)", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        run_menu = bar.addMenu("运行(&R)")
        act_start = QAction("▶ 开始下载", self)
        act_start.triggered.connect(self._on_start)
        run_menu.addAction(act_start)
        act_cancel = QAction("■ 取消下载", self)
        act_cancel.triggered.connect(self._on_cancel)
        run_menu.addAction(act_cancel)
        run_menu.addSeparator()
        act_tn = QAction("📋 下载 Technical Notes", self)
        act_tn.triggered.connect(self._on_download_tn)
        run_menu.addAction(act_tn)

        help_menu = bar.addMenu("帮助(&H)")
        act_guide = QAction("📘 使用说明  (界面截图版)", self)
        act_guide.setShortcut("F1")
        act_guide.triggered.connect(self._show_help_dialog)
        help_menu.addAction(act_guide)
        help_menu.addSeparator()
        act_about = QAction("ℹ️ 关于 / 作者信息", self)
        act_about.triggered.connect(self._show_about_dialog)
        help_menu.addAction(act_about)
        act_qr = QAction("📱 课题组公众号二维码", self)
        act_qr.triggered.connect(self._show_qr_dialog)
        help_menu.addAction(act_qr)
        help_menu.addSeparator()
        act_help_register = QAction("🆕 如何注册账号？", self)
        act_help_register.triggered.connect(self._show_register_dialog)
        help_menu.addAction(act_help_register)
        help_menu.addSeparator()
        act_declaration = QAction("📄 声明与致谢  /  Declaration", self)
        act_declaration.triggered.connect(self._show_declaration_dialog)
        help_menu.addAction(act_declaration)

    def _build_account_section(self, parent_layout: QVBoxLayout) -> None:
        """Earthdata account: credentials, the two "remember" options, sign-up."""
        group = QGroupBox("🔑  Account  /  账号")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setVerticalSpacing(8)
        form.setHorizontalSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # ── Username + "记住账号" ─────────────────────────────────────────
        user_row = QHBoxLayout()
        user_row.setSpacing(10)
        self._edit_username = QLineEdit()
        self._edit_username.setPlaceholderText("Earthdata 用户名")
        self._edit_username.setMinimumWidth(200)
        user_row.addWidget(self._edit_username, stretch=1)

        self._check_remember_user = QCheckBox("记住账号")
        self._check_remember_user.setToolTip(
            "勾选后，下次打开软件自动填入 Earthdata 用户名。"
        )
        self._check_remember_user.toggled.connect(self._on_remember_user_toggled)
        user_row.addWidget(self._check_remember_user)
        form.addRow("Username:", user_row)

        # ── Password + show/hide + "记住密码" ─────────────────────────────
        pw_row = QHBoxLayout()
        pw_row.setSpacing(10)
        self._edit_password = QLineEdit()
        self._edit_password.setEchoMode(QLineEdit.Password)
        self._edit_password.setPlaceholderText("Earthdata 密码")
        self._edit_password.setMinimumWidth(200)
        pw_row.addWidget(self._edit_password, stretch=1)

        self._btn_show_pw = QPushButton("👁")
        self._btn_show_pw.setFixedWidth(38)
        self._btn_show_pw.setMinimumHeight(26)
        self._btn_show_pw.setCheckable(True)
        self._btn_show_pw.setToolTip("显示 / 隐藏密码")
        self._btn_show_pw.toggled.connect(self._toggle_password_echo)
        pw_row.addWidget(self._btn_show_pw)

        self._check_remember_pw = QCheckBox("记住密码")
        self._check_remember_pw.setToolTip(
            "勾选后，下次打开软件自动填入密码。\n"
            f"密码保存在本程序目录下的 {CREDENTIAL_FILENAME}\n"
            "（Base64 混淆，并非加密），公用电脑请勿勾选。"
        )
        self._check_remember_pw.toggled.connect(self._on_remember_pw_toggled)
        pw_row.addWidget(self._check_remember_pw)
        form.addRow("Password:", pw_row)

        # ── Sign-up row + credential-state hint ──────────────────────────
        link_row = QHBoxLayout()
        link_row.setSpacing(10)

        self._btn_register = QPushButton("🆕  注册账号  (打开注册网址)")
        self._btn_register.setMinimumHeight(32)
        self._btn_register.setToolTip(
            f"在浏览器中打开 NASA Earthdata 注册页面：\n{EARTHDATA_REGISTER_URL}"
        )
        self._btn_register.clicked.connect(self._open_register_page)
        link_row.addWidget(self._btn_register)

        self._btn_register_help = QPushButton("❔  注册说明")
        self._btn_register_help.setMinimumHeight(32)
        self._btn_register_help.setToolTip("查看注册步骤与账号 / 密码规则")
        self._btn_register_help.clicked.connect(self._show_register_dialog)
        link_row.addWidget(self._btn_register_help)

        link_row.addStretch()

        self._label_cred_hint = QLabel("")
        link_row.addWidget(self._label_cred_hint)
        form.addRow("", link_row)

        self._group_account = group
        parent_layout.addWidget(group)

    def _build_params_section(self, parent_layout: QVBoxLayout) -> None:
        """Download parameters, in a second group so nothing is crowded."""
        group = QGroupBox("⚙️  Download Settings  /  下载参数")
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)
        form.setVerticalSpacing(8)
        form.setHorizontalSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # ── Target directory ─────────────────────────────────────────────
        dir_row = QHBoxLayout()
        self._edit_base_dir = QLineEdit()
        self._edit_base_dir.setText(str(DEFAULT_BASE_DIR))
        btn_browse = QPushButton("…")
        btn_browse.setFixedWidth(36)
        btn_browse.setToolTip("选择目标目录")
        btn_browse.clicked.connect(self._browse_base_dir)

        btn_open_dir = QPushButton("📂  打开文件夹")
        btn_open_dir.setMinimumHeight(28)
        btn_open_dir.setToolTip(
            "在资源管理器 / 访达中打开当前的目标目录\n"
            "（目录不存在时会提示，不会自动创建）"
        )
        btn_open_dir.clicked.connect(self._open_base_dir_folder)

        dir_row.addWidget(self._edit_base_dir, stretch=1)
        dir_row.addWidget(btn_browse)
        dir_row.addWidget(btn_open_dir)
        form.addRow("Target Directory:", dir_row)

        # ── Spherical-harmonic degree (marker in the GSM filename) ───────
        self._combo_degree = QComboBox()
        for deg in sorted(DEGREE_MARKERS):
            self._combo_degree.addItem(
                f"Degree {deg}  ({DEGREE_MARKERS[deg]})", deg
            )
        self._combo_degree.setToolTip(
            "Spherical-harmonic truncation: 60 (BA01) or 96 (BB01). "
            "Degree-96 files go to <target>/deg96/<centre>/."
        )
        form.addRow("SH Degree:", self._combo_degree)

        # ── Threads / retries (one row to save vertical space) ───────────
        spin_row = QHBoxLayout()
        spin_row.setSpacing(8)

        self._spin_threads = QSpinBox()
        self._spin_threads.setRange(1, 16)
        self._spin_threads.setValue(4)
        self._spin_threads.setMinimumWidth(70)
        self._spin_threads.setToolTip("Parallel download threads")
        spin_row.addWidget(QLabel("Threads:"))
        spin_row.addWidget(self._spin_threads)

        spin_row.addSpacing(20)

        self._spin_retries = QSpinBox()
        self._spin_retries.setRange(1, 10)
        self._spin_retries.setValue(3)
        self._spin_retries.setMinimumWidth(70)
        self._spin_retries.setToolTip("Max retries per dataset on failure")
        spin_row.addWidget(QLabel("Retries:"))
        spin_row.addWidget(self._spin_retries)

        spin_row.addStretch()
        form.addRow("Threads / Retries:", spin_row)

        self._group_params = group
        parent_layout.addWidget(group)

    def _build_tn_section(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("📋  Technical Notes  (低阶项改正数据)")
        v = QVBoxLayout(group)
        v.setSpacing(8)

        hint = QLabel(
            "Downloads the GRACE Technical Notes used by sh_to_grid.py — "
            "TN-14 (C20/C30 SLR) + TN-13 (degree-1 geocenter, all 3 centres). "
            "Public files, no Earthdata login required."
        )
        hint.setWordWrap(True)
        v.addWidget(hint)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(12)
        dir_row = QHBoxLayout()
        self._edit_tn_dir = QLineEdit()
        self._edit_tn_dir.setText(str(DEFAULT_TN_DIR))
        btn_browse = QPushButton("…")
        btn_browse.setFixedWidth(36)
        btn_browse.setToolTip("选择 Technical Notes 目录")
        btn_browse.clicked.connect(self._browse_tn_dir)

        btn_open_tn = QPushButton("📂  打开文件夹")
        btn_open_tn.setMinimumHeight(28)
        btn_open_tn.setToolTip(
            "在资源管理器 / 访达中打开 Technical Notes 目录\n"
            "（目录不存在时会提示，不会自动创建）"
        )
        btn_open_tn.clicked.connect(self._open_tn_dir_folder)

        dir_row.addWidget(self._edit_tn_dir, stretch=1)
        dir_row.addWidget(btn_browse)
        dir_row.addWidget(btn_open_tn)
        form.addRow("Target Directory:", dir_row)
        v.addLayout(form)

        btn_row = QHBoxLayout()
        self._btn_tn = QPushButton("⬇️  Download Latest Technical Notes")
        self._btn_tn.setMinimumHeight(32)
        self._btn_tn.clicked.connect(self._on_download_tn)
        self._label_tn_status = QLabel("")
        btn_row.addWidget(self._btn_tn)
        btn_row.addSpacing(12)
        btn_row.addWidget(self._label_tn_status)
        btn_row.addStretch()
        v.addLayout(btn_row)

        self._group_tn = group
        parent_layout.addWidget(group)

    def _build_dataset_section(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("📡  Datasets to Download  /  选择数据源")
        outer = QVBoxLayout(group)
        outer.setSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setHorizontalSpacing(28)

        # Header row
        grid.addWidget(QLabel("<b>Centre</b>"), 0, 0, Qt.AlignCenter)
        for j, mission in enumerate(MISSIONS):
            grid.addWidget(QLabel(f"<b>{mission}</b>"), 0, j + 1, Qt.AlignCenter)

        # Checkbox grid
        self._dataset_checkboxes: Dict[Tuple[str, str], QCheckBox] = {}
        for i, center in enumerate(CENTERS):
            grid.addWidget(QLabel(center), i + 1, 0, Qt.AlignCenter)
            for j, mission in enumerate(MISSIONS):
                cb = QCheckBox()
                cb.setChecked(True)
                grid.addWidget(cb, i + 1, j + 1, Qt.AlignCenter)
                self._dataset_checkboxes[(center, mission)] = cb

        grid.setColumnStretch(len(MISSIONS) + 1, 1)
        outer.addLayout(grid)

        # Select All / Deselect All
        btn_row = QHBoxLayout()
        btn_all = QPushButton("Select All")
        btn_all.setMinimumHeight(30)
        btn_all.clicked.connect(lambda: self._set_all_datasets(True))
        btn_none = QPushButton("Deselect All")
        btn_none.setMinimumHeight(30)
        btn_none.clicked.connect(lambda: self._set_all_datasets(False))
        btn_row.addStretch()
        btn_row.addWidget(btn_all)
        btn_row.addWidget(btn_none)
        btn_row.addStretch()
        outer.addLayout(btn_row)

        self._group_datasets = group
        parent_layout.addWidget(group)

    def _build_progress_section(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("📊  Progress")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Overall progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setValue(0)
        self._progress_bar.setMinimumHeight(24)
        layout.addWidget(self._progress_bar)

        # Status label
        self._label_status = QLabel("Idle")
        self._label_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._label_status)

        # Summary table
        self._summary_table = QTableWidget(0, 8)
        self._set_summary_header()
        self._summary_table.horizontalHeader().setStretchLastSection(True)
        self._summary_table.setMinimumHeight(130)
        # Keep the degree column header in sync with the selector
        self._combo_degree.currentIndexChanged.connect(self._set_summary_header)
        self._summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._summary_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._summary_table.verticalHeader().setDefaultSectionSize(26)
        layout.addWidget(self._summary_table)

        self._group_progress = group
        parent_layout.addWidget(group)

    def _build_log_section(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("📜  Log")
        layout = QVBoxLayout(group)

        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumBlockCount(5000)  # keep memory bounded
        self._log_view.setMinimumHeight(150)
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        self._log_view.setFont(font)
        layout.addWidget(self._log_view)

        self._group_log = group
        parent_layout.addWidget(group, stretch=4)

    def _build_button_row(self, parent_layout: QVBoxLayout) -> None:
        # Wrapped in a widget so the help guide can screenshot the row itself.
        container = QWidget()
        row = QHBoxLayout(container)
        row.setSpacing(10)
        row.setContentsMargins(0, 0, 0, 0)

        self._btn_start = QPushButton("▶  Start Download")
        self._btn_start.setMinimumHeight(36)
        self._btn_start.setMinimumWidth(150)
        self._btn_start.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-weight: bold; }"
            "QPushButton:disabled { background-color: #ccc; }"
            "QPushButton:hover:!disabled { background-color: #388e3c; }"
        )
        self._btn_start.clicked.connect(self._on_start)

        self._btn_cancel = QPushButton("■  Cancel")
        self._btn_cancel.setMinimumHeight(36)
        self._btn_cancel.setMinimumWidth(120)
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.setStyleSheet(
            "QPushButton { background-color: #c62828; color: white; font-weight: bold; }"
            "QPushButton:disabled { background-color: #ccc; }"
            "QPushButton:hover:!disabled { background-color: #d32f2f; }"
        )
        self._btn_cancel.clicked.connect(self._on_cancel)

        btn_clear = QPushButton("🗘  Clear")
        btn_clear.setMinimumHeight(36)
        btn_clear.clicked.connect(lambda: self._log_view.clear())

        btn_save = QPushButton("💾  Save")
        btn_save.setMinimumHeight(36)
        btn_save.clicked.connect(self._save_log)

        btn_about = QPushButton("ℹ️  About")
        btn_about.setMinimumHeight(36)
        btn_about.clicked.connect(self._show_about_dialog)

        btn_guide = QPushButton("📘  使用说明")
        btn_guide.setMinimumHeight(36)
        btn_guide.setToolTip("打开带界面截图的 HTML 使用说明（快捷键 F1）")
        btn_guide.clicked.connect(self._show_help_dialog)

        row.addWidget(self._btn_start)
        row.addWidget(self._btn_cancel)
        row.addStretch()
        row.addWidget(btn_clear)
        row.addWidget(btn_save)
        row.addWidget(btn_guide)
        row.addWidget(btn_about)

        self._actions_widget = container
        parent_layout.addWidget(container)

    # =========================================================================
    #    Slots  —  GUI control handlers
    # =========================================================================

    def _set_all_datasets(self, checked: bool) -> None:
        for cb in self._dataset_checkboxes.values():
            cb.setChecked(checked)

    def _browse_base_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select Target Directory", self._edit_base_dir.text(),
        )
        if path:
            self._edit_base_dir.setText(path)

    # ── Account: remember / register ────────────────────────────────────

    def _toggle_password_echo(self, shown: bool) -> None:
        self._edit_password.setEchoMode(
            QLineEdit.Normal if shown else QLineEdit.Password
        )

    def _on_remember_user_toggled(self, checked: bool) -> None:
        """'记住账号' toggled → persist the new state right away.

        Turning it off must delete the stored account, not merely clear the box.
        """
        self._sync_credentials()

    def _on_remember_pw_toggled(self, checked: bool) -> None:
        """'记住密码' toggled → persist the new state right away.

        Turning it off must delete the stored password immediately.
        """
        self._sync_credentials()

    def _sync_credentials(self) -> None:
        """Write the credentials file from the CURRENT checkbox + field state.

        The two options are fully independent: only switches that are checked
        contribute, and an unchecked switch removes its value from the file.
        Values of the *other* option are preserved, so e.g. unchecking the
        password never discards a remembered account.
        """
        remember_user = self._check_remember_user.isChecked()
        remember_pw = self._check_remember_pw.isChecked()
        existing = load_credentials()

        # Account: prefer what is on screen, else keep what is already stored.
        username = self._edit_username.text().strip()
        if not username and remember_user:
            username = existing.get("username", "")

        # Password: prefer the field; if it is empty and the option is on,
        # keep the already-stored secret instead of dropping it.
        password = self._edit_password.text()
        if not password and remember_pw:
            password = _decode_password(existing.get("password", ""))

        save_credentials(
            remember_username=remember_user,
            username=username or None,
            remember_password=remember_pw,
            password=password or None,
        )
        self._update_cred_hint()

    def _update_cred_hint(self) -> None:
        remember_user = self._check_remember_user.isChecked()
        remember_pw = self._check_remember_pw.isChecked()
        if remember_user and remember_pw:
            text = "✅ 账号与密码已保存在本机"
        elif remember_user:
            text = "✅ 仅记住账号（每次需输入密码）"
        elif remember_pw:
            text = "✅ 仅记住密码（每次需输入账号）"
        else:
            text = "未启用记忆功能"
        self._label_cred_hint.setText(f"<small>{text}</small>")

    def _open_register_page(self) -> None:
        """Open the official NASA Earthdata registration page in a browser."""
        url = EARTHDATA_REGISTER_URL
        self.statusBar().showMessage(f"Opening registration page: {url}")
        self._append_log(f"🌐  打开注册页面：{url}")
        if not open_url(url, self):
            # Last resort: show the link so it can be copied manually.
            box = QMessageBox(self)
            box.setWindowTitle("注册网址")
            box.setTextFormat(Qt.RichText)
            box.setText(
                "未能自动打开浏览器。请手动复制以下网址访问：<br><br>"
                f"<a href=\"{url}\">{url}</a>"
            )
            box.setTextInteractionFlags(Qt.TextSelectableByMouse)
            box.exec_()

    def _show_register_dialog(self) -> None:
        EarthdataRegisterDialog(self).exec_()

    def _show_qr_dialog(self) -> None:
        WeChatQRDialog(self).exec_()

    def _show_about_dialog(self) -> None:
        AboutDialog(self).exec_()

    def _show_declaration_dialog(self) -> None:
        """Technical stack, data source, licence and disclaimer."""
        DeclarationDialog(self, first_run=False).exec_()

    def _show_help_dialog(self) -> None:
        """Open the HTML 使用说明 in a popup.

        The screenshots ship with the release; they are regenerated from this
        window only when a file is missing (silently — the release build has no
        "refresh screenshots" button by design).
        """
        dlg = HelpDialog(self)
        missing = [s for s, _, _ in HELP_SHOTS
                   if not (docs_dir() / f"{s}.png").is_file()]
        if missing:
            try:
                dlg.refresh(regenerate_screenshots=True)
            except Exception:
                dlg.refresh(regenerate_screenshots=False)
        dlg.exec_()

    # ── Opening folders (file manager) ──────────────────────────────────

    def _open_base_dir_folder(self) -> None:
        """Reveal the target download directory in the file manager."""
        path = Path(self._edit_base_dir.text().strip())
        if not open_folder(path, self):
            return
        self.statusBar().showMessage(f"已在资源管理器中打开：{path}")
        self._append_log(f"📂  打开目标目录：{path}")

    def _open_tn_dir_folder(self) -> None:
        """Reveal the Technical Notes directory in the file manager."""
        path = Path(self._edit_tn_dir.text().strip())
        if not open_folder(path, self):
            return
        self.statusBar().showMessage(f"已在资源管理器中打开：{path}")
        self._append_log(f"📂  打开 Technical Notes 目录：{path}")

    # ── Help screenshots ────────────────────────────────────────────────

    _SHOT_WIDGETS = {
        "full_window": "self",
        "account": "_group_account",
        "params": "_group_params",
        "tn": "_group_tn",
        "datasets": "_group_datasets",
        "progress": "_group_progress",
        "log": "_group_log",
        "actions": "_actions_widget",
    }

    def capture_help_screenshots(self) -> Dict[str, bool]:
        """Screenshot this window and its sections into help_docs/.

        Returns {stem: written?}.  Each section is captured at its preferred
        height (sizeHint) even when the window is taller, so the pictures stay
        tidy instead of including large empty areas.
        """
        result: Dict[str, bool] = {}
        try:
            self.window().grab()          # force a layout/render pass
            QApplication.processEvents()
        except Exception:
            pass

        for stem, attr in self._SHOT_WIDGETS.items():
            try:
                if attr == "self":
                    widget = self
                    cap = None
                else:
                    widget = getattr(self, attr, None)
                    if widget is None:
                        result[stem] = False
                        continue
                    # Preferred height for group boxes, real height for the
                    # button row (it has no meaningful sizeHint).
                    hint = widget.sizeHint().height()
                    cap = hint if isinstance(widget, QGroupBox) else None
                saved = capture_widget_png(widget, f"{stem}.png", max_height=cap)
                result[stem] = saved is not None
            except Exception:
                result[stem] = False

        # Keep a standalone, self-contained HTML copy next to the pictures.
        try:
            write_help_html(result)
        except Exception:
            pass
        return result

    # ── Technical Notes (low-degree corrections) ────────────────────────

    def _browse_tn_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select Technical Notes Directory", self._edit_tn_dir.text(),
        )
        if path:
            self._edit_tn_dir.setText(path)

    def _on_download_tn(self) -> None:
        """Download the latest Technical Notes in a background thread."""
        tn_dir = Path(self._edit_tn_dir.text().strip())
        try:
            tn_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            QMessageBox.warning(
                self, "Validation Error",
                f"Cannot create target directory:\n{exc}",
            )
            return

        self._btn_tn.setEnabled(False)
        self._label_tn_status.setText("Downloading …")
        self._append_log("")

        self._thread_tn = QThread(self)
        self._worker_tn = TNNotesWorker(tn_dir, TN_FILES)
        self._worker_tn.moveToThread(self._thread_tn)

        self._thread_tn.started.connect(self._worker_tn.run)
        self._worker_tn.log_line.connect(self._append_log)
        self._worker_tn.progress.connect(self._update_progress)
        self._worker_tn.all_finished.connect(self._on_tn_finished)
        self._worker_tn.error_fatal.connect(self._on_fatal_error)

        self._worker_tn.all_finished.connect(self._thread_tn.quit)
        self._thread_tn.finished.connect(self._thread_tn.deleteLater)
        self._thread_tn.finished.connect(lambda: setattr(self, "_thread_tn", None))

        self._thread_tn.start()

    def _on_tn_finished(self, results: list) -> None:
        """Called when the TN worker completes."""
        self._btn_tn.setEnabled(True)
        ok = sum(1 for _, good in results if good)
        self._label_tn_status.setText(f"✅  {ok}/{len(results)} files OK")
        self.statusBar().showMessage(
            f"Technical Notes: {ok}/{len(results)} files downloaded to "
            f"{self._edit_tn_dir.text()}."
        )
        if ok == len(results) and results:
            self._append_log(
                "    ✅  All Technical Notes are up to date.  "
                "Re-run sh_to_grid.py to apply the new corrections."
            )

    def _selected_datasets(self) -> List[Tuple[str, str]]:
        return [
            key for key, cb in self._dataset_checkboxes.items() if cb.isChecked()
        ]

    # ── Start / Cancel ──────────────────────────────────────────────────

    def _on_start(self) -> None:
        """Validate inputs, then launch the download in a background thread."""
        username = self._edit_username.text().strip()
        password = self._edit_password.text()
        base_dir = Path(self._edit_base_dir.text().strip())
        selected = self._selected_datasets()
        degree = int(self._combo_degree.currentData())

        # Validation
        errors = []
        if not username:
            errors.append("Earthdata Username is required.")
        if not password:
            errors.append("Earthdata Password is required.")
        if not base_dir.exists():
            try:
                base_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                errors.append(f"Cannot create target directory: {exc}")
        if not selected:
            errors.append("Select at least one dataset to download.")

        if errors:
            errors.append(
                "\n没有账号？点击 “🆕 Register account (打开注册网址)” 注册，"
                "或使用菜单 文件 → 注册 Earthdata 账号。"
            )
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        # Save settings for next run (honours the two remember-* options)
        self._save_settings()

        # Prepare UI
        self._set_running_state(True)
        self._log_view.clear()
        self._summary_table.setRowCount(0)
        self._progress_bar.setMaximum(len(selected))
        self._progress_bar.setValue(0)
        self._label_status.setText("Starting …")
        self._all_stats = []

        # Create worker and thread
        self._thread = QThread(self)
        self._worker = DownloadWorker(
            username=username,
            password=password,
            base_dir=base_dir,
            selected_datasets=selected,
            degree=degree,
            max_workers=self._spin_threads.value(),
            max_retries=self._spin_retries.value(),
        )

        self._worker.moveToThread(self._thread)

        # Wire signals
        self._thread.started.connect(self._worker.run)
        self._worker.log_line.connect(self._append_log)
        self._worker.progress.connect(self._update_progress)
        self._worker.dataset_completed.connect(self._update_table_row)
        self._worker.all_finished.connect(self._on_finished)
        self._worker.error_fatal.connect(self._on_fatal_error)

        # Cleanup
        self._worker.all_finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(lambda: setattr(self, "_thread", None))

        self._thread.start()

    def _on_cancel(self) -> None:
        if self._worker:
            self._worker.cancel()
            self._btn_cancel.setEnabled(False)
            self._label_status.setText("Cancelling …")

    def _on_finished(self, all_stats: list) -> None:
        """Called when the worker completes (normally or by cancel)."""
        self._all_stats = all_stats
        self._set_running_state(False)
        self._print_summary(all_stats)
        self._label_status.setText("Finished.")
        self.statusBar().showMessage(
            f"Completed — {sum(s.get('downloaded', 0) for s in all_stats)} files downloaded."
        )

    def _on_fatal_error(self, message: str) -> None:
        self._append_log(f"\n❌  FATAL ERROR: {message}")
        self._set_running_state(False)
        self._label_status.setText("Error encountered.")
        hint = ""
        if "Auth" in message or "auth" in message or "401" in message:
            hint = (
                "\n\n提示：登录失败通常是因为账号未激活或密码错误。\n"
                "可点击 “🆕 Register account (打开注册网址)” 注册新账号。"
            )
        QMessageBox.critical(self, "Download Error", message + hint)

    # ── Progress updates (main thread) ──────────────────────────────────

    def _append_log(self, line: str) -> None:
        self._log_view.appendPlainText(line)
        # Auto-scroll to bottom
        self._log_view.moveCursor(QTextCursor.End)

    def _update_progress(self, current: int, total: int, status: str) -> None:
        self._progress_bar.setMaximum(max(total, 1))
        self._progress_bar.setValue(current)
        self._label_status.setText(status)

    def _set_summary_header(self) -> None:
        """Label the matched-count column with the currently selected degree."""
        degree = self._combo_degree.currentData() or DEFAULT_DEGREE
        self._summary_table.setHorizontalHeaderLabels(
            ["Centre", "Mission", "Version", "Found",
             f"Deg{degree}", "Have", "New", "Got"]
        )

    def _update_table_row(self, idx: int, stats: dict) -> None:
        """Insert a completed dataset into the summary table."""
        row = self._summary_table.rowCount()
        self._summary_table.insertRow(row)

        items = [
            QTableWidgetItem(str(stats.get("center", ""))),
            QTableWidgetItem(str(stats.get("mission", ""))),
            QTableWidgetItem(str(stats.get("version", ""))),
            QTableWidgetItem(str(stats.get("found", 0))),
            QTableWidgetItem(str(stats.get("matched", 0))),
            QTableWidgetItem(str(stats.get("already_have", 0))),
            QTableWidgetItem(str(stats.get("to_download", 0))),
            QTableWidgetItem(str(stats.get("downloaded", 0))),
        ]
        for col, item in enumerate(items):
            item.setTextAlignment(Qt.AlignCenter)
            self._summary_table.setItem(row, col, item)

        self._summary_table.resizeColumnsToContents()

    # ── Helpers ─────────────────────────────────────────────────────────

    def _set_running_state(self, running: bool) -> None:
        self._btn_start.setEnabled(not running)
        self._btn_cancel.setEnabled(running)
        # Disable config edits during run (remember-checkboxes stay editable)
        self._edit_username.setEnabled(not running)
        self._edit_password.setEnabled(not running)
        self._edit_base_dir.setEnabled(not running)
        self._combo_degree.setEnabled(not running)
        self._spin_threads.setEnabled(not running)
        self._spin_retries.setEnabled(not running)
        self._btn_register.setEnabled(not running)
        for cb in self._dataset_checkboxes.values():
            cb.setEnabled(not running)

    def _print_summary(self, all_stats: list) -> None:
        """Print a final summary table to the log view."""
        if not all_stats:
            return
        self._append_log("")
        self._append_log("=" * 62)
        self._append_log("📋  FINAL  SUMMARY")
        self._append_log("=" * 62)
        degree = (all_stats[0].get("degree", DEFAULT_DEGREE)
                  if all_stats else DEFAULT_DEGREE)
        header = "  {:6} {:10} {:>6} {:>6} {:>6} {:>6} {:>6}".format(
            "Centre", "Mission", "Found", f"Deg{degree}", "Have", "New", "Got",
        )
        self._append_log(header)
        self._append_log("  " + "-" * (len(header) - 2))

        total_found = total_matched = total_new = total_dl = 0
        for s in all_stats:
            line = "  {:<6} {:<10} {:>6} {:>6} {:>6} {:>6} {:>6}".format(
                s.get("center", ""),
                s.get("mission", ""),
                s.get("found", 0),
                s.get("matched", 0),
                s.get("already_have", 0),
                s.get("to_download", 0),
                s.get("downloaded", 0),
            )
            self._append_log(line)
            total_found += s.get("found", 0)
            total_matched += s.get("matched", 0)
            total_new += s.get("to_download", 0)
            total_dl += s.get("downloaded", 0)

        self._append_log("  " + "-" * (len(header) - 2))
        self._append_log(
            "  {:<17} {:>6} {:>6} {:>6} {:>6} {:>6}".format(
                "TOTAL", total_found, total_matched, "", total_new, total_dl,
            )
        )
        self._append_log("=" * 62)

    def _save_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "grace_download_log.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._log_view.toPlainText())
                f.write(
                    f"\n\n---\nGenerated by {APP_NAME} v{APP_VERSION}\n"
                    f"Author: {AUTHOR_NAME_CN} ({AUTHOR_NAME_EN})  "
                    f"<{AUTHOR_EMAIL}>  {AUTHOR_PHONE}\n"
                    f"{AUTHOR_AFFILIATION_CN} / {AUTHOR_AFFILIATION_EN}\n"
                    f"{WECHAT_QR_CAPTION}\n"
                    f"Source & releases: {PROJECT_URL}\n"
                )
            self.statusBar().showMessage(f"Log saved to {path}")

    # =========================================================================
    #    Settings persistence
    # =========================================================================

    def _save_settings(self) -> None:
        s = QSettings(self._SETTINGS_ORG, self._SETTINGS_APP)

        # ── Remember account / password → local credentials file ─────────
        # Two independent switches; either can be on without the other.
        self._sync_credentials()

        # ── Always-remembered, non-secret settings (registry / QSettings) ─
        s.setValue("base_dir", self._edit_base_dir.text().strip())
        s.setValue("tn_dir", self._edit_tn_dir.text().strip())
        s.setValue("degree", self._combo_degree.currentData())
        s.setValue("threads", self._spin_threads.value())
        s.setValue("retries", self._spin_retries.value())
        for (center, mission), cb in self._dataset_checkboxes.items():
            s.setValue(f"dataset/{center}/{mission}", cb.isChecked())
        s.sync()

    def _restore_settings(self) -> None:
        s = QSettings(self._SETTINGS_ORG, self._SETTINGS_APP)

        # The two remember switches live with the credentials they control,
        # so the whole feature keeps working even where QSettings/registry
        # writes are unavailable.
        creds = load_credentials()
        remember_user = creds.get("remember_username") == "true"
        remember_pw = creds.get("remember_password") == "true"

        # Block toggled() while applying the startup state, so restoring does
        # not immediately erase what is about to be restored.
        for cb in (self._check_remember_user, self._check_remember_pw):
            cb.blockSignals(True)
        self._check_remember_user.setChecked(remember_user)
        self._check_remember_pw.setChecked(remember_pw)
        for cb in (self._check_remember_user, self._check_remember_pw):
            cb.blockSignals(False)

        # ── Account (independent option) ─────────────────────────────────
        if remember_user and creds.get("username"):
            self._edit_username.setText(creds["username"])

        # ── Password (independent option) ────────────────────────────────
        if remember_pw and creds.get("password"):
            self._edit_password.setText(_decode_password(creds["password"]))

        # ── Directories / degree / threads / retries ─────────────────────
        if s.contains("base_dir"):
            self._edit_base_dir.setText(s.value("base_dir", str(DEFAULT_BASE_DIR)))
        if s.contains("tn_dir"):
            self._edit_tn_dir.setText(s.value("tn_dir", str(DEFAULT_TN_DIR)))
        if s.contains("degree"):
            idx = self._combo_degree.findData(int(s.value("degree", DEFAULT_DEGREE)))
            if idx >= 0:
                self._combo_degree.setCurrentIndex(idx)
        if s.contains("threads"):
            self._spin_threads.setValue(int(s.value("threads", 4)))
        if s.contains("retries"):
            self._spin_retries.setValue(int(s.value("retries", 3)))
        for (center, mission), cb in self._dataset_checkboxes.items():
            key = f"dataset/{center}/{mission}"
            if s.contains(key):
                cb.setChecked(s.value(key, "true") == "true")

        self._update_cred_hint()


# =============================================================================
#    Entry point
# =============================================================================

_NULL_STREAM = None


def _null_stream():
    """An inert stream that swallows writes (windowed builds have no console)."""
    class _NullStream:
        def write(self, text: str) -> int:      # noqa: D401
            return len(text) if text else 0

        def flush(self) -> None:
            return None

        def isatty(self) -> bool:
            return False

    return _NullStream()


def _silence_missing_streams() -> None:
    """Install the inert sink for any missing stdout/stderr.

    print() to a missing stream would raise, so this is a safety net.  Download
    progress still reaches the Log view because both workers replace sys.stdout
    with a Qt emitter while they run.
    """
    global _NULL_STREAM
    if sys.stdout is None or sys.stderr is None:
        _NULL_STREAM = _null_stream()
    if sys.stdout is None:
        sys.stdout = _NULL_STREAM  # type: ignore[assignment]
    if sys.stderr is None:
        sys.stderr = _NULL_STREAM  # type: ignore[assignment]


def run_self_test(deep: bool = False) -> int:
    """Check that this (frozen) installation can actually reach PODAAC.

    Used to verify a packaged release:

        GRACE_Downloader.exe --self-test          # imports, paths, write access
        GRACE_Downloader.exe --self-test --full   # + a live CMR search

    Writes the report to ``self_test.log`` (next to the executable) as well, so
    a windowed build without a console still leaves evidence.  Returns 0 on
    success.  Nothing here touches the GUI or downloads science data.
    """
    lines: List[str] = []
    failures = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        mark = "OK  " if ok else "FAIL"
        if not ok:
            failures += 1
        lines.append(f"[{mark}] {name}" + (f"  — {detail}" if detail else ""))

    lines.append(f"{APP_NAME} v{APP_VERSION}  self-test")
    lines.append(f"frozen        : {bool(getattr(sys, 'frozen', False))}")
    lines.append(f"executable    : {sys.executable}")
    lines.append(f"data root     : {data_root_dir()}")
    lines.append(f"resource root : {resource_base_dir()}")
    lines.append(f"python        : {sys.version.split()[0]}")
    lines.append("")

    check("icon present", ICON_PATH.is_file(), str(ICON_PATH))
    qr = wechat_qr_path()
    check("WeChat QR image found", qr is not None, str(qr))
    check("help guide HTML present", help_html_path().is_file(),
          str(help_html_path()))
    shots = [s for s, _, _ in HELP_SHOTS if (docs_dir() / f"{s}.png").is_file()]
    check("help screenshots present", len(shots) == len(HELP_SHOTS),
          f"{len(shots)}/{len(HELP_SHOTS)}")

    # The exe folder must be writable (credentials + regenerated screenshots).
    try:
        probe = data_root_dir() / ".grace_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        check("data folder writable", True, str(data_root_dir()))
    except Exception as exc:
        check("data folder writable", False, f"{type(exc).__name__}: {exc}")

    check("PyQt5 importable", "PyQt5" in sys.modules or _can_import("PyQt5"))
    check("earthaccess importable", _can_import("earthaccess"))
    check("fsspec importable", _can_import("fsspec"))
    check("s3fs importable (cloud backend)", _can_import("s3fs"))

    if deep:
        lines.append("")
        lines.append("live CMR search (needs network access) …")
        try:
            results = earthaccess.search_data(
                short_name="GRACE_GSM_L2_GRAV_CSR_RL06", count=5,
            )
            check("CMR search returned granules", len(results) > 0,
                  f"{len(results)} granule(s)")
            if results:
                marker = DEGREE_MARKERS[DEFAULT_DEGREE]
                matched = [g for g in results if granule_has_marker(g, marker)]
                check(f"granule files expose '{marker}'", len(matched) > 0,
                      f"{len(matched)} of {len(results)}")
        except Exception as exc:
            check("CMR search", False, f"{type(exc).__name__}: {exc}")

    lines.append("")
    lines.append(f"RESULT: {'ALL CHECKS PASSED' if failures == 0 else f'{failures} CHECK(S) FAILED'}")

    report = "\n".join(lines)
    try:
        (data_root_dir() / "self_test.log").write_text(report, encoding="utf-8")
        report += f"\n\n(log also written to {data_root_dir() / 'self_test.log'})"
    except Exception:
        pass

    print(report, flush=True)
    return 0 if failures == 0 else 1


def _can_import(module: str) -> bool:
    """True when *module* can be imported in this (possibly frozen) build."""
    try:
        __import__(module)
        return True
    except Exception:
        return False


def main():
    # A windowed build has no console: make sure print() cannot raise.
    _silence_missing_streams()

    # Ensure UTF-8 output on Windows
    if hasattr(sys.stdout, "reconfigure"):
        getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        getattr(sys.stderr, "reconfigure")(encoding="utf-8", errors="replace")

    # ── Diagnostic mode: verify a packaged installation ──────────────────
    if "--self-test" in sys.argv:
        deep = "--full" in sys.argv
        return run_self_test(deep=deep)

    # ── Print the declaration/credits notice and exit ─────────────────────
    if "--declaration" in sys.argv or "--credits" in sys.argv:
        text = (f"{APP_NAME} v{APP_VERSION}\n"
                f"Copyright (C) 2026 {AUTHOR_NAME_CN} ({AUTHOR_NAME_EN}), "
                f"{AUTHOR_AFFILIATION_CN}\n"
                f"Licence: GPL v3 (because this program uses PyQt5)\n"
                f"{'-' * 72}\n"
                f"{DECLARATION_TITLE}\n{'-' * 72}\n"
                f"{declaration_text()}\n")
        try:
            (data_root_dir() / "declaration.txt").write_text(text, encoding="utf-8")
            text += (f"\n(written to {data_root_dir() / 'declaration.txt'})\n")
        except Exception:
            pass
        print(text, flush=True)
        return 0

    # High-DPI friendly (Qt5 needs the attribute before QApplication exists)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(GraceDownloaderGUI._SETTINGS_ORG)

    # App icon (window + taskbar)
    if ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    # Larger default font (Chinese UI) so nothing is cramped
    app.setFont(QFont("Microsoft YaHei UI", 10))

    # Group boxes / menus a little airier than the Qt default
    app.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            margin-top: 14px;
            padding-top: 18px;
            padding-bottom: 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
        }
        QMenuBar { padding: 2px 4px; }
        QMenuBar::item { padding: 4px 10px; }
        QStatusBar { padding: 2px 6px; }
    """)

    window = GraceDownloaderGUI()
    window.show()
    # Declaration / credits notice on first run (skippable, remembered)
    QTimer.singleShot(0, window.maybe_show_first_run_notice)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
