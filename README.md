# VOA Daily Audio Downloader GUI

> 灵活归档 · 多线程加速 · 跨平台轻松批量下载 VOA “Daily English” 节目，自动识别 HQ 链接，并按“年 / 月”整理文件夹。

![screenshot](https://github.com/JustinYostar/VOA-Slow-English-Download/blob/main/screenshot.png) 

---

## 功能一览

| 功能            | 说明                                                                            |
| --------------- | ------------------------------------------------------------------------------- |
| **日期范围下载**    | 通过两个日历控件选择 *开始* / *结束* 日期，一键批量下载该区段所有 VOA Daily English 音频。                   |
| **自动 URL 适配** | 根据年份自动尝试不同域名、时码段 (`003003` / `003000`) 与 `_hq` / 普通版后缀，优先下载高质量 `_hq` 文件。      |
| **并发线程**      | 可在 GUI 中选择 1‑16 条并发下载线程（默认 4），显著提升批量下载速度。                                     |
| **目录归档**      | 文件按 `ROOT/年/月/日期.mp3` 结构自动保存，便于整理与后续播放器索引。                                    |
| **保存目录**   | 默认 `D:\VOA`，点击 “浏览…” 挑选任意硬盘或网络路径。。                                                   |
| **下载进度 & 停止** | 进度条实时显示完成度；点击“停止”立即取消剩余任务并删除未完成文件。                                            |
| **跨平台**       | 代码基于标准 `Tkinter` + `requests`，在 Windows 10/11、macOS、Linux (X11/Wayland) 测试通过。 |

---

## 环境要求

* **Python 3.8+**
* 依赖库：`requests`, `tkcalendar`, `tqdm`

```bash
pip install requests tkcalendar tqdm
```

> macOS 用户如遇 `tkcalendar` 中文无法显示，可安装思源黑体或改用英文界面。

---

## 快速开始

1. **克隆或下载** 本仓库代码。

2. 安装依赖：

   ```bash
   pip install -r requirements.txt  # 或手动安装依赖
   ```

3. 运行：

   ```bash
   python voa_downloader_gui.py
   ```

4. 在弹出的窗口中：

   * 选择 **开始 / 结束日期**
   * 根据网速设置 **并发线程数**（建议 4‑8 条最佳）
   * 确认 **保存目录**
   * 点击 **下载范围**，耐心等待进度条走完。

---

## 输出目录结构

```
D:│
  └─VOA
      ├─2025
      │   └─06
      │       └─20250609.mp3
      └─2024
          └─01
              └─20240101.mp3
```

* 若勾选 *跳过已存在*（默认启用），再次下载不会覆盖同名文件。

---

## 常见问题 FAQ

| 问题                                                 | 解决方案                                                                              |
| -------------------------------------------------- | --------------------------------------------------------------------------------- |
| 启动报 `SyntaxWarning: invalid escape sequence '\\V'` | 代码已改为原始字符串，确保路径前缀使用 `r"D:\\VOA"`，或在路径中用双反斜杠 / 正斜杠。                                |
| `SyntaxError: '(' was never closed`                | 请确认已使用 **最新** 源码；旧版本可能因复制不完整导致括号缺失。                                               |
| 下载速度慢                                              | 提高 **并发线程数**；同时确保网络对 `voa-audio-ns.akamaized.net` / `voa-audio.voanews.eu` 节点无瓶颈。 |
| 某些日期 404                                           | VOA 历史档案不完整，程序已自动跳过无法获取的文件。                                                       |

---

## 进阶用法

* **命令行批量**：可将核心下载逻辑抽离为 CLI 脚本，在无界面服务器环境运行。
* **计划任务**：结合系统任务计划（如 Windows 任务计划程序 / cron）每日自动拉取最新音频。
* **多语言界面**：将文本文案集中到 `i18n.py`，方便翻译成英语、法语等。

---

## 许可协议

本项目采用 [MIT License](LICENSE) 开源。在保留版权和许可声明的前提下，可自由使用、修改与再分发。

---

## 鸣谢

* Voice of America (VOA) 提供的 Daily English 节目音频。
* `tkcalendar` – 友好的 Tk 日历控件。
* `requests` – Python HTTP 简单之美。

---

🎉 **Enjoy your English listening journey!**

