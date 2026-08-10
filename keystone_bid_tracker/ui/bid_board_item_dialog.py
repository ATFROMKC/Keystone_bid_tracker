"""
Keystone Bid Tracker - Bid Board Item Dialog
Add / edit a Bid Board (Calendar) item. A board item is NOT a normal bid; it
only becomes one through the Complete Bid workflow (handled by the caller).

Outcomes (self.outcome) let the caller know what the user chose:
  - "save"           : save field edits (add or update)
  - "complete"       : user clicked Complete Bid (caller opens the Add Bid workflow)
  - "mark_complete"  : COMPLETE without creating a bid
  - "link_existing"  : attach an existing BidTracker bid
  - "not_bidding"    : mark this item NOT_BIDDING
  - "in_progress"    : revert this item to IN_PROGRESS
result_data holds the collected field values (valid for save/complete).
Call apply_side_effects(item_id) after the item exists to persist recipients
and attachments.
"""

import os
import shutil
import struct
import tempfile
from urllib.parse import unquote

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QDateEdit,
    QTimeEdit, QTextEdit, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QInputDialog, QCheckBox, QComboBox, QAbstractItemView,
    QScrollArea, QWidget, QFrame, QFileDialog, QSizePolicy, QTabWidget,
    QAbstractSpinBox, QTabBar,
)
from PyQt5.QtCore import Qt, QDate, QTime, QUrl, QEvent, pyqtSignal
from PyQt5.QtGui import QDesktopServices, QColor, QIcon, QPixmap, QPainter

from config import get_bid_board_files_path, get_estimator_color, UNASSIGNED_GRAY

UNASSIGNED_LABEL = "Unassigned"

_COMPACT_DT_STYLE = """
    QDateEdit, QTimeEdit {
        padding: 4px 8px;
        min-height: 22px;
        font-size: 13px;
    }
    QDateEdit::drop-down { width: 20px; }
    QTimeEdit::up-button, QTimeEdit::down-button { width: 16px; }
"""

_CHIP_BTN_STYLE = """
    QPushButton {
        padding: 4px 12px;
        min-height: 26px;
        min-width: 72px;
        font-size: 13px;
    }
"""

_TAB_WIDGET_STYLE = """
    QTabWidget::pane {
        top: 0px;
        border-top: 1px solid #3a3a3a;
    }
    QTabBar::tab {
        background-color: #1a1a1a;
        color: #999999;
        padding: 12px 18px 14px 18px;
        margin-right: 0px;
        border: none;
        border-right: 1px solid #3a3a3a;
        border-bottom: 2px solid transparent;
        font-weight: 500;
        font-size: 13px;
        min-width: 0px;
        min-height: 22px;
    }
    QTabBar::tab:selected {
        color: #4a9eff;
        border-bottom: 2px solid #4a9eff;
    }
    QTabBar::tab:hover:!selected {
        color: #f0f0f0;
        border-bottom: 2px solid #3a3a3a;
    }
"""


class FullTextTabBar(QTabBar):
    """Size tabs so labels are not clipped horizontally or vertically."""

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        fm = self.fontMetrics()
        text = self.tabText(index)
        text_w = fm.horizontalAdvance(text) if hasattr(fm, "horizontalAdvance") else fm.width(text)
        size.setWidth(max(size.width(), text_w + 40))
        size.setHeight(max(size.height(), fm.height() + fm.descent() + 20))
        return size


def _fg_for(bg_hex):
    c = QColor(bg_hex)
    lum = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255.0
    return "#1a1a1a" if lum > 0.6 else "#ffffff"


def _swatch_icon(hex_color, size=14):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(hex_color))
    painter.setPen(QColor("#1a1a1a"))
    painter.drawRoundedRect(0, 0, size - 1, size - 1, 3, 3)
    painter.end()
    return QIcon(pm)


def _coerce_fs_path(path):
    if not path:
        return ""
    if isinstance(path, bytes):
        path = path.decode("utf-8", errors="ignore")
    path = path.strip().strip("\x00").strip().strip('"')
    if not path:
        return ""
    path = unquote(path)
    if path.lower().startswith("file:"):
        local = QUrl(path).toLocalFile()
        path = local or path
        if path.lower().startswith("file:"):
            rest = path.split(":", 1)[1]
            path = rest[3:] if rest.startswith("///") else rest.lstrip("/")
    path = path.replace("/", os.sep)
    if len(path) >= 3 and path[0] in "\\/" and path[2] == ":":
        path = path[1:]
    return os.path.normpath(path)


def _add_fs_path(paths, path):
    path = _coerce_fs_path(path)
    if not path:
        return
    if os.path.isfile(path):
        if path not in paths:
            paths.append(path)
        return
    if os.path.isdir(path):
        try:
            for name in os.listdir(path):
                fp = os.path.join(path, name)
                if os.path.isfile(fp) and fp not in paths:
                    paths.append(fp)
        except OSError:
            pass


def _paths_from_hdrop(raw):
    if not raw or len(raw) < 20:
        return []
    try:
        offset = struct.unpack_from("<I", raw, 0)[0]
        fwide = struct.unpack_from("<I", raw, 16)[0]
        blob = raw[offset:]
        text = blob.decode("utf-16-le" if fwide else "mbcs", errors="ignore")
        return [p for p in text.split("\x00") if p]
    except Exception:
        return []


