import sys
import random
from PyQt5.QtCore import QUrl, QTimer, Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                             QVBoxLayout, QWidget, QToolBar, QAction, QLineEdit,
                             QGraphicsProxyWidget, QSizeGrip, QMenu, QDialog, QSpinBox,
                             QLabel, QDialogButtonBox, QFormLayout)
from PyQt5.QtWebEngineWidgets import QWebEngineView


class WebPageItem(QGraphicsProxyWidget):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.refresh_interval = 0  # Default: no auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_page)

        # Create widget container
        self.container = QWidget()
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Web view setup
        self.web_view = QWebEngineView()
        self.web_view.load(QUrl(url))
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)  # Disable right-click menu

        # Add resize grips
        self.size_grips = [
            SizeGrip(self.container, Qt.BottomRightCorner),
            SizeGrip(self.container, Qt.BottomLeftCorner),
            SizeGrip(self.container, Qt.TopRightCorner),
            SizeGrip(self.container, Qt.TopLeftCorner)
        ]

        layout.addWidget(self.web_view)
        self.setWidget(self.container)
        self.setZValue(1)

        # Enable dragging
        self.setFlag(QGraphicsProxyWidget.ItemIsMovable)
        self.setFlag(QGraphicsProxyWidget.ItemIsSelectable)

    def refresh_page(self):
        self.web_view.reload()

    def set_refresh_interval(self, seconds):
        self.refresh_interval = seconds
        self.refresh_timer.stop()
        if seconds > 0:
            self.refresh_timer.start(seconds * 1000)

    def get_title(self):
        return self.web_view.title()


class SizeGrip(QSizeGrip):
    def __init__(self, parent, corner):
        super().__init__(parent)
        self.corner = corner
        self.setFixedSize(10, 10)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            parent = self.parent().parent()
            new_geom = parent.geometry()
            pos = event.globalPos()

            if self.corner == Qt.BottomRightCorner:
                new_geom.setBottomRight(pos)
            elif self.corner == Qt.BottomLeftCorner:
                new_geom.setBottomLeft(pos)
            elif self.corner == Qt.TopRightCorner:
                new_geom.setTopRight(pos)
            elif self.corner == Qt.TopLeftCorner:
                new_geom.setTopLeft(pos)

            parent.setGeometry(new_geom)


class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor(240, 240, 240))
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def add_web_page(self, url):
        page = WebPageItem(url)
        self.scene.addItem(page)
        # Random position for new page
        page.setPos(random.randint(0, int(self.width() / 2)),
                    random.randint(0, int(self.height() / 2)))
        return page


class RefreshSettingsDialog(QDialog):
    def __init__(self, current_interval, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Refresh Settings")
        layout = QFormLayout()

        self.spin_box = QSpinBox()
        self.spin_box.setRange(0, 3600)  # 0-60 minutes
        self.spin_box.setValue(current_interval)
        self.spin_box.setSuffix(" seconds")

        layout.addRow(QLabel("Refresh Interval:"), self.spin_box)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)
        self.setLayout(layout)

    def get_interval(self):
        return self.spin_box.value()


class BrowserCanvasApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Canvas Browser")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create canvas
        self.canvas = Canvas()
        layout.addWidget(self.canvas)

        # Create toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL and press Enter")
        self.url_input.returnPressed.connect(self.add_new_page)
        toolbar.addWidget(self.url_input)

        # Add page action
        add_action = QAction("Add Page", self)
        add_action.triggered.connect(self.add_new_page)
        toolbar.addAction(add_action)

        # Context menu setup
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.current_page = None

    def add_new_page(self):
        url = self.url_input.text()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        self.canvas.add_web_page(url)
        self.url_input.clear()

    def show_context_menu(self, pos):
        # Find item under cursor
        scene_pos = self.canvas.mapToScene(pos)
        item = self.canvas.scene.itemAt(scene_pos, self.canvas.transform())

        if isinstance(item, WebPageItem):
            self.current_page = item
            menu = QMenu()

            # Refresh actions
            refresh_action = menu.addAction("Refresh Now")
            refresh_action.triggered.connect(item.refresh_page)

            # Auto-refresh settings
            refresh_settings = menu.addAction("Auto-Refresh Settings...")
            refresh_settings.triggered.connect(self.show_refresh_settings)

            # Close action
            close_action = menu.addAction("Close Page")
            close_action.triggered.connect(lambda: self.canvas.scene.removeItem(item))

            menu.exec_(self.mapToGlobal(pos))

    def show_refresh_settings(self):
        if self.current_page:
            dialog = RefreshSettingsDialog(self.current_page.refresh_interval)
            if dialog.exec_() == QDialog.Accepted:
                interval = dialog.get_interval()
                self.current_page.set_refresh_interval(interval)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrowserCanvasApp()
    window.show()
    sys.exit(app.exec_())