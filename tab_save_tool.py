"""
亿万僵尸 - 多存档工具
They Are Billions - Multi-Save Tool
"""

import os
import sys
import json
import shutil
import subprocess
import msvcrt
import unicodedata
from datetime import datetime

# ── 路径常量 ──────────────────────────────────────────────────────────────────
SAVE_PATH   = r"C:\Users\zw\Documents\My Games\They Are Billions"
BACKUP_BASE = r"C:\Users\zw\Documents\My Games\They Are Billions BACKUPS"
META_FILE   = os.path.join(BACKUP_BASE, "backup_meta.json")
MAX_BACKUPS = 9
UNKNOWN_TIME = "时间未知"

# ── ANSI 颜色 ─────────────────────────────────────────────────────────────────
C_RESET  = "\033[0m"
C_CYAN   = "\033[96m"
C_DCYAN  = "\033[36m"
C_GRAY   = "\033[90m"
C_GREEN  = "\033[92m"
C_RED    = "\033[91m"
C_YELLOW = "\033[93m"
BOX_W    = 70   # 边框内容宽度（含左右各 1 个空格）

# ── ANSI 支持 ─────────────────────────────────────────────────────────────────
def _enable_ansi() -> None:
    """开启 Windows 终端 ANSI 颜色支持。"""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        k32.SetConsoleMode(k32.GetStdHandle(-11), 7)
    except Exception:
        pass


# ── 显示宽度计算 ──────────────────────────────────────────────────────────────
def _char_width(ch: str) -> int:
    cp = ord(ch)
    if cp > 0xFFFF:
        return 2  # 补充平面字符（大部分彩色 emoji）
    if 0x2300 <= cp <= 0x23FF or 0x2600 <= cp <= 0x27FF:
        return 2  # Misc Technical / Symbols / Dingbats（✅⏳ 等）
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def _dw(s: str) -> int:
    """计算字符串在等宽终端中的显示宽度（CJK 字符和 Emoji 占 2 列）。"""
    return sum(_char_width(ch) for ch in s)


def _trunc(text: str, max_dw: int) -> str:
    """截断字符串使显示宽度不超过 max_dw，超出时末尾加 '…'。"""
    w = 0
    for i, ch in enumerate(text):
        cw = _char_width(ch)
        if w + cw > max_dw - 1:
            return text[:i] + "…"
        w += cw
    return text


# ── 边框工具 ──────────────────────────────────────────────────────────────────
def _box_top() -> None:
    print("┌" + "─" * BOX_W + "┐")


def _box_bottom() -> None:
    print("└" + "─" * BOX_W + "┘")


def _box_sep() -> None:
    print("├" + "─" * BOX_W + "┤")


def _box_line(text: str = "", color: str = "") -> None:
    """打印带左右边框的一行，文本自动右填充空格。"""
    pad = max(0, BOX_W - 2 - _dw(text))
    colored = (color + text + C_RESET) if color else text
    print(f"│ {colored}{' ' * pad} │")


def _box_raw_line(pre_colored: str, visible_dw: int) -> None:
    """打印含 ANSI 码的行；visible_dw 为去除 ANSI 后的可见显示宽度。"""
    pad = max(0, BOX_W - 2 - visible_dw)
    print(f"│ {pre_colored}{' ' * pad} │")


# ── 进度条 ────────────────────────────────────────────────────────────────────
def _scan_total_bytes(path: str) -> int:
    """递归统计目录下所有文件的总字节数。"""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for fn in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, fn))
            except OSError:
                pass
    return total


def _render_bar(copied: int, total: int) -> None:
    """原地刷新进度条（使用 \\r）。"""
    BAR_W = 24
    pct   = (copied / total) if total > 0 else 1.0
    filled = int(BAR_W * pct)
    bar    = "█" * filled + "░" * (BAR_W - filled)
    mb_done  = copied / 1_048_576
    mb_total = total  / 1_048_576
    line = f"  复制中... {bar} {pct*100:3.0f}%  ({mb_done:.1f} MB / {mb_total:.1f} MB)"
    sys.stdout.write(f"\r{C_CYAN}{line}{C_RESET}   ")
    sys.stdout.flush()


def _copy_tree_with_progress(src: str, dst: str) -> None:
    """带进度条的目录复制。"""
    total   = _scan_total_bytes(src)
    counter = [0]

    def _copy_fn(s: str, d: str) -> None:
        shutil.copy2(s, d)
        try:
            counter[0] += os.path.getsize(s)
        except OSError:
            pass
        _render_bar(counter[0], total)

    _render_bar(0, total)
    shutil.copytree(src, dst, copy_function=_copy_fn)
    _render_bar(total, total)
    print()