def _filename_from_descriptorw(raw):
    if not raw or len(raw) < 80:
        return ""
    try:
        if struct.unpack_from("<I", raw, 0)[0] < 1:
            return ""
        chunk = raw[76:76 + 520]
        return chunk.decode("utf-16-le", errors="ignore").split("\x00")[0].strip()
    except Exception:
        return ""


def _safe_drop_name(name):
    name = os.path.basename(name or "").strip() or "dropped.bin"
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, "_")
    return name


def _local_file_paths(mime):
    """Resolve Explorer / Outlook drops to real filesystem paths."""
    paths = []
    if mime.hasUrls():
        for url in mime.urls():
            _add_fs_path(paths, url.toLocalFile() or url.toString())
    if mime.hasText():
        for line in mime.text().splitlines():
            _add_fs_path(paths, line)

    for fmt in list(mime.formats() or []):
        low = fmt.lower()
        try:
            raw = bytes(mime.data(fmt) or b"")
        except Exception:
            continue
        if not raw:
            continue
        if "hdrop" in low:
            for p in _paths_from_hdrop(raw):
                _add_fs_path(paths, p)
        elif "filenamew" in low:
            _add_fs_path(paths, raw.decode("utf-16-le", errors="ignore"))
        elif "filename" in low and "filegroup" not in low:
            _add_fs_path(paths, raw.decode("mbcs", errors="ignore"))
        elif "uri-list" in low:
            text = raw.decode("utf-8", errors="ignore")
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    _add_fs_path(paths, line)

    if paths:
        return paths

    desc_raw = b""
    contents = b""
    for fmt in list(mime.formats() or []):
        low = fmt.lower()
        try:
            raw = bytes(mime.data(fmt) or b"")
        except Exception:
            continue
        if "filegroupdescriptorw" in low and raw:
            desc_raw = raw
        elif "filecontents" in low and raw:
            contents = raw
    if contents:
        name = _safe_drop_name(_filename_from_descriptorw(desc_raw) or "dropped.bin")
        dest_dir = os.path.join(tempfile.gettempdir(), "kbt_drops")
        try:
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, name)
            stem, ext = os.path.splitext(name)
            n = 1
            while os.path.exists(dest):
                dest = os.path.join(dest_dir, f"{stem}_{n}{ext}")
                n += 1
            with open(dest, "wb") as fh:
                fh.write(contents)
            if os.path.isfile(dest) and os.path.getsize(dest) > 0:
                paths.append(dest)
        except OSError:
            pass
    return paths


def _mime_looks_like_files(mime):
    if mime.hasUrls() or mime.hasFormat("text/uri-list"):
        return True
    for fmt in mime.formats() or []:
        low = fmt.lower()
        if any(k in low for k in ("filename", "filegroupdescriptor", "filecontents", "hdrop", "uri-list")):
            return True
    return False


def _accept_copy_drag(event):
    event.setDropAction(Qt.CopyAction)
    event.accept()


