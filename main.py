import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QLabel,
    QPushButton,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

from usage import AppUsageDB, AppUsageTracker


class UsageTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Приложение", "Время", "Единицы"])
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setShowGrid(True)
        self.verticalHeader().setVisible(False)

    def populate_today(self, rows):
        # rows: list of dicts with keys name, time, type, seconds
        self.setSortingEnabled(False)
        self.setRowCount(len(rows))
        for r, row in enumerate(rows):
            if row['type'] != 'seconds':
                self.setItem(r, 0, QTableWidgetItem(row["name"]))
                self.setItem(r, 1, QTableWidgetItem(str(round(row["time"], 3))))
                self.setItem(r, 2, QTableWidgetItem(row["type"]))
        self.setSortingEnabled(True)

    def populate_totals(self, totals_dict):
        # totals_dict: {name: {time, type}}
        items = list(totals_dict.items())
        self.setSortingEnabled(False)
        self.setRowCount(len(items))
        for r, (name, info) in enumerate(items):
            if info['type'] != 'seconds':
                self.setItem(r, 0, QTableWidgetItem(name))
                self.setItem(r, 1, QTableWidgetItem(str(round(info["time"], 2))))
                self.setItem(r, 2, QTableWidgetItem(info["type"]))
        self.setSortingEnabled(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Manager - App Usage")
        self.setMinimumSize(900, 600)
        self.setWindowIcon(QIcon())

        self.db = AppUsageDB("usage.db")
        self.tracker = AppUsageTracker(self.db)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Top bar with search and refresh
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск приложения…")
        self.refresh_btn = QPushButton("Обновить")
        self.status_label = QLabel("")
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.refresh_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.status_label)

        main_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Today tab
        self.today_tab = QWidget()
        self.today_table = UsageTable()
        today_layout = QVBoxLayout(self.today_tab)
        today_layout.setContentsMargins(0, 10, 0, 0)
        today_layout.addWidget(self.today_table)
        self.tabs.addTab(self.today_tab, "Сегодня")

        # Totals tab
        self.total_tab = QWidget()
        self.total_table = UsageTable()
        total_layout = QVBoxLayout(self.total_tab)
        total_layout.setContentsMargins(0, 10, 0, 0)
        total_layout.addWidget(self.total_table)
        self.tabs.addTab(self.total_tab, "Все время")

        # Connections
        self.refresh_btn.clicked.connect(self.refresh_tables)
        self.search_input.textChanged.connect(self.apply_filter)

        # Timer to update tracking and UI
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.on_tick)
        self.timer.start()

        self.refresh_tables()
        self.apply_modern_style()

    def on_tick(self):
        # Update usage and refresh visible tab for responsiveness
        self.tracker.update_usage()
        self.refresh_tables()

    def refresh_tables(self):
        today = self.db.fetch_today_stats()
        totals = self.db.fetch_all_time_stats()
        # Apply in-memory filter before populating
        query = self.search_input.text().strip().lower()
        if query:
            today = [r for r in today if query in r["name"].lower()]
            totals = {k: v for k, v in totals.items() if query in k.lower()}
        self.today_table.populate_today(today)
        self.total_table.populate_totals(totals)
        if today:
            self.status_label.setText(f"Активных записей сегодня: {len(today)}")
        else:
            self.status_label.setText("Нет данных за сегодня")

    def apply_filter(self):
        self.refresh_tables()

    def apply_modern_style(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #121212, stop:1 #0f0f0f);
            }
            QWidget {
                color: #ECECEC;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 24px;
            }
            QLabel {
                color: #B0B0B0;
                font-size: 12px;
            }
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #2a2a2a;
                border-radius: 10px;
                background: #1e1e1e;
                font-size: 14px;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
                background: #222222;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
            QPushButton {
                padding: 12px 20px;
                border: 2px solid #2a2a2a;
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1f1f1f, stop:1 #181818);
                color: #ECECEC;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2a2a2a, stop:1 #232323);
                border-color: #4a90e2;
            }
            QPushButton:pressed {
                background: #1a1a1a;
            }
            QTableWidget {
                gridline-color: #2a2a2a;
                background: #161616;
                alternate-background-color: #1a1a1a;
                selection-background-color: #4a90e2;
                selection-color: #ffffff;
                border: none;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #2a2a2a;
            }
            QTableWidget::item:selected {
                background: #4a90e2;
                color: #ffffff;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1f1f1f, stop:1 #181818);
                padding: 12px;
                border: none;
                border-bottom: 2px solid #2a2a2a;
                font-weight: 600;
                color: #ECECEC;
                font-size: 13px;
            }
            QHeaderView::section:hover {
                background: #2a2a2a;
            }
            QTabWidget::pane {
                border: 1px solid #2a2a2a;
                background: #161616;
                border-radius: 8px;
            }
            QTabBar::tab {
                padding: 12px 20px;
                background: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #B0B0B0;
                font-weight: 500;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #222222;
                color: #4a90e2;
                border-bottom: 2px solid #4a90e2;
            }
            QTabBar::tab:hover:!selected {
                background: #2a2a2a;
                color: #ECECEC;
            }
            """
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better modern look
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()