# ── 元数据 I/O ────────────────────────────────────────────────────────────────
def load_meta() -> dict:
    """读取备份元数据，键为 '01'~'09'，值为包含 'time' 和 'comment' 的字典。

    兼容旧格式（值为纯时间字符串）：自动转换为新格式。
    """
    if os.path.isfile(META_FILE):
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # 兼容旧格式：值为纯字符串时，转换为新格式
            for key, val in raw.items():
                if isinstance(val, str):
                    raw[key] = {"time": val, "comment": ""}
            return raw
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_meta(meta: dict) -> None:
    os.makedirs(BACKUP_BASE, exist_ok=True)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


# ── 路径辅助 ──────────────────────────────────────────────────────────────────
def backup_path(n: int) -> str:
    return os.path.join(BACKUP_BASE, f"BACKUP-{n:02d}")


# ── 带 ESC 支持的输入 ────────────────────────────────────────────────────────
def read_line(prompt: str):
    """逐字符读取输入；按 ESC 返回 None，按 Enter 返回字符串。"""
    print(prompt, end="", flush=True)
    buf = []
    while True:
        ch = msvcrt.getwch()
        if ch == "\x1b":           # ESC
            print()
            return None
        elif ch in ("\r", "\n"):   # Enter
            print()
            return "".join(buf)
        elif ch == "\x08":         # Backspace
            if buf:
                buf.pop()
                print("\b \b", end="", flush=True)
        elif ch >= " ":            # 可打印字符
            buf.append(ch)
            print(ch, end="", flush=True)


# ── 检测游戏存档路径 ──────────────────────────────────────────────────────────
def check_save_path() -> bool:
    if not os.path.isdir(SAVE_PATH):
        print(f"\n{C_RED}[错误] 未找到游戏存档目录：{C_RESET}\n  {SAVE_PATH}")
        print("请确认游戏已安装并至少运行过一次。")
        return False
    return True


# ── 检测游戏进程 ─────────────────────────────────────────────────────────────
GAME_EXE = "TheyAreBillions.exe"

def is_game_running() -> bool:
    result = subprocess.run(
        f'tasklist /FI "IMAGENAME eq {GAME_EXE}" /NH',
        shell=True, capture_output=True, text=True
    )
    return GAME_EXE.lower() in result.stdout.lower()


# ── 添加存档 ──────────────────────────────────────────────────────────────────
def add_save() -> None:
    os.makedirs(BACKUP_BASE, exist_ok=True)
    meta = load_meta()

    # 超出上限时删除最旧存档（BACKUP-09）
    oldest = backup_path(MAX_BACKUPS)
    if os.path.isdir(oldest):
        print(f"\n  {C_YELLOW}已达 {MAX_BACKUPS} 个存档上限，删除最旧存档 BACKUP-{MAX_BACKUPS:02d}...{C_RESET}")
        shutil.rmtree(oldest)
        meta.pop(f"{MAX_BACKUPS:02d}", None)

    # 将现有存档依次向后移一位（8→9, 7→8, ..., 1→2）
    for i in range(MAX_BACKUPS - 1, 0, -1):
        src = backup_path(i)
        dst = backup_path(i + 1)
        if os.path.isdir(src):
            os.rename(src, dst)
            key_old = f"{i:02d}"
            key_new = f"{i + 1:02d}"
            if key_old in meta:
                meta[key_new] = meta.pop(key_old)

    # 询问用户是否添加注释
    comment_input = read_line(f"\n  {C_YELLOW}请输入存档注释（直接按 Enter 跳过）：{C_RESET}")
    comment = (comment_input or "").strip()

    # 将当前游戏存档复制为 BACKUP-01（带进度条）
    dst01 = backup_path(1)
    print()
    _copy_tree_with_progress(SAVE_PATH, dst01)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta["01"] = {"time": timestamp, "comment": comment}
    save_meta(meta)

    print()
    _box_top()
    _box_line(f"  ✅ 已保存为 BACKUP-01  ({timestamp})", C_GREEN)
    if comment:
        _box_line(f"     注释：{comment}", C_GRAY)
    _box_bottom()


