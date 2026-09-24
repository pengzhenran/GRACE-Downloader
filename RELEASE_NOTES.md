# GRACE Downloader v1.0.1 发行说明

**GRACE & GRACE-FO Level-2 球谐重力场下载器**（图形界面）
版本 v1.0.1 · 发行版冻结（界面不再变更）

| 项目 | 内容 |
|------|------|
| 作者 | 彭桢燃（Zhenran Peng） |
| 单位 | 中国地质大学（武汉）China University of Geosciences (Wuhan) |
| 邮箱 | zhenran.peng@cug.edu.cn |
| 课题组公众号 | 地球重力与人类生活（TVGG） |
| 界面语言 | 中文 / English 双语标签 |
| 许可 | GNU GPL v3（因使用 PyQt5） |

---

## 本版更新（v1.0 → v1.0.1）

| 变更 | 说明 |
|------|------|
| 关于对话框 | 新增「源码仓库 Source」一行与「🌐 GitHub 仓库」按钮，一键打开项目主页 |
| 声明与致谢 | 「联系方式」一节加入源码 / 发行版 / 问题反馈链接 |
| 内置使用说明 | 页头加入仓库地址（可直接点击） |
| 保存的日志 | 页脚追加源码仓库地址 |
| 联系方式 | 邮箱、电话与课题组公众号与 v1.0 一致，未改动 |

> v1.0.1 与 v1.0 的下载功能完全相同，仅补充仓库与反馈入口；数据下载行为未做任何改动。

---

## 一、本版本功能

| 功能 | 说明 |
|------|------|
| 下载 GRACE / GRACE-FO Level-2 GSM 月重力场 | CSR、JPL、GFZ 三家 × GRACE（RL06）/ GRACE-FO（RL06.3） |
| 阶数选择 | Degree 60（BA01，默认）/ Degree 96（BB01，存于 `deg96/` 子目录） |
| 技术说明文件（Technical Notes） | TN-14（C20/C30 SLR 改正）、TN-13（一阶项地心改正，三家中心），公开文件、**无需账号** |
| 断点续传 | 自动跳过本地已存在的文件，可反复运行只补缺失部分 |
| 记住账号 / 记住密码 | **两个独立开关**，可只记其一；取消勾选立即删除本机保存的内容 |
| 注册账号 | 一键打开 NASA Earthdata 官方注册页，并内置注册步骤与账号规则说明 |
| 打开文件夹 | 目标目录、Technical Notes 目录可一键在资源管理器中打开 |
| 使用说明 | 菜单「帮助 → 使用说明」（快捷键 **F1**），带本软件各区域截图，HTML 渲染在弹出窗口内 |
| 作者信息 | 菜单「帮助 → 关于 / 作者信息」 |
| 日志 | 全过程日志，可清空 / 保存为 txt（文件末尾自动附作者信息） |

## 二、运行环境

- Windows 10 / 11（64 位）；macOS、Linux 亦可从源码运行
- 打包版**无需安装 Python**；源码运行需 `pip install earthaccess PyQt5`
- 需要能访问 NASA CMR / PO.DAAC（下载数据需 Earthdata 账号）

## 三、发行包内容

```
GRACE_Downloader_v1.0.1\
├── GRACE_Downloader.exe          ← 双击运行
├── _internal\                    ← 运行时库（勿删）
├── help_docs\
│   ├── 使用说明.html             ← 可直接用浏览器打开的说明（含截图）
│   ├── full_window.png           ← 各区域界面截图
│   └── ...（account / params / datasets / tn / progress / log / actions）
├── 使用说明.md                   ← 安装与账号说明
├── 方法说明.md                   ← 数据处理方法说明
├── 发行说明.md                   ← 本文件
├── grace_icon.ico
└── grace_icon_preview.png
```

## 四、快速上手

