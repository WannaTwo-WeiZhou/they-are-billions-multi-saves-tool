# 亿万僵尸 - 多存档工具
**They Are Billions - Multi-Save Tool**

亿万僵尸官方只支持单一存档，本工具通过备份/恢复机制实现最多 9 个存档槽位。

## 功能

- **添加存档**：将当前游戏存档备份为一个新槽位（最多 9 个，超出时自动删除最旧的）
- **添加注释**：保存存档时可输入一段注释（如"第二波之前"），也可直接按 Enter 跳过
- **读取存档**：选择某个备份槽位恢复为当前游戏存档，列表中会同时显示各存档的注释信息
- 读取存档时自动检测游戏是否在运行，避免存档损坏
- 每个备份槽位记录保存时间及注释

## 使用方法

1. 确保已安装 Python 3
2. 双击运行 `tab_save_tool.bat`，或直接运行：
   ```
   python tab_save_tool.py
   ```
3. 按菜单提示操作：
   - 按 `1` 备份当前存档
   - 按 `2` 恢复某个备份
   - 按 `ESC` 退出

## 路径说明

| 路径 | 说明 |
|------|------|
| `C:\Users\<你的用户名>\Documents\My Games\They Are Billions` | 游戏存档目录 |
| `C:\Users\<你的用户名>\Documents\My Games\They Are Billions BACKUPS` | 备份存放目录 |

> 如果你的 Windows 用户名不是 `zw`，请修改 `tab_save_tool.py` 顶部的 `SAVE_PATH` 和 `BACKUP_BASE` 路径。

## 系统要求

- Windows
- Python 3.x
- 亿万僵尸（They Are Billions）