# ── 读取存档 ──────────────────────────────────────────────────────────────────
def load_save() -> None:
    # 自动检测游戏是否在运行
    while is_game_running():
        print()
        _box_top()
        _box_line("  🔴 检测到游戏正在运行，请先关闭游戏。", C_RED)
        _box_bottom()
        input(f"  {C_GRAY}关闭游戏后按 Enter 继续...{C_RESET}")

    print()
    _box_top()
    _box_line("  ✅ 游戏已关闭，可安全操作。", C_GREEN)
    _box_sep()

    meta = load_meta()

    # 列出现有存档
    available = []
    for i in range(1, MAX_BACKUPS + 1):
        p = backup_path(i)
        if os.path.isdir(p):
            key = f"{i:02d}"
            entry = meta.get(key, {})
            if isinstance(entry, dict):
                timestamp = entry.get("time", UNKNOWN_TIME)
                comment   = entry.get("comment", "")
            else:
                timestamp = str(entry) if entry else UNKNOWN_TIME
                comment   = ""
            available.append((i, timestamp, comment))

    if not available:
        _box_line("  尚无任何备份存档，请先使用「添加存档」功能。", C_YELLOW)
        _box_bottom()
        return

    # 列宽（显示列数）
    COL_NUM  = 3   # "1."
    COL_NAME = 11  # "BACKUP-01"
    COL_TS   = 21  # "2026-04-08 09:30:00"
    # 前缀固定宽度：3(缩进) + COL_NUM + 2(间距) + COL_NAME + 2 + COL_TS + 2
    PREFIX_DW = 3 + COL_NUM + 2 + COL_NAME + 2 + COL_TS + 2
    CM_MAX_DW = BOX_W - 2 - PREFIX_DW

    # 表头
    hdr = (
        "   "
        + "#" + " " * (COL_NUM  - _dw("#"))        + "  "
        + "备份名称" + " " * (COL_NAME - _dw("备份名称")) + "  "
        + "保存时间" + " " * (COL_TS   - _dw("保存时间")) + "  "
        + "注释"
    )
    _box_line(hdr, C_GRAY)
    _box_sep()

    for n, ts, cm in available:
        num_s  = f"{n}."
        name_s = f"BACKUP-{n:02d}"
        cm_s   = _trunc(cm, CM_MAX_DW) if cm else "—"
        num_pad  = " " * max(0, COL_NUM  - _dw(num_s))
        name_pad = " " * max(0, COL_NAME - _dw(name_s))
        ts_pad   = " " * max(0, COL_TS   - _dw(ts))
        visible_dw = PREFIX_DW + _dw(cm_s)
        colored = (
            "   "
            + C_YELLOW + num_s  + C_RESET + num_pad  + "  "
            + C_CYAN   + name_s + C_RESET + name_pad + "  "
            + C_GRAY   + ts     + C_RESET + ts_pad   + "  "
            + (C_GRAY + cm_s + C_RESET if not cm else cm_s)
        )
        _box_raw_line(colored, visible_dw)

    _box_sep()
    valid_nums = [n for n, _, _ in available]
    _box_line(f"   请输入编号（{valid_nums[0]}~{valid_nums[-1]}）恢复存档，ESC 取消", C_GRAY)
    _box_bottom()

    # 获取用户选择
    while True:
        raw = read_line(f"\n  {C_YELLOW}请输入存档编号：{C_RESET}")
        if raw is None:
            print(f"  {C_GRAY}操作已取消。{C_RESET}")
            return
        if raw.strip().isdigit() and int(raw.strip()) in valid_nums:
            choice = int(raw.strip())
            break
        print(f"  {C_RED}无效输入，请输入列表中的编号。{C_RESET}")

    src = backup_path(choice)
    key = f"{choice:02d}"
    entry = meta.get(key, {})
    if isinstance(entry, dict):
        ts = entry.get("time", UNKNOWN_TIME)
        cm = entry.get("comment", "")
    else:
        ts = str(entry) if entry else UNKNOWN_TIME
        cm = ""

    print(f"\n  {C_GRAY}正在清理当前存档...{C_RESET}")
    shutil.rmtree(SAVE_PATH)
    print()
    _copy_tree_with_progress(src, SAVE_PATH)

    print()
    _box_top()
    _box_line(f"  ✅ 已恢复 BACKUP-{choice:02d}  ({ts})", C_GREEN)
    if cm:
        _box_line(f"     注释：{cm}", C_GRAY)
    _box_sep()
    _box_line("     现在可以启动游戏继续游玩。", C_GRAY)
    _box_bottom()


# ── 主菜单 ────────────────────────────────────────────────────────────────────
def main() -> None:
    _enable_ansi()

    if not check_save_path():
        input("\n按 Enter 退出...")
        return

    while True:
        existing = sum(1 for i in range(1, MAX_BACKUPS + 1) if os.path.isdir(backup_path(i)))
        max_path_dw = BOX_W - 2 - _dw("  📁 存档路径：")
        display_path = SAVE_PATH if _dw(SAVE_PATH) <= max_path_dw else "..." + SAVE_PATH[-(max_path_dw - 3):]

        print()
        _box_top()
        _box_line("  亿万僵尸  They Are Billions", C_CYAN)
        _box_line("  多存档管理工具  v1.1", C_DCYAN)
        _box_sep()
        _box_line(f"  📁 存档路径：{display_path}", C_GRAY)
        _box_line(f"  💾 当前备份：{existing} / {MAX_BACKUPS}", C_YELLOW)
        _box_sep()
        _box_line()
        _box_line("    1  →  添加存档（备份当前游戏存档）")
        _box_line("    2  →  读取存档（恢复某个备份到游戏）")
        _box_line()
        _box_line("   ESC  退出", C_GRAY)
        _box_line()
        _box_bottom()

        choice = read_line(f"\n  {C_YELLOW}请输入操作编号：{C_RESET}")

        if choice is None:
            break
        elif choice.strip() == "1":
            add_save()
        elif choice.strip() == "2":
            load_save()
        else:
            print(f"  {C_RED}无效输入。{C_RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已中断。")
        sys.exit(0)
