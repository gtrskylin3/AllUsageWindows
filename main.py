from collections import defaultdict
import win32gui
import time
import win32process
import psutil
from datetime import datetime
import sqlite3

storage = defaultdict(str)
time_process = {}


# class AppUsageDB:
#     def __init__(self, db_name="usage.db"):
#         self.conn = sqlite3.connect(db_name)
#         self.cursor = self.conn.cursor()
#         self._create_table()

#     def _create_table(self):
#         self.cursor.execute(
#             """
#             CREATE TABLE IF NOT EXISTS usage (
#                 name_process TEXT PRIMARY KEY,
#                 time REAL NOT NULL,
#                 time_type TEXT NOT NULL
#             )
#         """
#         )
#         self.conn.commit()

#     def _normalize_time

class AppUsageTracker:
    def __init__(self):
        self.usage_time = {}
        self.active_app = None
        self.last_switch_time = None

    def get_active_app(self) -> str:
        """Возвращает имя активного приложения"""
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            process = psutil.Process(pid)
            name = process.name().replace(".exe", "").title()
            return name
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            return "Unknown"

    def update_usage(self):
        """Обновляет время для текущего активного приложения"""
        current_app = self.get_active_app()

        if current_app != self.active_app:
            now = time.time()
            if self.active_app and self.last_switch_time:
                elapsed = now - self.last_switch_time
                self.usage_time[self.active_app] = (
                    self.usage_time.get(self.active_app, 0) + elapsed
                )
            self.active_app = current_app
            self.last_switch_time = now

    def format_time(self, seconds: float) -> str:
        """Красивый вывод времени"""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutes"
        else:
            return f"{seconds/3600:.1f} hours"

    def print_stats(self):
        stats = {app: self.format_time(sec) for app, sec in self.usage_time.items()}
        if self.active_app and self.last_switch_time:
            stats[self.active_app] = self.format_time(
                self.usage_time.get(self.active_app, 0)
                + (time.time() - self.last_switch_time)
            )
        print(stats)


if __name__ == "__main__":
    tracker = AppUsageTracker()
    try:
        while True:
            tracker.update_usage()
            tracker.print_stats()
            time.sleep(60)

    except KeyboardInterrupt:
        print("\nFinal stats:")
        tracker.print_stats()


# def storage_update_process_time(name: str):
#     """SAVES TIME FOR EACH APPLICATION"""
#     cur_time = time_process[name]
#     if cur_time < 60:
#         storage[name] = f"{cur_time} seconds"
#     elif 60 < cur_time < 3600:
#         storage[name] = f'{cur_time/60:.1f} minutes'
#     else:
#         storage[name] = f'{cur_time/3600:.1f} hours'

# def get_active_window():
#     hwnd = win32gui.GetForegroundWindow()
#     _, pid = win32process.GetWindowThreadProcessId(hwnd)
#     try:
#         process = psutil.Process(pid)
#         process_name = process.name()
#     except:
#         pass
#     process_name = process_name.replace('.exe', '').title()
#     if process_name not in storage:
#         time_process[process_name] = 1
#         storage_update_process_time(process_name)
#         return process_name
#     time_process[process_name] += 1
#     storage_update_process_time(process_name)
#     return process_name


# while True:
#     process_name = get_active_window()
#     print(process_name, storage[process_name])
#     sleep(time)