1. **注册账号**：界面「🆕 注册账号」→ 浏览器打开 <https://urs.earthdata.nasa.gov/users/new>
   填写用户名、密码、姓名、邮箱、国家（选 China），到邮箱点激活链接。
   - 用户名：4–30 位小写字母 / 数字 / `.` / `_`
   - 密码：≥12 位，含大写字母、小写字母、数字、特殊字符各至少一个
2. **填账号**：在「🔑 Account」区输入用户名与密码；需要自动填入就勾选「记住账号」「记住密码」。
3. **选目录**：在「⚙️ Download Settings」区选好 Target Directory（可点「📂 打开文件夹」查看）。
4. **选数据源**：默认全选 CSR / JPL / GFZ × GRACE / GRACE-FO，按需取消。
5. **开始**：点「▶ Start Download」，进度与日志实时显示；中断后可再次点击继续补齐。
6. **低阶项改正**：点「⬇️ Download Latest Technical Notes」，无需账号。

## 五、数据与目录说明

选择 Degree 60（默认）时数据下载到 `<目标目录>\<中心>\`；
选择 Degree 96 时下载到 `<目标目录>\deg96\<中心>\`，与 60 阶数据互不覆盖。

## 六、本机生成的文件

| 文件 | 说明 |
|------|------|
| `.grace_credentials.json` | 勾选「记住账号 / 记住密码」后保存的内容（密码仅 Base64 混淆，**不是加密**；不勾选则不生成，取消勾选即删除） |
| `help_docs\` | 使用说明截图与 HTML（随发行包提供；若缺失，首次打开说明时会自动重新截图生成） |
| 注册表 `HKCU\Software\GRACE-Downloader\GUI` | 界面偏好（目录、阶数、线程、重试、数据源勾选） |

> 公用电脑上请勿勾选「记住密码」。

## 七、安装 / 卸载

**方式一：安装程序（推荐）**

双击 `GRACE_Downloader_Setup_v1.0.1.exe`，按向导安装：

- 默认安装到 `%LOCALAPPDATA%\Programs\GRACE Downloader`（**不需要管理员权限**，也可改成全员安装）
- 安装程序约 47–50 MB，安装后约 124 MB
- 自动创建开始菜单项（程序、使用说明 HTML、卸载）与可选桌面快捷方式
- 卸载：开始菜单 → 卸载，或 `设置 → 应用 → GRACE Downloader`

**方式二：便携版**

直接解压 `GRACE_Downloader_v1.0.1\` 整个目录，双击 `GRACE_Downloader.exe` 即可，
不写注册表、不装任何东西。

**安装后自检**（可选，用于排查环境问题）：

```
GRACE_Downloader.exe --self-test          # 检查依赖与文件是否齐全
GRACE_Downloader.exe --self-test --full   # 外加一次真实的 CMR 检索
GRACE_Downloader.exe --declaration        # 打印声明 / 致谢与许可信息
```

结果分别写入程序目录下的 `self_test.log` 与 `declaration.txt`。
另外，程序**首次运行会自动弹出「声明与致谢」对话框**（技术栈、数据来源、GPL v3 许可
与免责声明），勾选「下次不再显示」后不再弹出，之后可随时从
**帮助 → 📄 声明与致谢** 打开。

## 八、打包与再发行

### 8.1 专用精简 Python 环境

本发行版使用一个**专门的精简环境**（不是 Anaconda base，避免把 419 个包一起打进程序）：

```bat
conda create -n grace -y --no-default-packages python=3.13 pip
%USERPROFILE%\anaconda3\envs\grace\python.exe -m pip install earthaccess PyQt5 pyinstaller
```

- 环境位置：`%USERPROFILE%\anaconda3\envs\grace`（约 337 MB，**44 个包**）
- 只装三样东西：`earthaccess`（含 fsspec / s3fs / requests 等依赖）、`PyQt5`、`pyinstaller`

### 8.2 构建步骤

```bat
:: 一键构建（自动使用上面的 grace 环境，含生成安装程序）
src\build_release.bat

