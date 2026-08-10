"""
Keystone Bid Tracker - Calendar / Bid Board tab (Estimator Portal)

A monthly, Outlook-style bid board using the Keystone dark UI. Bid Board items
are estimating opportunities; Complete Bid can create one or many independent
normal BidTracker bids (not revisions) linked to the same card.

Color / state matrix:
  IN_PROGRESS + unassigned  -> gray
  IN_PROGRESS + assigned    -> estimator color (shared roster)
  COMPLETE                  -> universal blue (any estimator)
  NOT_BIDDING               -> distinct treatment
Gray is derived (never stored).
"""

import calendar
from datetime import date, datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QFrame, QMenu, QMessageBox, QInputDialog, QDialog, QScrollArea,
    QSizePolicy, QCheckBox, QButtonGroup, QLineEdit, QListWidget, QListWidgetItem,
    QAbstractItemView,
)
from PyQt5.QtGui import QDrag, QColor, QFontMetrics
from PyQt5.QtCore import Qt, QMimeData, QDate, QTime, pyqtSignal, QTimer, QEvent

from config import (
    get_estimator_color, get_complete_blue, UNASSIGNED_GRAY, NOT_BIDDING_COLOR,
    get_current_estimator, set_current_estimator,
    get_calendar_view, set_calendar_view, get_hide_weekends, set_hide_weekends,
    get_outlook_sync_config,
)
from utils.outlook_sync_worker import OutlookSyncWorker
from styles.theme import COLORS
from ui.bid_board_item_dialog import BidBoardItemDialog
from ui.add_bid_dialog import AddBidDialog
from ui.link_board_bid_dialog import LinkBoardBidDialog
from ui.outlook_hint_review_dialog import OutlookHintReviewDialog

MIME_ITEM = "application/x-keystone-bidboard-item"
MAX_VISIBLE_CARDS = 6
WEEKDAYS_ALL = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ME_FILTER = "__ME__"


def item_color(item, color_map=None) -> str:
    """Resolve a card's fill color from the state matrix."""
    status = item.get("board_status", "IN_PROGRESS")
    if status == "COMPLETE":
        return get_complete_blue()
    if status == "NOT_BIDDING":
        return NOT_BIDDING_COLOR
    estimator = item.get("estimator")
    if estimator and str(estimator).strip():
        name = str(estimator).strip()
        if color_map and color_map.get(name):
            return color_map[name]
        return get_estimator_color(name)
    return UNASSIGNED_GRAY


def _text_color_for(bg_hex: str) -> str:
    c = QColor(bg_hex)
    luminance = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255.0
    return "#1a1a1a" if luminance > 0.6 else "#ffffff"


def _format_time(item) -> str:
    t = item.get("actual_due_time")
    if not t:
        return ""
    tt = QTime.fromString(t, "HH:mm")
    if not tt.isValid():
        return ""
    return tt.toString("h:mm AP").replace(" AM", "am").replace(" PM", "pm")


def _due_text(item) -> str:
    due = item.get("actual_due_date")
    if not due:
        return ""
    d = QDate.fromString(due, "yyyy-MM-dd")
    if not d.isValid():
        return ""
    return f"Due {d.toString('ddd M/d')}"


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


class BoardCard(QFrame):
    """A compact, draggable card representing one Bid Board item."""

    clicked = pyqtSignal(int)
    menu_requested = pyqtSignal(int, object)

    def __init__(self, item, color_map=None, parent=None):
        super().__init__(parent)
        self.item = item
        self.item_id = item["id"]
        self._press_pos = None
        self._dragging = False
        self._full_name = item.get("bid_name", "") or ""

        self.setObjectName("boardCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        bg = item_color(item, color_map)
        fg = _text_color_for(bg)
        status = item.get("board_status", "IN_PROGRESS")
        self.setStyleSheet(
            f"#boardCard {{ background-color: {bg}; border-radius: 4px; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 3, 6, 3)
        lay.setSpacing(0)

        prefix = "\u2713 " if status == "COMPLETE" else ""
        time_txt = _format_time(item)
        marks = ""
        if item.get("attachment_count"):
            marks += " \U0001f4ce"
        if item.get("recipient_count"):
            marks += " @"
        if (item.get("source") or "").upper() == "OUTLOOK":
            marks += " O"
        self._name_core = prefix + self._full_name + marks
        self.name_label = QLabel(self._name_core)
        name_style = f"color: {fg}; font-size: 11px; font-weight: 600; background: transparent;"
        if status == "NOT_BIDDING":
            name_style += " text-decoration: line-through;"
        self.name_label.setStyleSheet(name_style)
        lay.addWidget(self.name_label)

        estimator = item.get("estimator") or "Unassigned"
        location = (item.get("location") or "").strip()
        due = _due_text(item)
        sub_bits = []
        if location:
            sub_bits.append(location)
        sub_bits.append(estimator)
        if due and time_txt:
            sub_bits.append(f"{due} {time_txt}")
        elif due:
            sub_bits.append(due)
        elif time_txt:
            sub_bits.append(time_txt)
        self.sub_label = QLabel("  \u2022  ".join(sub_bits))
        self.sub_label.setStyleSheet(
            f"color: {fg}; font-size: 10px; background: transparent;"
        )
        lay.addWidget(self.sub_label)

        tip = self._full_name
        if time_txt:
            tip += f"\nTime: {time_txt}"
        if location:
            tip += f"\nLocation: {location}"
        if item.get("customer_names"):
            tip += f"\nAccounts: {item['customer_names']}"
        tip += f"\nEstimator: {estimator}"
        if due:
            tip += f"\n{due}"
        tip += f"\nStatus: {status}"
        if item.get("recipient_count"):
            rec_names = (item.get("customer_names") or "").strip()
            if rec_names:
                tip += f"\nRecipients: {item['recipient_count']} ({rec_names})"
            else:
                tip += f"\nRecipients: {item['recipient_count']}"
        if item.get("attachment_count"):
            tip += f"\nAttachments: {item['attachment_count']}"
        if item.get("linked_bid_count"):
            tip += f"\nLinked bids: {item['linked_bid_count']}"
        self.setToolTip(tip)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        fm = QFontMetrics(self.name_label.font())
        avail = max(20, self.width() - 16)
        elided = fm.elidedText(getattr(self, "_name_core", self._full_name), Qt.ElideRight, avail)
        self.name_label.setText(elided)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.pos()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self._press_pos is None:
            return
        from PyQt5.QtWidgets import QApplication
        if (event.pos() - self._press_pos).manhattanLength() < QApplication.startDragDistance():
            return
        self._dragging = True
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_ITEM, str(self.item_id).encode("utf-8"))
        drag.setMimeData(mime)
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.MoveAction)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self._dragging:
            self.clicked.emit(self.item_id)
        self._press_pos = None
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        self.menu_requested.emit(self.item_id, event.globalPos())