class DropZoneFrame(QFrame):
    """Always-visible drop target for bid invite files."""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setObjectName("dropZone")
        self.setStyleSheet(
            "QFrame#dropZone {"
            "  background-color: #222222;"
            "  border: 2px dashed #6a6a6a;"
            "  border-radius: 8px;"
            "}"
            "QFrame#dropZone[dragHover=\"true\"] {"
            "  border-color: #4a9eff;"
            "  background-color: #1e3a5a;"
            "}"
        )
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        self.label = QLabel("Drop PDF, .msg, or files here")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setObjectName("secondaryLabel")
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        lay.addWidget(self.label)

    def _set_hover(self, on):
        self.setProperty("dragHover", "true" if on else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def dragEnterEvent(self, event):
        if _mime_looks_like_files(event.mimeData()):
            self._set_hover(True)
            _accept_copy_drag(event)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if _mime_looks_like_files(event.mimeData()):
            _accept_copy_drag(event)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_hover(False)
        event.accept()

    def dropEvent(self, event):
        self._set_hover(False)
        _accept_copy_drag(event)
        self.files_dropped.emit(_local_file_paths(event.mimeData()))


class BidBoardItemDialog(QDialog):
    """Dialog for adding or editing a Bid Board item."""

    def __init__(self, db, parent=None, item_data=None):
        super().__init__(parent)
        self.db = db
        self.item_data = item_data
        self.result_data = None
        self.outcome = None
        self._board_touched = False
        self._selected_contact_ids = set()
        self._pending_files = []
        self._pending_links = []
        self._deleted_attachment_ids = set()
        self._existing_attachments = []
        self.pending_open_bid_id = None

        self.editing = item_data is not None
        if self.editing:
            try:
                self._selected_contact_ids = {
                    c["id"] for c in self.db.get_board_item_contacts(item_data["id"])
                }
                self._existing_attachments = list(self.db.get_board_attachments(item_data["id"]))
            except Exception:
                pass

        self.setWindowTitle("Edit Bid Board Item" if self.editing else "Add to Bid Board")
        self.setMinimumSize(820, 660)
        self.setModal(True)
        self.setAcceptDrops(True)
        self._estimator_colors = {}

        self._build_ui()
        if self.editing:
            self._populate(item_data)
        else:
            self._update_summaries()
            self._sync_title()
            self._apply_estimator_combo_color()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 12)
        outer.setSpacing(10)

        self.title_label = QLabel("Add to Bid Board")
        self.title_label.setObjectName("headingLabel")
        self.title_label.setWordWrap(True)
        outer.addWidget(self.title_label)

        status_txt = (self.item_data or {}).get("board_status", "IN_PROGRESS")
        if self.editing:
            self.status_label = QLabel(self._status_caption(status_txt))
            self.status_label.setObjectName("secondaryLabel")
            outer.addWidget(self.status_label)

        self.tabs = QTabWidget()
        bar = FullTextTabBar()
        bar.setExpanding(False)
        bar.setElideMode(Qt.ElideNone)
        bar.setUsesScrollButtons(False)
        self.tabs.setTabBar(bar)
        self.tabs.setStyleSheet(_TAB_WIDGET_STYLE)
        self.tabs.addTab(self._build_details_tab(), "Details")
        self.tabs.addTab(self._build_recipients_tab(), "Who receives this bid")
        self.tabs.addTab(self._build_attachments_tab(), "Attachments")
        bar.setMinimumHeight(bar.tabSizeHint(0).height())
        outer.addWidget(self.tabs, 1)
        self._install_drop_filters()

        self._load_customers()
        self._rebuild_attachments()

        btn_row = QHBoxLayout()
        if self.editing:
            if status_txt == "NOT_BIDDING":
                self.toggle_status_btn = QPushButton("Mark In Progress")
                self.toggle_status_btn.clicked.connect(lambda: self._finish("in_progress"))
            elif status_txt == "IN_PROGRESS":
                self.toggle_status_btn = QPushButton("Mark Not Bidding")
                self.toggle_status_btn.setObjectName("dangerButton")
                self.toggle_status_btn.clicked.connect(lambda: self._finish("not_bidding"))
            elif status_txt == "COMPLETE":
                self.toggle_status_btn = QPushButton("Mark In Progress")
                self.toggle_status_btn.clicked.connect(lambda: self._finish("in_progress"))
            else:
                self.toggle_status_btn = None
            if self.toggle_status_btn is not None:
                btn_row.addWidget(self.toggle_status_btn)

            link_btn = QPushButton("Link Existing Bid")
            link_btn.setToolTip("Attach a bid already in Bid Tracker (no new bid is created).")
            link_btn.clicked.connect(lambda: self._finish("link_existing"))
            btn_row.addWidget(link_btn)

            if status_txt == "COMPLETE":
                log_btn = QPushButton("Log Another Bid")
                log_btn.setObjectName("successButton")
                log_btn.setToolTip("Create another normal BidTracker bid for this opportunity.")
                log_btn.clicked.connect(lambda: self._finish("complete"))
                btn_row.addWidget(log_btn)
            elif status_txt != "NOT_BIDDING":
                mark_btn = QPushButton("Mark Complete")
                mark_btn.setToolTip("Turn this card blue without logging a new bid.")
                mark_btn.clicked.connect(lambda: self._finish("mark_complete"))
                btn_row.addWidget(mark_btn)
                complete_btn = QPushButton("Complete Bid")
                complete_btn.setObjectName("successButton")
                complete_btn.setToolTip(
                    "Log one or more normal BidTracker bids from this opportunity."
                )
                complete_btn.clicked.connect(lambda: self._finish("complete"))
                btn_row.addWidget(complete_btn)

        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(lambda: self._finish("save"))
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

    def _build_details_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter bid name...")
        self.name_input.textChanged.connect(self._sync_title)
        form.addRow("Bid Name *", self.name_input)

        self.board_date_input = QDateEdit()
        self.board_date_input.setCalendarPopup(True)
        self.board_date_input.setDisplayFormat("MM/dd/yyyy")
        self.board_date_input.setDate(QDate.currentDate())
        self.board_date_input.dateChanged.connect(lambda _: setattr(self, "_board_touched", True))
        form.addRow("Board Date *", self.board_date_input)

        due_row = QHBoxLayout()
        self.due_date_check = QCheckBox("Has due date")
        self.due_date_check.setChecked(True)
        self.due_date_check.toggled.connect(self._on_due_toggled)
        due_row.addWidget(self.due_date_check)
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDisplayFormat("MM/dd/yyyy")
        self.due_date_input.setDate(QDate.currentDate())
        self.due_date_input.dateChanged.connect(self._on_due_date_changed)
        self.due_date_input.setStyleSheet(_COMPACT_DT_STYLE)
        self.due_date_input.setMinimumWidth(158)
        self.due_date_input.setMaximumWidth(180)
        due_row.addWidget(self.due_date_input)

        self.due_time_check = QCheckBox("Time")
        self.due_time_check.setChecked(False)
        self.due_time_check.toggled.connect(self._on_due_time_toggled)
        due_row.addWidget(self.due_time_check)
        self.due_time_input = QTimeEdit()
        self.due_time_input.setDisplayFormat("h:mm AP")
        self.due_time_input.setTime(QTime(14, 0))
        self.due_time_input.setEnabled(False)
        self.due_time_input.setStyleSheet(_COMPACT_DT_STYLE)
        self.due_time_input.setMinimumWidth(118)
        self.due_time_input.setMaximumWidth(132)
        due_row.addWidget(self.due_time_input)
        due_row.addStretch()
        form.addRow("Actual Due Date", due_row)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("City, ST  (optional — shown on calendar if entered)")
        form.addRow("Location", self.location_input)

        self.estimator_input = QComboBox()
        self.estimator_input.setObjectName("estimatorCombo")
        self.estimator_input.setEditable(True)
        self.estimator_input.setInsertPolicy(QComboBox.NoInsert)
        self._load_estimators()
        self.estimator_input.currentTextChanged.connect(self._apply_estimator_combo_color)
        form.addRow("Estimator", self.estimator_input)

        for _w in (self.name_input, self.location_input, self.estimator_input):
            _w.setAcceptDrops(False)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Optional notes...")
        self.notes_input.setMaximumHeight(90)
        self.notes_input.setAcceptDrops(False)
        form.addRow("Notes", self.notes_input)
        layout.addLayout(form)

        summary_label = QLabel("This bid")
        summary_label.setObjectName("subheadingLabel")
        layout.addWidget(summary_label)

        self.summary_recipients_btn = QPushButton("No recipients selected yet")
        self.summary_recipients_btn.setFlat(True)
        self.summary_recipients_btn.setStyleSheet("text-align: left; padding: 6px 2px;")
        self.summary_recipients_btn.setCursor(Qt.PointingHandCursor)
        self.summary_recipients_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        layout.addWidget(self.summary_recipients_btn)

        self.summary_attachments_btn = QPushButton("No attachments yet")
        self.summary_attachments_btn.setFlat(True)
        self.summary_attachments_btn.setStyleSheet("text-align: left; padding: 6px 2px;")
        self.summary_attachments_btn.setCursor(Qt.PointingHandCursor)
        self.summary_attachments_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        layout.addWidget(self.summary_attachments_btn)

        self.outlook_notes_label = QLabel("Outlook notes")
        self.outlook_notes_label.setObjectName("subheadingLabel")
        layout.addWidget(self.outlook_notes_label)
        self.outlook_notes_view = QTextEdit()
        self.outlook_notes_view.setReadOnly(True)
        self.outlook_notes_view.setMaximumHeight(70)
        self.outlook_notes_view.setAcceptDrops(False)
        layout.addWidget(self.outlook_notes_view)
        self.outlook_notes_label.hide()
        self.outlook_notes_view.hide()

        self.linked_bids_label = QLabel("Linked Bids")
        self.linked_bids_label.setObjectName("subheadingLabel")
        layout.addWidget(self.linked_bids_label)
        self.linked_bids_host = QWidget()
        self.linked_bids_box = QVBoxLayout(self.linked_bids_host)
        self.linked_bids_box.setContentsMargins(0, 0, 0, 0)
        self.linked_bids_box.setSpacing(6)
        layout.addWidget(self.linked_bids_host)
        self._rebuild_linked_bids()

        layout.addStretch()
        return page

    def _build_recipients_tab(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left = QVBoxLayout()
        cust_header = QHBoxLayout()
        cust_label = QLabel("Accounts")
        cust_label.setObjectName("subheadingLabel")
        cust_header.addWidget(cust_label)
        cust_header.addStretch()
        add_cust_btn = QPushButton("+ New Account")
        add_cust_btn.setFixedHeight(28)
        add_cust_btn.clicked.connect(self._on_add_customer)
        cust_header.addWidget(add_cust_btn)
        left.addLayout(cust_header)

        self.cust_search = QLineEdit()
        self.cust_search.setPlaceholderText("Search accounts...")
        self.cust_search.textChanged.connect(self._filter_customers)
        left.addWidget(self.cust_search)

        self.cust_list = QListWidget()
        self.cust_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.cust_list.setMinimumWidth(220)
        self.cust_list.itemChanged.connect(self._on_account_check_changed)
        left.addWidget(self.cust_list, 1)
        layout.addLayout(left, 1)

        right = QVBoxLayout()
        rec_label = QLabel("Recipient emails")
        rec_label.setObjectName("subheadingLabel")
        right.addWidget(rec_label)
        rec_hint = QLabel(
            "Check the accounts on the left, then check the emails this invite "
            "should go to. Add an email to reuse it on future bids."
        )
        rec_hint.setObjectName("secondaryLabel")
        rec_hint.setWordWrap(True)
        right.addWidget(rec_hint)

        rec_scroll = QScrollArea()
        rec_scroll.setWidgetResizable(True)
        rec_scroll.setFrameShape(QFrame.NoFrame)
        self.recipients_host = QWidget()
        self.recipients_box = QVBoxLayout(self.recipients_host)
        self.recipients_box.setContentsMargins(0, 0, 0, 4)
        self.recipients_box.setSpacing(6)
        rec_scroll.setWidget(self.recipients_host)
        right.addWidget(rec_scroll, 1)
        layout.addLayout(right, 2)
        return page

    def _build_attachments_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        att_label = QLabel("Attachments & Links")
        att_label.setObjectName("subheadingLabel")
        layout.addWidget(att_label)
        att_hint = QLabel(
            "Attach plans PDFs or a saved Outlook email (.msg), or paste a plans "
            "download link. To save an Outlook email: drag it from Outlook to a "
            "folder (or File > Save As .msg), then drop it here."
        )
        att_hint.setObjectName("secondaryLabel")
        att_hint.setWordWrap(True)
        layout.addWidget(att_hint)

        self.drop_zone = DropZoneFrame()
        self.drop_zone.files_dropped.connect(self._handle_drop_paths)
        layout.addWidget(self.drop_zone)

        att_btns = QHBoxLayout()
        add_file_btn = QPushButton("Add File...")
        add_file_btn.clicked.connect(self._on_add_file)
        att_btns.addWidget(add_file_btn)
        add_link_btn = QPushButton("Add Link...")
        add_link_btn.clicked.connect(self._on_add_link)
        att_btns.addWidget(add_link_btn)
        att_btns.addStretch()
        layout.addLayout(att_btns)

        att_scroll = QScrollArea()
        att_scroll.setWidgetResizable(True)
        att_scroll.setFrameShape(QFrame.NoFrame)
        att_scroll.setMinimumHeight(120)
        self.attachments_host = QWidget()
        self.attachments_box = QVBoxLayout(self.attachments_host)
        self.attachments_box.setContentsMargins(0, 0, 0, 4)
        self.attachments_box.setSpacing(4)
        att_scroll.setWidget(self.attachments_host)
        layout.addWidget(att_scroll, 1)
        return page

    def _status_caption(self, status):
        return {
            "IN_PROGRESS": "Status: In Progress",
            "COMPLETE": "Status: Complete (linked to a saved bid)",
            "NOT_BIDDING": "Status: Not Bidding",
        }.get(status, f"Status: {status}")

    def _clear_box(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                w.deleteLater()
            elif item.layout() is not None:
                self._clear_box(item.layout())

    def _update_summaries(self):
        if not hasattr(self, "summary_recipients_btn"):
            return
        selected_ids = self._get_selected_customer_ids()
        parts = []
        for cid in selected_ids:
            company = None
            for i in range(self.cust_list.count()):
                item = self.cust_list.item(i)
                if item.data(Qt.UserRole) == cid:
                    company = item.text()
                    break
            contacts = self.db.get_customer_contacts(cid, active_only=True)
            emails = []
            for c in contacts:
                if c["id"] in self._selected_contact_ids:
                    emails.append(c.get("email") or "")
            if company and emails:
                parts.append(f"{company} ({', '.join(e for e in emails if e)})")
            elif company:
                parts.append(f"{company} (no emails checked)")
        if parts:
            self.summary_recipients_btn.setText("Receiving: " + "; ".join(parts))
        else:
            self.summary_recipients_btn.setText("No recipients selected yet  —  click to choose accounts & emails")

        n = self._attachment_count()
        if n:
            self.summary_attachments_btn.setText(
                f"{n} attachment{'s' if n != 1 else ''}  —  click to view"
            )
        else:
            self.summary_attachments_btn.setText("No attachments yet  —  click to add files or links")

    def _attachment_count(self):
        existing = sum(1 for a in self._existing_attachments if a["id"] not in self._deleted_attachment_ids)
        return existing + len(self._pending_files) + len(self._pending_links)

    def _rebuild_linked_bids(self):
        if not hasattr(self, "linked_bids_box"):
            return
        self._clear_box(self.linked_bids_box)
        if not self.editing or not self.item_data:
            self.linked_bids_label.hide()
            self.linked_bids_host.hide()
            return
        try:
            bids = self.db.get_board_item_bids(self.item_data["id"])
        except Exception:
            bids = []
        if not bids:
            self.linked_bids_label.hide()
            self.linked_bids_host.hide()
            return
        self.linked_bids_label.setText(f"Linked Bids ({len(bids)})")
        self.linked_bids_label.show()
        self.linked_bids_host.show()
        for b in bids:
            row = QWidget()
            lay = QHBoxLayout(row)
            lay.setContentsMargins(0, 0, 0, 0)
            total = b.get("bid_total") or 0
            name = b.get("bid_name") or f"Bid #{b.get('id')}"
            lbl = QLabel(f"{name}\n${total:,.0f}")
            lbl.setWordWrap(True)
            lay.addWidget(lbl, 1)
            open_btn = QPushButton("Open Bid")
            open_btn.setStyleSheet(_CHIP_BTN_STYLE)
            open_btn.clicked.connect(lambda _, bid_id=b["id"]: self._open_linked_bid(bid_id))
            lay.addWidget(open_btn)
            unlink_btn = QPushButton("Unlink")
            unlink_btn.setStyleSheet(_CHIP_BTN_STYLE)
            unlink_btn.clicked.connect(lambda _, bid_id=b["id"]: self._unlink_linked_bid(bid_id))
            lay.addWidget(unlink_btn)
            self.linked_bids_box.addWidget(row)

    def _open_linked_bid(self, bid_id):
        self.pending_open_bid_id = bid_id
        self.reject()

    def _unlink_linked_bid(self, bid_id):
        item_id = (self.item_data or {}).get("id")
        if not item_id:
            return
        reply = QMessageBox.question(
            self, "Unlink bid",
            "Remove this Bid Tracker bid from the board card?\n"
            "The bid itself stays in Bids — only the link is removed.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.db.unlink_board_item_bid(item_id, bid_id)
        except Exception as e:
            QMessageBox.warning(self, "Unlink failed", str(e))
            return
        self._rebuild_linked_bids()

    # ------------------------------------------------------------------
    # Field helpers
    # ------------------------------------------------------------------
    def _on_due_toggled(self, on):
        self.due_date_input.setEnabled(on)
        self.due_time_check.setEnabled(on)
        if not on:
            self.due_time_check.setChecked(False)
        self.due_time_input.setEnabled(on and self.due_time_check.isChecked())

    def _on_due_time_toggled(self, on):
        self.due_time_input.setEnabled(on and self.due_date_check.isChecked())

    def _on_due_date_changed(self, qdate):
        if not self.editing and not self._board_touched:
            self.board_date_input.blockSignals(True)
            self.board_date_input.setDate(qdate)
            self.board_date_input.blockSignals(False)

    def _sync_title(self, _text=None):
        name = self.name_input.text().strip()
        if not name and self.editing:
            name = ((self.item_data or {}).get("bid_name") or "").strip()
        if name:
            self.title_label.setText(name)
            self.setWindowTitle(name)
        else:
            fallback = "Add to Bid Board"
            self.title_label.setText(fallback)
            self.setWindowTitle(fallback)

    def _estimator_color_for(self, name):
        name = (name or "").strip()
        if not name or name == UNASSIGNED_LABEL:
            return UNASSIGNED_GRAY
        return self._estimator_colors.get(name) or get_estimator_color(name)

    def _apply_estimator_combo_color(self, _text=None):
        if not hasattr(self, "estimator_input"):
            return
        bg = self._estimator_color_for(self.estimator_input.currentText())
        fg = _fg_for(bg)
        self.estimator_input.setStyleSheet(
            f"QComboBox#estimatorCombo {{"
            f"  background-color: {bg}; color: {fg};"
            f"  border: 1px solid #3a3a3a; border-radius: 6px;"
            f"  padding: 8px 12px; min-height: 16px;"
            f"}}"
            f"QComboBox#estimatorCombo QLineEdit {{"
            f"  background-color: {bg}; color: {fg}; border: none; padding: 0px;"
            f"}}"
            f"QComboBox#estimatorCombo::drop-down {{ border: none; width: 30px; }}"
        )
        line = self.estimator_input.lineEdit()
        if line is not None:
            line.setStyleSheet(f"background-color: {bg}; color: {fg}; border: none;")

    def _load_estimators(self):
        self.estimator_input.clear()
        try:
            self._estimator_colors = dict(self.db.get_estimator_color_map() or {})
        except Exception:
            self._estimator_colors = {}
        self.estimator_input.addItem(_swatch_icon(UNASSIGNED_GRAY), UNASSIGNED_LABEL)
        try:
            names = self.db.get_all_estimator_names()
        except Exception:
            names = list(self.db.get_estimators())
        for name in names:
            if name:
                self.estimator_input.addItem(_swatch_icon(self._estimator_color_for(name)), name)
        self.estimator_input.setCurrentIndex(0)
        self._apply_estimator_combo_color()

    def _load_customers(self, select_ids=None):
        self.cust_list.blockSignals(True)
        self.cust_list.clear()
        customers = self.db.get_customers(active_only=True)
        if self.editing and select_ids:
            existing_ids = {c["id"] for c in customers}
            for lc in self.db.get_board_item_customers(self.item_data["id"]):
                if lc["id"] not in existing_ids:
                    customers.append(lc)
        for c in customers:
            item = QListWidgetItem(c["name"])
            item.setData(Qt.UserRole, c["id"])
            item.setFlags((item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsSelectable)
            item.setCheckState(Qt.Checked if select_ids and c["id"] in select_ids else Qt.Unchecked)
            self.cust_list.addItem(item)
        self.cust_list.blockSignals(False)
        self._filter_customers(self.cust_search.text().strip())
        self._rebuild_recipients()

    def _filter_customers(self, text):
        for i in range(self.cust_list.count()):
            item = self.cust_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _on_add_customer(self):
        name, ok = QInputDialog.getText(self, "Add Account", "Account name:")
        if ok and name.strip():
            existing = self.db.get_customer_by_name(name.strip())
            if existing:
                for i in range(self.cust_list.count()):
                    item = self.cust_list.item(i)
                    if item.data(Qt.UserRole) == existing["id"]:
                        item.setCheckState(Qt.Checked)
                        break
                return
            cid = self.db.add_customer(name.strip())
            selected = self._get_selected_customer_ids()
            selected.add(cid)
            self._load_customers(select_ids=selected)

    def _get_selected_customer_ids(self):
        ids = set()
        if not hasattr(self, "cust_list"):
            return ids
        for i in range(self.cust_list.count()):
            item = self.cust_list.item(i)
            if item.checkState() == Qt.Checked:
                ids.add(item.data(Qt.UserRole))
        return ids

    def _on_account_check_changed(self, _item):
        self._rebuild_recipients()

    # ------------------------------------------------------------------
    # Recipients
    # ------------------------------------------------------------------
    def _rebuild_recipients(self):
        if not hasattr(self, "recipients_box"):
            return
        self._clear_box(self.recipients_box)
        selected_ids = self._get_selected_customer_ids()
        if not selected_ids:
            hint = QLabel("Select one or more accounts on the left to choose recipient emails.")
            hint.setObjectName("secondaryLabel")
            hint.setWordWrap(True)
            self.recipients_box.addWidget(hint)
            self.recipients_box.addStretch()
            self._update_summaries()
            return

        customers = {c["id"]: c for c in self.db.get_customers()}
        if self.editing:
            for lc in self.db.get_board_item_customers(self.item_data["id"]):
                customers.setdefault(lc["id"], lc)

        for cid in sorted(selected_ids, key=lambda i: (customers.get(i, {}).get("name") or "").lower()):
            company = customers.get(cid, {})
            company_name = company.get("name") or f"Account {cid}"
            block = QFrame()
            block.setObjectName("card")
            block_lay = QVBoxLayout(block)
            block_lay.setContentsMargins(10, 8, 10, 8)
            block_lay.setSpacing(4)

            header = QHBoxLayout()
            hl = QLabel(company_name)
            hl.setStyleSheet("font-weight: 600;")
            header.addWidget(hl)
            header.addStretch()
            add_btn = QPushButton("+ Add email")
            add_btn.setFixedHeight(26)
            add_btn.clicked.connect(lambda _, i=cid, n=company_name: self._on_add_email_for_account(i, n))
            header.addWidget(add_btn)
            block_lay.addLayout(header)

            contacts = self.db.get_customer_contacts(cid, active_only=True)
            if not contacts:
                empty = QLabel("No emails yet for this account.")
                empty.setObjectName("secondaryLabel")
                block_lay.addWidget(empty)
            else:
                for contact in contacts:
                    label_txt = self._contact_label(company_name, contact)
                    cb = QCheckBox(label_txt)
                    cb.setChecked(contact["id"] in self._selected_contact_ids)
                    cb.toggled.connect(
                        lambda on, cid_=contact["id"]: self._toggle_contact(cid_, on)
                    )
                    block_lay.addWidget(cb)
            self.recipients_box.addWidget(block)

        self.recipients_box.addStretch()
        self._update_summaries()

    def _contact_label(self, company_name, contact):
        person = (contact.get("name") or "").strip()
        email = (contact.get("email") or "").strip()
        if person:
            return f"{person}  <{email}>"
        return email

    def _toggle_contact(self, contact_id, on):
        if on:
            self._selected_contact_ids.add(contact_id)
        else:
            self._selected_contact_ids.discard(contact_id)
        self._update_summaries()

    def _on_add_email_for_account(self, customer_id, company_name):
        email, ok = QInputDialog.getText(
            self, "Add email", f"Email for {company_name}:"
        )
        if not ok or not email.strip() or "@" not in email:
            if ok:
                QMessageBox.warning(self, "Invalid email", "Enter a valid email address.")
            return
        name, ok2 = QInputDialog.getText(
            self, "Contact name", "Contact name (optional):"
        )
        if not ok2:
            return
        try:
            cid = self.db.add_customer_contact(customer_id, email.strip(), name.strip())
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        self._selected_contact_ids.add(cid)
        self._rebuild_recipients()

    # ------------------------------------------------------------------
    # Attachments
    # ------------------------------------------------------------------
    def _rebuild_attachments(self):
        if not hasattr(self, "attachments_box"):
            return
        self._clear_box(self.attachments_box)
        shown = 0
        for att in self._existing_attachments:
            if att["id"] in self._deleted_attachment_ids:
                continue
            self.attachments_box.addWidget(self._attachment_row(att, existing=True))
            shown += 1
        for idx, path in enumerate(self._pending_files):
            fake = {"kind": "file", "label": os.path.basename(path), "value": path, "_pending_file": idx}
            self.attachments_box.addWidget(self._attachment_row(fake, existing=False))
            shown += 1
        for idx, link in enumerate(self._pending_links):
            fake = {"kind": "link", "label": link.get("label") or link["value"], "value": link["value"], "_pending_link": idx}
            self.attachments_box.addWidget(self._attachment_row(fake, existing=False))
            shown += 1
        if shown == 0:
            hint = QLabel("No attachments yet. Use the drop zone above or Add File / Add Link.")
            hint.setObjectName("secondaryLabel")
            self.attachments_box.addWidget(hint)
        self.attachments_box.addStretch()
        self._update_summaries()

    def _attachment_row(self, att, existing):
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        kind = att.get("kind") or "file"
        prefix = "File" if kind == "file" else "Link"
        label = att.get("label") or att.get("value") or ""
        lbl = QLabel(f"{prefix}: {label}")
        lbl.setToolTip(att.get("value") or "")
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lay.addWidget(lbl, 1)
        open_btn = QPushButton("Open")
        open_btn.setStyleSheet(_CHIP_BTN_STYLE)
        open_btn.clicked.connect(lambda: self._open_attachment(att))
        lay.addWidget(open_btn)
        rem_btn = QPushButton("Remove")
        rem_btn.setStyleSheet(_CHIP_BTN_STYLE)
        rem_btn.clicked.connect(lambda: self._remove_attachment(att, existing))
        lay.addWidget(rem_btn)
        return row

    def _install_drop_filters(self):
        skip = (QLineEdit, QTextEdit, QComboBox, QAbstractSpinBox, QListWidget)
        for child in self.findChildren(QWidget):
            if isinstance(child, skip):
                child.setAcceptDrops(False)
                continue
            child.setAcceptDrops(True)
            child.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Drop and hasattr(event, "mimeData"):
            _accept_copy_drag(event)
            if hasattr(self, "drop_zone"):
                self.drop_zone._set_hover(False)
            self._handle_drop_paths(_local_file_paths(event.mimeData()))
            return True
        return super().eventFilter(obj, event)

    def _handle_drop_paths(self, paths):
        if paths:
            self._on_files_dropped(paths)
            return
        QMessageBox.information(
            self,
            "Couldn't attach that drop",
            "Windows didn't provide a usable file path.\n\n"
            "Use Add File..., or save an Outlook email as .msg to a folder "
            "and drop that file.",
        )

    def _on_files_dropped(self, paths):
        added = False
        for path in paths or []:
            if path and path not in self._pending_files:
                self._pending_files.append(path)
                added = True
        if added:
            self._rebuild_attachments()
            if hasattr(self, "tabs"):
                self.tabs.setCurrentIndex(2)

    def dragEnterEvent(self, event):
        if _mime_looks_like_files(event.mimeData()):
            _accept_copy_drag(event)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if _mime_looks_like_files(event.mimeData()):
            _accept_copy_drag(event)
        else:
            event.ignore()

    def dropEvent(self, event):
        _accept_copy_drag(event)
        self._handle_drop_paths(_local_file_paths(event.mimeData()))

    def _on_add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Attach files", "",
            "All files (*.*);;PDF (*.pdf);;Outlook message (*.msg);;Images (*.png *.jpg *.jpeg)",
        )
        if paths:
            self._on_files_dropped(list(paths))

    def _on_add_link(self):
        url, ok = QInputDialog.getText(self, "Add link", "Plans / download URL:")
        if not ok or not url.strip():
            return
        label, ok2 = QInputDialog.getText(self, "Link label", "Label (optional):", text=url.strip())
        if not ok2:
            return
        self._pending_links.append({"value": url.strip(), "label": (label or "").strip()})
        self._rebuild_attachments()

    def _open_attachment(self, att):
        value = att.get("value") or ""
        kind = att.get("kind") or "file"
        if kind == "link":
            QDesktopServices.openUrl(QUrl(value))
            return
        if os.path.isfile(value):
            try:
                os.startfile(value)
            except Exception as e:
                QMessageBox.warning(self, "Open failed", str(e))
        else:
            QMessageBox.warning(self, "Missing file", f"File not found:\n{value}")

    def _remove_attachment(self, att, existing):
        if existing:
            self._deleted_attachment_ids.add(att["id"])
        elif "_pending_file" in att:
            idx = att["_pending_file"]
            if 0 <= idx < len(self._pending_files):
                self._pending_files.pop(idx)
        elif "_pending_link" in att:
            idx = att["_pending_link"]
            if 0 <= idx < len(self._pending_links):
                self._pending_links.pop(idx)
        self._rebuild_attachments()

    def apply_side_effects(self, item_id):
        """Persist recipients + attachments after the board item exists."""
        self.db.set_board_item_contacts(item_id, list(self._selected_contact_ids))

        for att_id in self._deleted_attachment_ids:
            self.db.delete_board_attachment(att_id)

        dest_dir = os.path.join(get_bid_board_files_path(self.db.db_path), str(item_id))
        for src in self._pending_files:
            if not os.path.isfile(src):
                continue
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, os.path.basename(src))
            if os.path.exists(dest):
                stem, ext = os.path.splitext(os.path.basename(src))
                n = 1
                while os.path.exists(dest):
                    dest = os.path.join(dest_dir, f"{stem}_{n}{ext}")
                    n += 1
            try:
                shutil.copy2(src, dest)
            except Exception as e:
                QMessageBox.warning(self, "Copy failed", f"Could not copy {src}:\n{e}")
                continue
            self.db.add_board_attachment(item_id, "file", os.path.basename(dest), dest)

        for link in self._pending_links:
            self.db.add_board_attachment(
                item_id, "link", link.get("label") or link["value"], link["value"]
            )

        self._pending_files = []
        self._pending_links = []
        self._deleted_attachment_ids = set()

    # ------------------------------------------------------------------
    # Populate / collect
    # ------------------------------------------------------------------
    def _populate(self, data):
        self.name_input.setText(data.get("bid_name", "") or "")
        self._sync_title()

        bd = QDate.fromString(data.get("board_date", "") or "", "yyyy-MM-dd")
        if bd.isValid():
            self.board_date_input.setDate(bd)

        due = data.get("actual_due_date")
        if due:
            d = QDate.fromString(due, "yyyy-MM-dd")
            if d.isValid():
                self.due_date_check.setChecked(True)
                self.due_date_input.setDate(d)
        else:
            self.due_date_check.setChecked(False)
            self._on_due_toggled(False)

        due_time = data.get("actual_due_time")
        if due_time:
            t = QTime.fromString(due_time, "HH:mm")
            if t.isValid():
                self.due_time_check.setChecked(True)
                self.due_time_input.setTime(t)

        estimator = data.get("estimator")
        if estimator:
            idx = self.estimator_input.findText(estimator)
            if idx >= 0:
                self.estimator_input.setCurrentIndex(idx)
            else:
                self.estimator_input.setEditText(estimator)
        else:
            self.estimator_input.setCurrentIndex(0)
        self._apply_estimator_combo_color()

        self.notes_input.setPlainText(data.get("notes", "") or "")
        self.location_input.setText(data.get("location") or "")
        src_notes = (data.get("outlook_source_notes") or "").strip()
        if src_notes:
            self.outlook_notes_label.show()
            self.outlook_notes_view.show()
            self.outlook_notes_view.setPlainText(src_notes)
        else:
            self.outlook_notes_label.hide()
            self.outlook_notes_view.hide()

        linked = {c["id"] for c in self.db.get_board_item_customers(data["id"])}
        self._load_customers(select_ids=linked)
        self._board_touched = True

    def _collect(self):
        bid_name = self.name_input.text().strip()
        if not bid_name:
            QMessageBox.warning(self, "Validation Error", "Bid Name is required.")
            return None

        board_date = self.board_date_input.date().toString("yyyy-MM-dd")

        actual_due_date = None
        if self.due_date_check.isChecked():
            actual_due_date = self.due_date_input.date().toString("yyyy-MM-dd")

        actual_due_time = None
        if self.due_time_check.isChecked():
            actual_due_time = self.due_time_input.time().toString("HH:mm")

        estimator_text = self.estimator_input.currentText().strip()
        estimator = None if (not estimator_text or estimator_text == UNASSIGNED_LABEL) else estimator_text

        return {
            "bid_name": bid_name,
            "board_date": board_date,
            "actual_due_date": actual_due_date,
            "actual_due_time": actual_due_time,
            "location": self.location_input.text().strip(),
            "estimator": estimator,
            "notes": self.notes_input.toPlainText().strip(),
            "customer_ids": list(self._get_selected_customer_ids()),
        }

    def _finish(self, outcome):
        data = self._collect()
        if data is None:
            return
        self.result_data = data
        self.outcome = outcome
        self.accept()