:: 或分步执行
%USERPROFILE%\anaconda3\envs\grace\python.exe -m PyInstaller --clean --noconfirm ^
    --distpath dist --workpath build_release grace_downloader_release.spec
"E:\Inno Setup 6\ISCC.exe" installer_release.iss
```

详细说明见仓库内 `docs/构建与打包.md`。环境变量 `GRACE_PYTHON` 可覆盖使用的解释器。

### 8.3 打包时踩过的两个坑（已在 spec 中修好）

1. **`import ssl` 失败 → earthaccess 完全无法导入**
   conda 的 OpenSSL 动态库（`libssl-3-x64.dll`、`libcrypto-3-x64.dll`）不在任何包目录里，而在
   `<env>\Library\bin`，PyInstaller 的钩子找不到它们，于是打包后 `_ssl.pyd` 加载失败。
   现已由 `grace_downloader_release.spec` 显式收集这两个 DLL（约 8.4 MB）。

2. **包体从 449 MB 减到 124 MB**
   不要对 `s3fs / botocore / requests / certifi` 使用 `collect_all()`：它会把依赖树当作数据文件铺开，
   反而让里面的 urllib3 覆盖掉正确冻结的副本。同时对 `numba / llvmlite / rasterio / GDAL /
   scipy / pandas / xarray` 等 transitive 但用不到的库加了 `excludes`。

## 九、声明与许可（重要）

### 9.1 开发技术栈

| 组件 | 版本 | 许可 |
|---|---|---|
| 语言 | Python 3.13 | PSF |
| **图形界面** | **PyQt5 5.15.11**（绑定 Qt 5.15.2） | **GPL v3**（Riverbank 商业双许可） |
| sip 绑定 | PyQt5-sip 12.19.0 | SIP 许可 |
| Qt 5 运行时 | 5.15.2（`_internal\PyQt5\Qt5\`） | LGPL v3 |
| 数据访问 | earthaccess 0.19.0（fsspec / s3fs / aiobotocore / requests / python-cmr） | MIT / BSD / Apache-2.0 |
| 加密库 | OpenSSL 3.x（`libssl-3-x64.dll` / `libcrypto-3-x64.dll`） | Apache-2.0 |
| 打包 | PyInstaller 6.22.2（引导程序例外条款） | GPL-2.0-or-later |
| 安装程序 | Inno Setup 6.7.3 | Inno Setup License |
| 文档生成 | python-docx 1.2.0、lxml 6.1.3 | MIT / BSD-3-Clause |

> **本软件使用 PyQt5，不是 PySide6。**

### 9.2 许可结论

因使用 PyQt5，**本程序整体按 GPL v3 分发**。再分发时须保留版权与许可声明，
并一并提供完整源代码（本仓库 `src/grace_downloader_gui_release.py` 即发布版 exe
的对应源码）。完整条款见仓库内 `LICENSE`、`许可说明.md` 与 `第三方组件与许可声明.md`。

### 9.3 数据来源与免责

GRACE / GRACE-FO Level-2 GSM 月重力场数据与 GRACE Technical Notes 均来自
**NASA PO.DAAC**，版权归 NASA 及数据生产机构所有，使用须遵守 NASA Earthdata
数据使用条款。本软件**仅供科研与教学免费使用**，按「现状」提供，不对使用结果作任何
担保；因使用本软件造成的数据丢失、下载失败或其它损失，作者不承担责任。

## 十、数据来源与致谢

数据来自 NASA PO.DAAC：

- GRACE Level-2 GSM（CSR / JPL / GFZ，RL06）
- GRACE-FO Level-2 GSM（CSR / JPL / GFZ，RL06.3）
- GRACE Technical Notes（TN-13 / TN-14）

本软件仅供科研与教学使用，请遵守 NASA Earthdata 数据使用条款。

---

*作者：彭桢燃 · 中国地质大学（武汉）· zhenran.peng@cug.edu.cn*
*课题组公众号：地球重力与人类生活（TVGG）*
