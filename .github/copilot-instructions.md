# Copilot Instructions

## General rules

- **所有回复使用中文。**
- **禁止在未经用户允许的情况下执行 `git commit` 或 `git push`。**
- **每次功能更新后，及时同步更新 `README.md`。**

## Running the tool

```bash
python tab_save_tool.py
# or double-click:
tab_save_tool.bat   # auto-installs Python via winget if missing
```

No build, lint, or test setup exists in this project.

## Architecture

Single-file Python script (`tab_save_tool.py`) — no packages or dependencies beyond the standard library.

| Component | Description |
|---|---|
| `SAVE_PATH` / `BACKUP_BASE` | Hardcoded Windows paths at the top of the file — users must update these to match their username |
| `backup_meta.json` | JSON file inside `BACKUP_BASE` tracking timestamp + comment per slot; keys are zero-padded strings `"01"`–`"09"` |
| Backup slots | Directories named `BACKUP-01` through `BACKUP-09` inside `BACKUP_BASE`; slot 01 is always the newest |

**Save flow (add):** existing slots shift up by one (1→2, …, 8→9), slot 09 is deleted if full, then current game dir is copied to `BACKUP-01`.

**Restore flow (load):** script polls until `TheyAreBillions.exe` is not in `tasklist`, then `shutil.rmtree` + `shutil.copytree` swaps the game directory.

## Key conventions

- **Windows-only**: uses `msvcrt.getwch()` for raw keypress input (ESC to cancel, Enter to confirm). Do not replace with `input()` — ESC support would be lost.
- **Bilingual**: UI strings are Chinese; code identifiers and comments are English or inline Chinese. Keep new user-facing strings in Chinese.
- **Metadata backward-compat**: `load_meta()` silently upgrades old format (string value → `{"time": ..., "comment": ""}` dict). Any schema change must preserve this migration.
- **Slot numbering**: always zero-padded two-digit strings (`"01"`–`"09"`) as JSON keys and `BACKUP-{n:02d}` as directory names.
- **Path constants** (`SAVE_PATH`, `BACKUP_BASE`) are the only items a user needs to change; keep them at the top of the file with a clear comment.
