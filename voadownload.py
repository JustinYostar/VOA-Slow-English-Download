import os
import threading
import concurrent.futures
import requests
import datetime as dt
import itertools
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry

# ========= 可配置参数 =========
SAVE_DIR = r"D:\VOA"      # 根存储路径
CHUNK_SIZE = 8192           # 下载块大小 (bytes)
TIMEOUT = 15                # 网络超时 (秒)
SKIP_EXISTING = True        # 若文件已存在是否跳过
DOMAINS = [
    "https://voa-audio-ns.akamaized.net",
    "https://voa-audio.voanews.eu",
]
TIME_CODES = ["003003", "003000"]
SUFFIXES = ["_hq.mp3", ".mp3"]  # HQ 优先
DEFAULT_CONCURRENCY = 4           # 默认并发线程
MAX_CONCURRENCY = 16              # GUI 上限
# ============================

def generate_candidate_urls(the_date: dt.date):
    """Yield possible VOA mp3 URLs for *the_date*, ordered by priority."""
    for domain, time_code, suffix in itertools.product(DOMAINS, TIME_CODES, SUFFIXES):
        yield (
            f"{domain}/vle/"
            f"{the_date.year}/{the_date.month:02d}/{the_date.day:02d}/"
            f"{the_date:%Y%m%d}-{time_code}-vle122-program{suffix}"
        )

def get_dest_path(date: dt.date, root_dir: str) -> str:
    """Return full file path under root_dir/YYYY/MM/ for the date."""
    year_dir = os.path.join(root_dir, f"{date.year}")
    month_dir = os.path.join(year_dir, f"{date.month:02d}")
    os.makedirs(month_dir, exist_ok=True)
    return os.path.join(month_dir, f"{date:%Y%m%d}.mp3")

