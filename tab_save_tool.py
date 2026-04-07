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
from datetime import datetime

# ── 路径常量 ──────────────────────────────────────────────────────────────────
SAVE_PATH   = r"C:\Users\zw\Documents\My Games\They Are Billions"
BACKUP_BASE = r"C:\Users\zw\Documents\My Games\They Are Billions BACKUPS"
META_FILE   = os.path.join(BACKUP_BASE, "backup_meta.json")
MAX_BACKUPS = 9


# ── 元数据 I/O ────────────────────────────────────────────────────────────────
def load_meta() -> dict:
    """读取备份时间戳元数据，键为 '01'~'09'，值为时间字符串。"""
    if os.path.isfile(META_FILE):
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
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
        print(f"\n[错误] 未找到游戏存档目录：\n  {SAVE_PATH}")
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

    # 显示现有存档列表（含时间戳）
    existing = [(i, meta.get(f"{i:02d}", "时间未知"))
                for i in range(1, MAX_BACKUPS + 1)
                if os.path.isdir(backup_path(i))]
    if existing:
        print("\n──── 当前存档列表 ────────────────────────────────")
        for n, ts in existing:
            print(f"  BACKUP-{n:02d}  ({ts})")
        print("──────────────────────────────────────────────────")

    # 超出上限时删除最旧存档（BACKUP-09）
    oldest = backup_path(MAX_BACKUPS)
    if os.path.isdir(oldest):
        print(f"  已达 {MAX_BACKUPS} 个存档上限，删除最旧存档 BACKUP-{MAX_BACKUPS:02d}...")
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

    # 将当前游戏存档复制为 BACKUP-01
    dst01 = backup_path(1)
    print(f"  正在复制存档，请稍候...")
    shutil.copytree(SAVE_PATH, dst01)
    meta["01"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_meta(meta)
    print(f"\n[成功] 存档已保存为 BACKUP-01（{meta['01']}）")


# ── 读取存档 ──────────────────────────────────────────────────────────────────
def load_save() -> None:
    # 自动检测游戏是否在运行
    while is_game_running():
        print("\n[提示] 检测到游戏正在运行，请先关闭游戏。")
        input("关闭游戏后按 Enter 继续...")
    print("\n[检测] 游戏已关闭，继续操作。")

    meta = load_meta()

    # 列出现有存档
    available = []
    for i in range(1, MAX_BACKUPS + 1):
        p = backup_path(i)
        if os.path.isdir(p):
            key = f"{i:02d}"
            timestamp = meta.get(key, "时间未知")
            available.append((i, timestamp))

    if not available:
        print("\n[提示] 尚无任何备份存档，请先使用「添加存档」功能。")
        return

    print("\n──── 可用存档列表 ────────────────────────────────")
    for idx, (n, ts) in enumerate(available, start=1):
        print(f"  {n}. BACKUP-{n:02d}  ({ts})")
    print("──────────────────────────────────────────────────")

    # 获取用户选择
    valid_nums = [n for n, _ in available]
    while True:
        raw = read_line(f"\n请输入存档编号（{valid_nums[0]}~{valid_nums[-1]}），ESC 取消：")
        if raw is None:
            print("操作已取消。")
            return
        if raw.strip().isdigit() and int(raw.strip()) in valid_nums:
            choice = int(raw.strip())
            break
        print(f"  无效输入，请输入列表中的编号。")

    src = backup_path(choice)
    key = f"{choice:02d}"
    ts  = meta.get(key, "时间未知")

    print(f"\n  正在恢复 BACKUP-{choice:02d}（{ts}），请稍候...")
    # 先删除当前游戏存档，再复制所选备份
    shutil.rmtree(SAVE_PATH)
    shutil.copytree(src, SAVE_PATH)
    print(f"\n[成功] 已将 BACKUP-{choice:02d} 恢复为当前游戏存档。")
    print("  现在可以启动游戏继续游玩。")


# ── 主菜单 ────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 50)
    print("   亿万僵尸 - 多存档工具  v1.0")
    print("=" * 50)

    if not check_save_path():
        input("\n按 Enter 退出...")
        return

    while True:
        print(f"\n游戏存档路径：{SAVE_PATH}")

        # 统计现有备份数量
        existing = sum(1 for i in range(1, MAX_BACKUPS + 1) if os.path.isdir(backup_path(i)))
        print(f"当前备份数量：{existing} / {MAX_BACKUPS}")

        print("\n请选择操作：")
        print("  1. 添加存档（备份当前游戏存档）")
        print("  2. 读取存档（恢复某个备份到游戏）")
        print("  ESC. 退出")

        choice = read_line("\n请输入操作编号：")

        if choice is None:
            break
        elif choice.strip() == "1":
            add_save()
        elif choice.strip() == "2":
            load_save()
        else:
            print("无效输入。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已中断。")
        sys.exit(0)
