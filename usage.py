from collections import defaultdict
import win32gui
import time
import win32process
import psutil
from datetime import datetime
import sqlite3

storage = defaultdict(str)
time_process = {}

# Список процессов, которые не учитываются в трекинге (приводятся к .title() ниже)
IGNORED_APPS = {
    'Explorer',
    'Windowsterminal',
    'Taskmgr',
    'Unknown',
    'Applicationframehost',
    'Runtimebroker',
    'Startmenuexperiencehost',
    'Searchexperiencehost',
    'Searchui',
    'Shelleexperiencehost',
    'Systemsettings',
    'Textinputhost',
    'Ctfmon',
    'Dllhost',
    'Wwahost',
    'Yourphone',
    'Widgets',
}

import sqlite3
from pathlib import Path

class AppUsageDB:
    def __init__(self, db_name="usage.db"):
        # Берем путь к папке, где находится скрипт gui.py
        script_path = Path(__file__).resolve()
        # Если база должна быть в корне проекта (например, на уровень выше скрипта)
        root_path = script_path.parent
        db_path = root_path / db_name

        # Подключаемся к базе по абсолютному пути
        self.conn = sqlite3.connect(db_path)
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

    def _to_seconds(self, time: int, type) -> float:
        if type == 'seconds':
            return time
        if type == 'minutes':
            return time * 60
    
        elif type== 'hours':
            return time * 3600
        
        raise ValueError('Invalid time type; must be "seconds", "minutes", or "hours"')
        
    def _normalize_time(self, seconds: float):
        """Normalize time to a readable unit"""
        if seconds < 60:
            return round(seconds), "seconds"
        elif seconds < 3600:
            return round(seconds/60, 10), "minutes"
        else:
            return round(seconds/3600, 10), "hours"

    def update_app_time(self, app: str, elapsed: float):
        """Add or update time for an app on today's date."""
        if app in IGNORED_APPS:
            return
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
            time_value, time_type = self._normalize_time(new_time)
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
        """Return total time stats for all apps across all days as a dict."""
        self.cursor.execute("SELECT * FROM usage")
        all_rows = self.cursor.fetchall()
        totals = defaultdict(float)
        for name, _, time, time_type in all_rows:
            totals[name] += self._to_seconds(time, time_type)
        result = {}
        for name, total_seconds in sorted(totals.items(), key=lambda x: x[1], reverse=True):
            time_value, time_type = self._normalize_time(total_seconds)
            result[name] = {'time': time_value, 
                            'type': time_type}
        return result

    def fetch_today_stats(self):
        """Return today's stats as a list of dicts, sorted by time descending."""
        today = datetime.today().strftime('%Y-%m-%d')
        self.cursor.execute("SELECT * FROM usage WHERE date=?", (today,))
        rows = self.cursor.fetchall()
        result = []
        for name, date, time, time_type in rows:
            seconds = self._to_seconds(time, time_type)
            result.append({'name': name, 'date': date, 'time': time, 'type': time_type, 'seconds': seconds})
        return sorted(result, key=lambda x: x['seconds'], reverse=True)
    
    def fetch_daily_stats(self):
        """Return today's stats as a list of dicts, sorted by time descending."""
        
        self.cursor.execute("SELECT * FROM usage")
        rows =  self.cursor.fetchall()
        return [{'name': name, 'date': date, 'time': time, 'type': time_type}
                for name, date, time, time_type in rows]
    
    # def print_stats(self):
    #     rows = self.fetch_daily_stats()
    #     print("\nUsage stats:")
    #     for name, date, t, t_type in rows:
    #         print(f"{date=} {name=}: {t:.1f} {t_type}")
    
    def close(self):
        self.conn.close()


class AppUsageTracker:
    def __init__(self, db: AppUsageDB):
        self.db = db
        self.active_app = None
        self.last_switch_time = time.time()

    def get_active_app(self) -> str:
        """Get the name of the active app."""
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            process = psutil.Process(pid)
            name = process.name().replace(".exe", "").title()
            return name
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            return "Unknown"

    def update_usage(self):
        """Update time for the current active app."""
        current_app = self.get_active_app()
        now = time.time()
        if self.active_app:
            elapsed = now - self.last_switch_time
            self.db.update_app_time(self.active_app, elapsed)
        self.active_app = current_app
        self.last_switch_time = now