class DayCell(QFrame):
    """One day in the month/week grid. Accepts card drops."""

    def __init__(self, cell_date, in_month, controller, max_visible=MAX_VISIBLE_CARDS, parent=None):
        super().__init__(parent)
        self.cell_date = cell_date
        self.in_month = in_month
        self.controller = controller
        self.max_visible = max_visible
        self.setAcceptDrops(True)
        self.setObjectName("dayCell")

        is_today = cell_date == date.today()
        border = COLORS["accent"] if is_today else COLORS["border"]
        bg = COLORS["surface"] if in_month else COLORS["background"]
        self.setStyleSheet(
            f"#dayCell {{ background-color: {bg}; border: 1px solid {border}; "
            f"border-radius: 6px; }}"
        )

        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(4, 4, 4, 4)
        self.v.setSpacing(3)

        num_color = COLORS["text_primary"] if in_month else COLORS["muted"]
        weight = "700" if is_today else "500"
        self.num_label = QLabel(str(cell_date.day))
        self.num_label.setStyleSheet(
            f"color: {num_color}; font-size: 11px; font-weight: {weight}; background: transparent;"
        )
        self.num_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.v.addWidget(self.num_label)

    def set_items(self, items, color_map=None):
        cap = self.max_visible if self.max_visible else len(items)
        visible = items[:cap]
        for it in visible:
            card = BoardCard(it, color_map=color_map)
            card.clicked.connect(self.controller.open_item)
            card.menu_requested.connect(self.controller.show_card_menu)
            self.v.addWidget(card)
        extra = len(items) - len(visible)
        if extra > 0:
            more = QPushButton(f"+ {extra} more")
            more.setFlat(True)
            more.setCursor(Qt.PointingHandCursor)
            more.setStyleSheet(
                f"QPushButton {{ color: {COLORS['accent']}; font-size: 10px; "
                f"text-align: left; border: none; background: transparent; padding: 1px; }}"
            )
            more.clicked.connect(lambda: self.controller.show_day_popup(self.cell_date, items))
            self.v.addWidget(more)
        self.v.addStretch()

    def mouseDoubleClickEvent(self, event):
        self.controller.add_item(default_date=self.cell_date)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME_ITEM):
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet().replace(COLORS["border"], COLORS["accent"]))

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(MIME_ITEM):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        is_today = self.cell_date == date.today()
        border = COLORS["accent"] if is_today else COLORS["border"]
        bg = COLORS["surface"] if self.in_month else COLORS["background"]
        self.setStyleSheet(
            f"#dayCell {{ background-color: {bg}; border: 1px solid {border}; "
            f"border-radius: 6px; }}"
        )

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(MIME_ITEM):
            return
        raw = bytes(event.mimeData().data(MIME_ITEM)).decode("utf-8")
        try:
            item_id = int(raw)
        except ValueError:
            return
        event.acceptProposedAction()
        self.controller.move_item(item_id, self.cell_date)


class CalendarTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        today = date.today()
        self.anchor_date = today
        self.view_mode = get_calendar_view("month")
        self.hide_weekends = get_hide_weekends(False)
        self.color_map = {}
        self._outlook_syncing = False
        self._search_popup = None
        self._search_busy = False
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(280)
        self._search_timer.timeout.connect(self._refresh_search_suggestions)
        self._build_ui()
        self._rebuild()
        self._refresh_outlook_sync_label()
        self._outlook_timer = QTimer(self)
        self._outlook_timer.setInterval(30 * 60 * 1000)
        self._outlook_timer.timeout.connect(self._maybe_auto_sync)
        self._outlook_timer.start()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)

        self.prev_btn = QPushButton("\u2039")
        self.prev_btn.setFixedWidth(36)
        self.prev_btn.clicked.connect(self._prev)
        header.addWidget(self.prev_btn)

        today_btn = QPushButton("Today")
        today_btn.clicked.connect(self._go_today)
        header.addWidget(today_btn)

        self.next_btn = QPushButton("\u203a")
        self.next_btn.setFixedWidth(36)
        self.next_btn.clicked.connect(self._next)
        header.addWidget(self.next_btn)

        self.month_label = QLabel("")
        self.month_label.setObjectName("headingLabel")
        header.addWidget(self.month_label)

        header.addStretch()

        self.view_group = QButtonGroup(self)
        self.view_group.setExclusive(True)
        for mode, label in (("month", "Month"), ("3week", "3 Weeks"), ("week", "Week"), ("day", "Day")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(self.view_mode == mode)
            btn.clicked.connect(lambda _, m=mode: self._set_view(m))
            self.view_group.addButton(btn)
            header.addWidget(btn)

        self.hide_weekends_cb = QCheckBox("Hide weekends")
        self.hide_weekends_cb.setChecked(self.hide_weekends)
        self.hide_weekends_cb.toggled.connect(self._on_hide_weekends)
        header.addWidget(self.hide_weekends_cb)

        header.addWidget(QLabel("Estimator:"))
        self.estimator_combo = QComboBox()
        self.estimator_combo.setMinimumWidth(140)
        self.estimator_combo.currentIndexChanged.connect(self._rebuild)
        header.addWidget(self.estimator_combo)

        header.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("All", None)
        self.status_combo.addItem("In Progress", ["IN_PROGRESS"])
        self.status_combo.addItem("Complete", ["COMPLETE"])
        self.status_combo.addItem("Not Bidding", ["NOT_BIDDING"])
        self.status_combo.currentIndexChanged.connect(self._rebuild)
        header.addWidget(self.status_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search board…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(180)
        self.search_input.setMaximumWidth(260)
        self.search_input.setToolTip(
            "Type to find by name, account, estimator, notes, or location. "
            "Arrow keys move the list; Enter opens; Esc clears. "
            "Search opens the full results dialog."
        )
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._on_search_return)
        self.search_input.installEventFilter(self)
        header.addWidget(self.search_input)
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._run_board_search)
        header.addWidget(search_btn)

        add_btn = QPushButton("+ Add to Bid Board")
        add_btn.setObjectName("addBidButton")
        add_btn.clicked.connect(lambda: self.add_item())
        header.addWidget(add_btn)

        self.outlook_sync_btn = QPushButton("\u21bb Sync Outlook")
        self.outlook_sync_btn.setToolTip("Read-only import from the shared Outlook calendar.")
        self.outlook_sync_btn.clicked.connect(self._sync_outlook)
        header.addWidget(self.outlook_sync_btn)
        self.outlook_sync_label = QLabel("")
        self.outlook_sync_label.setObjectName("secondaryLabel")
        header.addWidget(self.outlook_sync_label)

        outer.addLayout(header)

        self.counts_label = QLabel("")
        self.counts_label.setObjectName("secondaryLabel")
        self.counts_label.setWordWrap(True)
        outer.addWidget(self.counts_label)

        # Inline suggestions (not a Qt.Popup — Popup steals focus and can freeze on Windows)
        self.search_suggest_frame = QFrame()
        self.search_suggest_frame.setObjectName("card")
        self.search_suggest_frame.setVisible(False)
        suggest_lay = QVBoxLayout(self.search_suggest_frame)
        suggest_lay.setContentsMargins(8, 6, 8, 6)
        suggest_lay.setSpacing(4)
        suggest_tip = QLabel("Matches (click or Enter to open)")
        suggest_tip.setObjectName("secondaryLabel")
        suggest_lay.addWidget(suggest_tip)
        self._search_popup = QListWidget()
        self._search_popup.setFocusPolicy(Qt.NoFocus)
        self._search_popup.setMaximumHeight(180)
        self._search_popup.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._search_popup.setSelectionMode(QAbstractItemView.SingleSelection)
        self._search_popup.setAlternatingRowColors(True)
        self._search_popup.itemClicked.connect(self._on_search_suggestion_chosen)
        suggest_lay.addWidget(self._search_popup)
        outer.addWidget(self.search_suggest_frame)

        self.weekday_host = QWidget()
        self.weekday_row = QGridLayout(self.weekday_host)
        self.weekday_row.setContentsMargins(0, 0, 0, 0)
        self.weekday_row.setSpacing(6)
        outer.addWidget(self.weekday_host)

        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(6)
        self.grid.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.grid_host)
        outer.addWidget(scroll, 1)

        self._load_estimator_filter()

    def _visible_weekdays(self):
        return WEEKDAYS_ALL[:5] if self.hide_weekends else WEEKDAYS_ALL

    def _set_equal_columns(self, layout, count, max_cols=8):
        """Give the first `count` columns equal stretch; collapse leftover weekend cols."""
        for c in range(max_cols):
            layout.setColumnStretch(c, 1 if c < count else 0)
            layout.setColumnMinimumWidth(c, 0)

    def _rebuild_weekday_header(self):
        while self.weekday_row.count():
            item = self.weekday_row.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        days = self._visible_weekdays()
        if self.view_mode == "day":
            lbl = QLabel(self.anchor_date.strftime("%A"))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: 600;"
            )
            self.weekday_row.addWidget(lbl, 0, 0)
            self._set_equal_columns(self.weekday_row, 1)
            return
        for i, wd in enumerate(days):
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: 600;"
            )
            self.weekday_row.addWidget(lbl, 0, i)
        self._set_equal_columns(self.weekday_row, len(days))

    def _load_estimator_filter(self):
        current = self.estimator_combo.currentData() if self.estimator_combo.count() else None
        self.estimator_combo.blockSignals(True)
        self.estimator_combo.clear()
        self.estimator_combo.addItem("All Estimators", None)
        self.estimator_combo.addItem("Me", ME_FILTER)
        self.estimator_combo.addItem("Unassigned", self.db.UNASSIGNED)
        try:
            names = self.db.get_all_estimator_names()
        except Exception:
            names = [x for x in self.db.get_estimators() if x]
        for n in names:
            self.estimator_combo.addItem(n, n)
        if current is not None:
            idx = self.estimator_combo.findData(current)
            if idx >= 0:
                self.estimator_combo.setCurrentIndex(idx)
        self.estimator_combo.blockSignals(False)

    # ------------------------------------------------------------------
    # Navigation / view
    # ------------------------------------------------------------------
    def _set_view(self, mode):
        self.view_mode = mode
        set_calendar_view(mode)
        self._rebuild()

    def _on_hide_weekends(self, checked):
        self.hide_weekends = bool(checked)
        set_hide_weekends(self.hide_weekends)
        if self.hide_weekends and self.anchor_date.weekday() >= 5:
            self.anchor_date = self.anchor_date - timedelta(days=self.anchor_date.weekday() - 4)
        self._rebuild()

    def _prev(self):
        if self.view_mode == "month":
            y, m = self.anchor_date.year, self.anchor_date.month - 1
            if m < 1:
                m, y = 12, y - 1
            day = min(self.anchor_date.day, calendar.monthrange(y, m)[1])
            self.anchor_date = date(y, m, day)
        elif self.view_mode in ("week", "3week"):
            self.anchor_date -= timedelta(days=7)
        else:
            self.anchor_date -= timedelta(days=1)
            if self.hide_weekends:
                while self.anchor_date.weekday() >= 5:
                    self.anchor_date -= timedelta(days=1)
        self._rebuild()

    def _next(self):
        if self.view_mode == "month":
            y, m = self.anchor_date.year, self.anchor_date.month + 1
            if m > 12:
                m, y = 1, y + 1
            day = min(self.anchor_date.day, calendar.monthrange(y, m)[1])
            self.anchor_date = date(y, m, day)
        elif self.view_mode in ("week", "3week"):
            self.anchor_date += timedelta(days=7)
        else:
            self.anchor_date += timedelta(days=1)
            if self.hide_weekends:
                while self.anchor_date.weekday() >= 5:
                    self.anchor_date += timedelta(days=1)
        self._rebuild()

    def _go_today(self):
        self.anchor_date = date.today()
        if self.hide_weekends and self.anchor_date.weekday() >= 5:
            self.anchor_date = self.anchor_date - timedelta(days=self.anchor_date.weekday() - 4)
        self._rebuild()

    # ------------------------------------------------------------------
    # Build / refresh
    # ------------------------------------------------------------------
    def refresh(self):
        self._load_estimator_filter()
        self._rebuild()
        self._refresh_outlook_sync_label()

    def showEvent(self, event):
        super().showEvent(event)
        self._maybe_auto_sync()

    def _format_last_synced(self, iso_text):
        if not iso_text:
            return "Last synced: never"
        try:
            dt = datetime.fromisoformat(iso_text)
            return "Last synced: " + dt.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            return f"Last synced: {iso_text}"

    def _refresh_outlook_sync_label(self):
        if not hasattr(self, "outlook_sync_label"):
            return
        cfg = get_outlook_sync_config()
        self.outlook_sync_label.setText(self._format_last_synced(cfg.get("last_synced_at")))

    def _maybe_auto_sync(self):
        cfg = get_outlook_sync_config()
        if not cfg.get("calendar_id"):
            return
        if (cfg.get("provider") or "desktop") == "graph" and not cfg.get("client_id"):
            return
        last = cfg.get("last_synced_at") or ""
        if last:
            try:
                prev = datetime.fromisoformat(last)
                if (datetime.now() - prev).total_seconds() < 15 * 60:
                    return
            except ValueError:
                pass
        self._sync_outlook(silent=True)

    def _sync_outlook(self, silent=False):
        if self._outlook_syncing:
            return
        cfg = get_outlook_sync_config()
        if not cfg.get("calendar_id"):
            if not silent:
                QMessageBox.information(
                    self, "Outlook sync",
                    "Set up Outlook Sync in Hub Settings first "
                    "(pick Local Outlook Desktop and the shared Commercial Bid calendar).",
                )
            return
        if (cfg.get("provider") or "desktop") == "graph" and not (
            cfg.get("client_id") and cfg.get("tenant_id")
        ):
            if not silent:
                QMessageBox.information(
                    self, "Outlook sync",
                    "Microsoft Graph sync needs tenant ID, client ID, and sign-in "
                    "in Hub Settings — or switch the source to Local Outlook Desktop.",
                )
            return
        self._outlook_syncing = True
        self.outlook_sync_btn.setEnabled(False)
        self.outlook_sync_label.setText("Syncing Outlook…")
        self._outlook_worker = OutlookSyncWorker(self.db)
        self._outlook_worker.finished.connect(
            lambda ok, msg, result: self._on_outlook_sync_done(ok, msg, result, silent)
        )
        self._outlook_worker.start()

    def _on_outlook_sync_done(self, ok, msg, result, silent):
        self._outlook_syncing = False
        self.outlook_sync_btn.setEnabled(True)
        self._refresh_outlook_sync_label()
        if not ok:
            self.outlook_sync_label.setText("Outlook sync failed")
            if not silent:
                QMessageBox.warning(self, "Outlook sync", msg)
            return

        due_applied = 0
        account_applied = 0
        if not silent and result:
            candidates = result.get("hint_candidates") or []
            if candidates:
                review = OutlookHintReviewDialog(candidates, self)
                if review.exec_() == QDialog.Accepted:
                    for row in review.accepted_applies:
                        try:
                            applied = self.db.apply_board_item_outlook_hints(
                                row["item_id"],
                                actual_due_date=row.get("actual_due_date"),
                                customer_ids=row.get("customer_ids"),
                            )
                            if applied.get("due_date"):
                                due_applied += 1
                            account_applied += int(applied.get("customers") or 0)
                        except Exception:
                            pass

        self._rebuild()
        if silent:
            return

        extra = []
        if due_applied:
            extra.append(f"{due_applied} due date(s) applied")
        if account_applied:
            extra.append(f"{account_applied} account link(s) applied")
        full_msg = msg
        if extra:
            full_msg = msg.rstrip(".") + "; " + ", ".join(extra) + "."

        body = (result or {}).get("body_stats") or {}
        filled = int(body.get("filled") or 0)
        attempted = int(body.get("attempted") or (result or {}).get("fetched") or 0)
        hints = int(
            (result or {}).get("hint_candidate_count")
            or len((result or {}).get("hint_candidates") or [])
        )
        self.outlook_sync_label.setText(
            f"Last sync · bodies {filled}/{attempted} · suggestions {hints}"
        )

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("Outlook sync")
        box.setText(full_msg)
        changes = (result or {}).get("changes") or []
        if changes:
            lines = []
            for ch in changes[:50]:
                action = "New" if ch.get("action") == "new" else "Updated"
                lines.append(
                    f"{action}: {ch.get('bid_name') or '—'}  ({ch.get('board_date') or '—'})"
                )
            box.setDetailedText("\n".join(lines))
        box.exec_()

    def eventFilter(self, obj, event):
        if obj is self.search_input and event.type() == QEvent.KeyPress:
            key = event.key()
            visible = (
                self.search_suggest_frame.isVisible()
                if hasattr(self, "search_suggest_frame")
                else False
            )
            if visible and self._search_popup and self._search_popup.count():
                if key == Qt.Key_Down:
                    row = self._search_popup.currentRow()
                    self._search_popup.setCurrentRow(
                        min(row + 1, self._search_popup.count() - 1)
                    )
                    return True
                if key == Qt.Key_Up:
                    row = self._search_popup.currentRow()
                    self._search_popup.setCurrentRow(max(row - 1, 0))
                    return True
                if key == Qt.Key_Escape:
                    self._hide_search_suggestions()
                    return True
            elif key == Qt.Key_Escape and (self.search_input.text() or "").strip():
                self.search_input.clear()
                return True
        return super().eventFilter(obj, event)

    def _on_search_text_changed(self, _text):
        if self._search_busy:
            return
        self._search_timer.start()

    def _hide_search_suggestions(self):
        if hasattr(self, "search_suggest_frame"):
            self.search_suggest_frame.setVisible(False)
        if self._search_popup:
            self._search_popup.clear()

    def _format_search_row(self, r) -> str:
        status = r.get("board_status") or ""
        est = r.get("estimator") or "Unassigned"
        loc = (r.get("location") or "").strip()
        line = f"{r.get('board_date') or '—'}  ·  {r.get('bid_name') or '—'}  ·  {est}  ·  {status}"
        if loc:
            line += f"  ·  {loc}"
        return line

    def _refresh_search_suggestions(self):
        if self._search_busy:
            return
        q = (self.search_input.text() or "").strip()
        if len(q) < 2:
            self._hide_search_suggestions()
            return
        self._search_busy = True
        try:
            rows = self.db.search_board_items(q, limit=12, quick=True)
        except Exception:
            rows = []
        finally:
            self._search_busy = False
        if (self.search_input.text() or "").strip() != q:
            # Text changed while we searched — let the timer catch up
            self._search_timer.start()
            return
        if not rows:
            self._hide_search_suggestions()
            return
        self._search_popup.clear()
        for r in rows:
            item = QListWidgetItem(self._format_search_row(r))
            item.setData(Qt.UserRole, r)
            self._search_popup.addItem(item)
        self._search_popup.setCurrentRow(0)
        self.search_suggest_frame.setVisible(True)

    def _on_search_suggestion_chosen(self, item):
        row = (item.data(Qt.UserRole) if item else None) or {}
        self._hide_search_suggestions()
        self._open_board_search_hit(row)

    def _on_search_return(self):
        if (
            hasattr(self, "search_suggest_frame")
            and self.search_suggest_frame.isVisible()
            and self._search_popup
            and self._search_popup.count()
        ):
            item = self._search_popup.currentItem() or self._search_popup.item(0)
            if item:
                self._on_search_suggestion_chosen(item)
                return
        self._run_board_search()

    def _open_board_search_hit(self, row):
        if not row:
            return
        item_id = row.get("id")
        board_date = (row.get("board_date") or "")[:10]
        if board_date:
            try:
                self.anchor_date = date.fromisoformat(board_date)
            except ValueError:
                pass
            self._rebuild()
        if item_id:
            # Defer dialog so the calendar paint finishes first
            QTimer.singleShot(0, lambda iid=item_id: self.open_item(iid))

    def _resolved_estimator_filter(self):
        data = self.estimator_combo.currentData()
        if data != ME_FILTER:
            return data
        name = get_current_estimator()
        if name:
            return name
        try:
            options = self.db.get_all_estimator_names()
        except Exception:
            options = [x for x in self.db.get_estimators() if x]
        chosen, ok = QInputDialog.getItem(
            self, "Set your estimator",
            "Pick your name for the Me filter (saved on this PC):",
            options, 0, True,
        )
        if not ok or not chosen.strip():
            self.estimator_combo.blockSignals(True)
            self.estimator_combo.setCurrentIndex(0)
            self.estimator_combo.blockSignals(False)
            return None
        set_current_estimator(chosen.strip())
        return chosen.strip()

    def _refresh_estimator_counts(self, start, end, statuses):
        if not hasattr(self, "counts_label"):
            return
        try:
            rows = self.db.count_board_items_by_estimator(
                start.isoformat(), end.isoformat(), statuses=statuses,
            )
        except Exception:
            self.counts_label.setText("")
            return
        if not rows:
            self.counts_label.setText("No board items in this view.")
            return
        self.counts_label.setText(" · ".join(f"{name} {cnt}" for name, cnt in rows))

    def _run_board_search(self):
        self._hide_search_suggestions()
        q = (self.search_input.text() or "").strip()
        if not q:
            QMessageBox.information(self, "Search", "Type a name, account, estimator, or location.")
            return
        try:
            rows = self.db.search_board_items(q, limit=80)
        except Exception as e:
            QMessageBox.warning(self, "Search failed", str(e))
            return
        if not rows:
            QMessageBox.information(self, "Search", f"No board items matched “{q}”.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Board search — {len(rows)} result(s)")
        dlg.setMinimumSize(560, 420)
        lay = QVBoxLayout(dlg)
        tip = QLabel("Double-click a row to open it. COMPLETE items stay searchable forever.")
        tip.setObjectName("secondaryLabel")
        tip.setWordWrap(True)
        lay.addWidget(tip)
        lst = QListWidget()
        lst.setAlternatingRowColors(True)
        for r in rows:
            item = QListWidgetItem(self._format_search_row(r))
            item.setData(Qt.UserRole, r)
            lst.addItem(item)
        lay.addWidget(lst, 1)

        def _open_selected():
            item = lst.currentItem()
            if not item:
                return
            row = item.data(Qt.UserRole) or {}
            dlg.accept()
            self._open_board_search_hit(row)

        lst.itemDoubleClicked.connect(lambda _i: _open_selected())
        btns = QHBoxLayout()
        btns.addStretch()
        open_btn = QPushButton("Open")
        open_btn.setObjectName("primaryButton")
        open_btn.clicked.connect(_open_selected)
        btns.addWidget(open_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.reject)
        btns.addWidget(close_btn)
        lay.addLayout(btns)
        dlg.exec_()

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for c in range(8):
            self.grid.setColumnStretch(c, 0)
            self.grid.setColumnMinimumWidth(c, 0)
        for r in range(8):
            self.grid.setRowStretch(r, 0)
            self.grid.setRowMinimumHeight(r, 0)

    def _visible_range(self):
        if self.view_mode == "day":
            return self.anchor_date, self.anchor_date
        monday = _monday_of(self.anchor_date)
        if self.view_mode == "week":
            end = monday + timedelta(days=4 if self.hide_weekends else 6)
            return monday, end
        if self.view_mode == "3week":
            start = monday - timedelta(days=7)
            end = start + timedelta(days=20)
            return start, end
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdatescalendar(self.anchor_date.year, self.anchor_date.month)
        return weeks[0][0], weeks[-1][6]

    def _heading_text(self):
        if self.view_mode == "day":
            return self.anchor_date.strftime("%A, %b %d, %Y")
        if self.view_mode in ("week", "3week"):
            start, end = self._visible_range()
            if start.year == end.year:
                return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
            return f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
        return f"{calendar.month_name[self.anchor_date.month]} {self.anchor_date.year}"

    def _rebuild(self):
        self._clear_grid()
        self._rebuild_weekday_header()
        self.month_label.setText(self._heading_text())
        nav_tips = {
            "month": ("Previous month", "Next month"),
            "3week": ("Previous week", "Next week"),
            "week": ("Previous week", "Next week"),
            "day": ("Previous day", "Next day"),
        }
        self.prev_btn.setToolTip(nav_tips[self.view_mode][0])
        self.next_btn.setToolTip(nav_tips[self.view_mode][1])

        try:
            self.color_map = self.db.get_estimator_color_map()
        except Exception:
            self.color_map = {}

        start, end = self._visible_range()
        estimator_filter = self._resolved_estimator_filter()
        statuses = self.status_combo.currentData()
        items = self.db.get_board_items(
            start.isoformat(), end.isoformat(),
            estimator=estimator_filter, statuses=statuses,
        )
        self._refresh_estimator_counts(start, end, statuses)
        by_date = {}
        for it in items:
            by_date.setdefault(it["board_date"], []).append(it)

        if self.view_mode == "day":
            cell = DayCell(self.anchor_date, True, self, max_visible=None)
            cell.set_items(by_date.get(self.anchor_date.isoformat(), []), self.color_map)
            self.grid.addWidget(cell, 0, 0)
            self.grid.setRowStretch(0, 1)
            self._set_equal_columns(self.grid, 1)
            return

        if self.view_mode == "week":
            monday = _monday_of(self.anchor_date)
            days = [monday + timedelta(days=i) for i in range(5 if self.hide_weekends else 7)]
            self.grid.setRowStretch(0, 1)
            for c, day in enumerate(days):
                cell = DayCell(day, True, self, max_visible=12)
                cell.set_items(by_date.get(day.isoformat(), []), self.color_map)
                self.grid.addWidget(cell, 0, c)
            self._set_equal_columns(self.grid, len(days))
            return

        if self.view_mode == "3week":
            start_monday = _monday_of(self.anchor_date) - timedelta(days=7)
            cols = 5 if self.hide_weekends else 7
            for r in range(3):
                self.grid.setRowStretch(r, 1)
                week_monday = start_monday + timedelta(days=7 * r)
                days = [week_monday + timedelta(days=i) for i in range(cols)]
                for c, day in enumerate(days):
                    cell = DayCell(day, True, self, max_visible=10)
                    cell.set_items(by_date.get(day.isoformat(), []), self.color_map)
                    self.grid.addWidget(cell, r, c)
            self._set_equal_columns(self.grid, cols)
            return

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdatescalendar(self.anchor_date.year, self.anchor_date.month)
        for r, week in enumerate(weeks):
            days = week[:5] if self.hide_weekends else week
            self.grid.setRowStretch(r, 1)
            for c, day in enumerate(days):
                cell = DayCell(day, day.month == self.anchor_date.month, self)
                cell.set_items(by_date.get(day.isoformat(), []), self.color_map)
                self.grid.addWidget(cell, r, c)
        self._set_equal_columns(self.grid, 5 if self.hide_weekends else 7)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def move_item(self, item_id, new_date):
        try:
            self.db.update_board_item_date(item_id, new_date.isoformat())
        except Exception as e:
            QMessageBox.warning(self, "Move failed", str(e))
        self._rebuild()

    def add_item(self, default_date=None):
        dlg = BidBoardItemDialog(self.db, self)
        if default_date is not None:
            qd = QDate(default_date.year, default_date.month, default_date.day)
            dlg.due_date_input.setDate(qd)
            dlg.board_date_input.setDate(qd)
        if dlg.exec_() == QDialog.Accepted and dlg.outcome == "save" and dlg.result_data:
            d = dlg.result_data
            item_id = self.db.add_board_item(
                d["bid_name"], d["board_date"], d["actual_due_date"],
                d["actual_due_time"], d["estimator"], d["notes"], d["customer_ids"],
                location=d.get("location"),
            )
            dlg.apply_side_effects(item_id)
            self.refresh()

    def open_item(self, item_id):
        data = self.db.get_board_item(item_id)
        if not data:
            return
        dlg = BidBoardItemDialog(self.db, self, item_data=data)
        result = dlg.exec_()
        pending_bid = getattr(dlg, "pending_open_bid_id", None)
        if pending_bid:
            self._open_normal_bid(pending_bid)
            return
        if result != QDialog.Accepted or not dlg.result_data:
            return
        d = dlg.result_data
        self.db.update_board_item(
            item_id, d["bid_name"], d["board_date"], d["actual_due_date"],
            d["actual_due_time"], d["estimator"], d["notes"], d["customer_ids"],
            location=d.get("location"),
        )
        dlg.apply_side_effects(item_id)
        if dlg.outcome == "complete":
            self._complete(item_id)
        elif dlg.outcome == "mark_complete":
            self._mark_complete_only(item_id)
        elif dlg.outcome == "link_existing":
            self._link_existing_bid(item_id)
        elif dlg.outcome == "not_bidding":
            self.db.set_board_item_status(item_id, "NOT_BIDDING")
            self._rebuild()
        elif dlg.outcome == "in_progress":
            self.db.set_board_item_status(item_id, "IN_PROGRESS")
            self._rebuild()
        else:
            self._rebuild()

    def show_card_menu(self, item_id, global_pos):
        data = self.db.get_board_item(item_id)
        if not data:
            return
        status = data.get("board_status", "IN_PROGRESS")
        menu = QMenu(self)

        edit_act = menu.addAction("Open / Edit...")

        assign_menu = menu.addMenu("Assign to")
        me_act = assign_menu.addAction("Me")
        assign_menu.addSeparator()
        estimator_acts = {}
        try:
            names = self.db.get_all_estimator_names()
        except Exception:
            names = [x for x in self.db.get_estimators() if x]
        for name in names:
            act = assign_menu.addAction(name)
            estimator_acts[act] = name
        unassign_act = None
        if data.get("estimator"):
            menu.addSeparator()
            unassign_act = menu.addAction("Unassign")

        complete_act = None
        mark_complete_act = None
        link_act = None
        not_bidding_act = None
        in_progress_act = None
        menu.addSeparator()
        link_act = menu.addAction("Link Existing Bid...")
        if status == "COMPLETE":
            complete_act = menu.addAction("Log Another Bid...")
            in_progress_act = menu.addAction("Mark In Progress")
        elif status != "NOT_BIDDING":
            complete_act = menu.addAction("Complete Bid...")
            mark_complete_act = menu.addAction("Mark Complete (no new bid)")
        if status == "IN_PROGRESS":
            not_bidding_act = menu.addAction("Mark Not Bidding")
        elif status == "NOT_BIDDING":
            in_progress_act = menu.addAction("Mark In Progress")

        chosen = menu.exec_(global_pos)
        if chosen is None:
            return
        if chosen == edit_act:
            self.open_item(item_id)
        elif chosen == me_act:
            self._assign_to_me(item_id)
        elif chosen in estimator_acts:
            self.db.assign_board_item(item_id, estimator_acts[chosen])
            self.refresh()
        elif unassign_act is not None and chosen == unassign_act:
            self.db.assign_board_item(item_id, None)
            self._rebuild()
        elif link_act is not None and chosen == link_act:
            self._link_existing_bid(item_id)
        elif mark_complete_act is not None and chosen == mark_complete_act:
            self._mark_complete_only(item_id)
        elif complete_act is not None and chosen == complete_act:
            self._complete(item_id)
        elif not_bidding_act is not None and chosen == not_bidding_act:
            self.db.set_board_item_status(item_id, "NOT_BIDDING")
            self._rebuild()
        elif in_progress_act is not None and chosen == in_progress_act:
            self.db.set_board_item_status(item_id, "IN_PROGRESS")
            self._rebuild()

    def _assign_to_me(self, item_id):
        name = get_current_estimator()
        if not name:
            try:
                options = self.db.get_all_estimator_names()
            except Exception:
                options = [x for x in self.db.get_estimators() if x]
            chosen, ok = QInputDialog.getItem(
                self, "Set your estimator",
                "This computer has no estimator identity yet.\n"
                "Pick your name (saved for future 'Assign to Me'):",
                options, 0, True,
            )
            if not ok or not chosen.strip():
                return
            name = chosen.strip()
            set_current_estimator(name)
        self.db.assign_board_item(item_id, name)
        self.refresh()

    def _mark_complete_only(self, item_id):
        """Blue COMPLETE without creating a BidTracker bid. Outlook will not undo this."""
        try:
            self.db.mark_board_item_complete(item_id)
        except Exception as e:
            QMessageBox.critical(self, "Mark Complete failed", str(e))
        self._rebuild()

    def _link_existing_bid(self, item_id):
        data = self.db.get_board_item(item_id)
        if not data:
            return
        dlg = LinkBoardBidDialog(self.db, data, self)
        if dlg.exec_() != QDialog.Accepted or not dlg.selected_bid:
            return
        bid = dlg.selected_bid
        try:
            self.db.link_existing_board_bid(item_id, bid["id"])
        except Exception as e:
            QMessageBox.critical(self, "Link failed", str(e))
            self._rebuild()
            return
        self._refresh_bids_tab()
        ask = QMessageBox(self)
        ask.setIcon(QMessageBox.Question)
        ask.setWindowTitle("Bid linked")
        ask.setText(
            f"Linked “{bid.get('bid_name') or 'bid'}” to this board item.\n\n"
            "Mark the board item Complete (no new bid)?"
        )
        yes = ask.addButton("Mark Complete", QMessageBox.YesRole)
        ask.addButton("Keep current status", QMessageBox.NoRole)
        ask.exec_()
        if ask.clickedButton() == yes and data.get("board_status") != "COMPLETE":
            try:
                self.db.mark_board_item_complete(item_id)
            except Exception as e:
                QMessageBox.warning(self, "Mark Complete failed", str(e))
        self.refresh()

    def _complete(self, item_id):
        """Log one or more normal bids from this opportunity; COMPLETE only on Finish."""
        while True:
            item = self.db.get_board_item(item_id)
            if not item:
                return
            already_complete = item.get("board_status") == "COMPLETE"
            due = item.get("actual_due_date") or item.get("board_date")
            prefill = {
                "bid_name": item.get("bid_name", ""),
                "estimator": item.get("estimator") or "",
                "original_bid_date": date.today().isoformat(),
                "due_date": due,
                "location": item.get("location") or "",
                "notes": item.get("notes", "") or "",
                "customer_ids": [c["id"] for c in self.db.get_board_item_customers(item_id)],
            }

            dlg = AddBidDialog(self.db, self, initial_values=prefill)
            if dlg.exec_() != QDialog.Accepted or not dlg.result_data:
                self._rebuild()
                return
            d = dlg.result_data
            try:
                self.db.log_board_item_bid(
                    item_id, d["bid_name"], d["estimator"], d["original_bid_date"],
                    d["notes"], d["customer_ids"], d["bid_total"],
                    d["solid_surf_sf"], d["stone_sf"],
                    due_date=d.get("due_date"), location=d.get("location"),
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Log bid failed",
                    f"The bid was not created. The board item was not changed.\n\n{e}",
                )
                self._rebuild()
                return

            self._refresh_bids_tab()

            box = QMessageBox(self)
            box.setIcon(QMessageBox.Information)
            box.setWindowTitle("Bid logged")
            box.setText(
                "Bid logged successfully. Are there additional bid options "
                "or pricing versions for this opportunity?"
            )
            log_btn = box.addButton("Log Another Bid", QMessageBox.AcceptRole)
            if already_complete:
                done_btn = box.addButton("Done", QMessageBox.RejectRole)
            else:
                done_btn = box.addButton("Finish & Mark Complete", QMessageBox.YesRole)
            box.exec_()
            clicked = box.clickedButton()
            if clicked == log_btn:
                continue
            if not already_complete and clicked == done_btn:
                try:
                    self.db.mark_board_item_complete(item_id)
                except Exception as e:
                    QMessageBox.critical(self, "Complete failed", str(e))
            break

        self.refresh()
        self._refresh_bids_tab()

    def _open_normal_bid(self, bid_id):
        win = self.window()
        bids_tab = getattr(win, "bids_tab", None)
        tabs = getattr(win, "tabs", None)
        if tabs is not None and bids_tab is not None:
            idx = tabs.indexOf(bids_tab)
            if idx >= 0:
                tabs.setCurrentIndex(idx)
        if bids_tab is not None and hasattr(bids_tab, "open_bid"):
            bids_tab.open_bid(bid_id)

    def _refresh_bids_tab(self):
        win = self.window()
        bids_tab = getattr(win, "bids_tab", None)
        if bids_tab is not None and hasattr(bids_tab, "refresh"):
            try:
                bids_tab.refresh()
            except Exception:
                pass

    def show_day_popup(self, cell_date, items):
        dlg = QDialog(self)
        dlg.setWindowTitle(cell_date.strftime("%A, %B %d, %Y"))
        dlg.setModal(True)
        dlg.setMinimumWidth(360)
        v = QVBoxLayout(dlg)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(6)

        title = QLabel(f"{len(items)} bid board item(s)")
        title.setObjectName("subheadingLabel")
        v.addWidget(title)

        for it in items:
            card = BoardCard(it, color_map=self.color_map)
            card.clicked.connect(lambda iid, d=dlg: (d.accept(), self.open_item(iid)))
            card.menu_requested.connect(self.show_card_menu)
            v.addWidget(card)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        v.addWidget(close_btn)
        dlg.exec_()