def download_one(date: dt.date, root_dir: str, stop_event: threading.Event) -> bool:
    """Download mp3 for *date* to year/month subfolder in *root_dir*.
    Returns True if saved or already exists, False otherwise."""
    file_path = get_dest_path(date, root_dir)

    if SKIP_EXISTING and os.path.isfile(file_path):
        return True

    for url in generate_candidate_urls(date):
        if stop_event.is_set():
            return False
        try:
            with requests.get(url, stream=True, timeout=TIMEOUT) as resp:
                if resp.status_code != 200:
                    continue  # 尝试下一个候选
                # 找到可用 URL – 写文件
                with open(file_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        if stop_event.is_set():
                            f.close()
                            os.remove(file_path)
                            return False
                        if chunk:
                            f.write(chunk)
                return True
        except requests.RequestException:
            continue  # 网络错误 → 尝试下个 URL
    return False  # 所有候选均失败

class RangeDownloaderThread(threading.Thread):
    """Manage a thread pool to download a list of dates in parallel."""

    def __init__(self, dates, root_dir, stop_event, progress_cb, concurrency: int):
        super().__init__(daemon=True)
        self.dates = dates
        self.root_dir = root_dir
        self.stop_event = stop_event
        self.progress_cb = progress_cb
        self.concurrency = concurrency

    def run(self):
        total = len(self.dates)
        completed = 0
        os.makedirs(self.root_dir, exist_ok=True)

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                future_to_date = {
                    executor.submit(download_one, d, self.root_dir, self.stop_event): d for d in self.dates
                }
                for future in concurrent.futures.as_completed(future_to_date):
                    if self.stop_event.is_set():
                        executor.shutdown(wait=False, cancel_futures=True)
                        self.progress_cb("stopped", "已手动停止")
                        return
                    completed += 1
                    self.progress_cb("progress", (completed, total))
        except Exception as e:
            self.progress_cb("error", str(e))
            return

        self.progress_cb("done", "全部下载完成 🎉")

class VOAApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VOA 音频批量下载器")
        self.resizable(False, False)
        self.configure(padx=18, pady=18)

        # ---- 日期选择 ----
        today = dt.date.today()
        ttk.Label(self, text="开始日期：").grid(row=0, column=0, sticky="w")
        self.start_entry = DateEntry(self, width=12, locale="zh_CN", date_pattern="yyyy-mm-dd",
                                     year=today.year, month=today.month, day=today.day)
        self.start_entry.grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(self, text="结束日期：").grid(row=1, column=0, sticky="w")
        self.end_entry = DateEntry(self, width=12, locale="zh_CN", date_pattern="yyyy-mm-dd",
                                   year=today.year, month=today.month, day=today.day)
        self.end_entry.grid(row=1, column=1, sticky="w", pady=4)

        # ---- 并发线程数 ----
        ttk.Label(self, text="并发线程：").grid(row=2, column=0, sticky="w")
        self.concurrency_var = tk.IntVar(value=DEFAULT_CONCURRENCY)
        self.thread_spin = ttk.Spinbox(self, from_=1, to=MAX_CONCURRENCY, width=5,
                                       textvariable=self.concurrency_var, wrap=True)
        self.thread_spin.grid(row=2, column=1, sticky="w", pady=4)

        # ---- 存储目录 ----
        self.dir_var = tk.StringVar(value=SAVE_DIR)
        ttk.Label(self, text="保存至：").grid(row=3, column=0, sticky="w")
        dir_frame = ttk.Frame(self)
        dir_frame.grid(row=3, column=1, sticky="w", pady=4)
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=28)
        self.dir_entry.pack(side="left")
        ttk.Button(dir_frame, text="浏览…", command=self.choose_dir).pack(side="left", padx=(6, 0))

        # ---- 进度条 ----
        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate", length=260)
        self.progress.grid(row=4, columnspan=2, pady=10)

        # ---- 控制按钮 ----
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, columnspan=2, pady=(0, 6))
        self.download_btn = ttk.Button(btn_frame, text="下载范围", command=self.start_download, width=14)
        self.download_btn.pack(side="left", padx=4)
        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_download, state="disabled", width=14)
        self.stop_btn.pack(side="left", padx=4)

        # ---- 状态 ----
        self.status_var = tk.StringVar(value="准备就绪")
        ttk.Label(self, textvariable=self.status_var).grid(row=6, columnspan=2, sticky="w")

        self.stop_event = threading.Event()
        self.thread: RangeDownloaderThread | None = None

    # ---- UI helpers ----
    def choose_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.dir_var.set(path)

    # ---- Download control ----
    def start_download(self):
        start_date = self.start_entry.get_date()
        end_date = self.end_entry.get_date()
        if end_date < start_date:
            messagebox.showerror("日期错误", "结束日期不能早于开始日期！")
            return

        # 生成日期列表（包含端点）
        total_days = (end_date - start_date).days + 1
        dates = [start_date + dt.timedelta(days=i) for i in range(total_days)]

        # 读取并发线程数
        concurrency = max(1, min(MAX_CONCURRENCY, self.concurrency_var.get()))

        # 重置 UI
        self.progress.configure(value=0, maximum=total_days)
        self.status_var.set(f"开始下载… (并发 {concurrency})")
        self.download_btn["state"] = "disabled"
        self.stop_btn["state"] = "normal"
        self.stop_event.clear()

        # 启动后台下载线程
        root_dir = self.dir_var.get()
        self.thread = RangeDownloaderThread(dates, root_dir, self.stop_event, self.on_progress, concurrency)
        self.thread.start()
        self.after(200, self.poll_thread)

    def stop_download(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.stop_btn["state"] = "disabled"

    def on_progress(self, kind: str, msg):
        def _update():
            if kind == "progress":
                completed, total = msg
                self.progress.configure(value=completed, maximum=total)
                pct = int(completed / total * 100)
                self.status_var.set(f"已完成 {completed}/{total} (约 {pct}%)")
            elif kind == "done":
                self.progress.configure(value=self.progress["maximum"])
                self.status_var.set(msg)
                self.download_btn["state"] = "normal"
                self.stop_btn["state"] = "disabled"
                messagebox.showinfo("完成", msg)
            elif kind == "error":
                self.status_var.set(f"错误: {msg}")
                self.download_btn["state"] = "normal"
                self.stop_btn["state"] = "disabled"
                messagebox.showerror("下载失败", msg)
            elif kind == "stopped":
                self.status_var.set(msg)
                self.download_btn["state"] = "normal"
                self.stop_btn["state"] = "disabled"
        self.after(0, _update)

    def poll_thread(self):
        if self.thread and self.thread.is_alive():
            self.after(200, self.poll_thread)

if __name__ == "__main__":
    VOAApp().mainloop()
