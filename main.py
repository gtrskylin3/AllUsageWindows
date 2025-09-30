from collections import defaultdict
import win32gui
import time
import win32process
import psutil
from datetime import datetime
import sqlite3

storage = defaultdict(str)
time_process = {}


class AppUsageDB:
    def __init__(self, db_name="usage.db"):
        self.conn = sqlite3.connect(db_name, autocommit=True)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usage (
                name_process TEXT,
                date TEXT,
                time REAL NOT NULL,
                time_type TEXT NOT NULL,
                PRIMARY KEY (name_process, date)
            )
        """
        )
        self.conn.commit()

    def _to_seconds(self, seconds: int, type) -> float:
        if type == 'seconds':
            return seconds
        if type == 'minutes':
            return seconds * 60
    
        elif type== 'hours':
            return seconds * 3600
        
        raise ValueError('TYPE MUST BE HOURS OR MINUTES')
        
    def _normalize_time(self, seconds: float , type=None):
        """Красивый вывод времени"""
        if seconds < 60:
            return round(seconds), "seconds"
        elif seconds < 3600:
            return round(seconds/60, 2), "minutes"
        else:
            return round(seconds/3600, 2), "hours"

    def update_app_time(self, app: str, elapsed: float):
        """Добавляем или обновляем запись для приложения"""
        date = datetime.today().strftime("%Y-%m-%d")
        self.cursor.execute(
            "SELECT time, time_type FROM usage WHERE name_process=? AND date=?",
            (app, date))
        row = self.cursor.fetchone()

        if row:
            old_time, old_type = row
            if old_type != 'seconds':
                old_time = self._to_seconds(old_time, old_type)
            new_time = old_time + elapsed
            time_value, time_type = self._normalize_time(new_time, old_type)
            self.cursor.execute("""
                UPDATE usage SET time=?, time_type=? 
                WHERE name_process=? AND date=?
            """, (time_value, time_type, app, date))
        else:
            time_value, time_type = self._normalize_time(elapsed)
            self.cursor.execute(
                """
                INSERT INTO usage (name_process, date, time, time_type) 
                VALUES (?, ?, ?, ?)
            """, (app, date, time_value, time_type)
            )
            self.conn.commit()

    def fetch_all_time_stats(self):
        """Считает сумму времени за все время для каждого приложения"""
        self.cursor.execute("SELECT * FROM usage")
        all_rows = self.cursor.fetchall()
        answer = defaultdict(float)
        for name, _, time, time_type in all_rows:
            answer[name] += self._to_seconds(time, time_type)
        for k, v in answer.items():
            t, t_type = self._normalize_time(v)
            print(f"Total time {k}: {t:.1f} {t_type}")

    def fetch_daily_stats(self):
        """Возвращает все данные за день"""
        self.cursor.execute("SELECT * FROM usage")
        return self.cursor.fetchall()
    
    def print_stats(self):
        rows = self.fetch_daily_stats()
        print("\nUsage stats:")
        for name, date, t, t_type in rows:
            print(f"{date=} {name=}: {t:.1f} {t_type}")
    
    def close(self):
        self.conn.close()


class AppUsageTracker:
    def __init__(self, db: AppUsageDB):
        self.db = db
        self.active_app = None
        self.last_switch_time = time.time()

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

        # if current_app != self.active_app:
        now = time.time()
        if self.active_app and self.last_switch_time:
            elapsed = now - self.last_switch_time
            self.db.update_app_time(self.active_app, elapsed)
        self.active_app = current_app
        self.last_switch_time = now



if __name__ == "__main__":
    db = AppUsageDB()
    tracker = AppUsageTracker(db)

    try:
        while True:
            tracker.update_usage()
            db.print_stats()
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nFinal stats:")
        db.fetch_all_time_stats()
        db.print_stats()
        db.close()


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
