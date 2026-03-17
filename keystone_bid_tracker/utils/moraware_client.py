"""
Keystone Bid Tracker - Moraware Client
Handles session-based login and data extraction from Moraware.

Uses web login for session auth, then scrapes the job detail page for
job info (salesperson, PM, created date, status). Job Ticket A TP codes
and sq_ft are fetched via Moraware's AJAX endpoint
(Dialog_GetJobFormContentForExpand). Invoice activities are scraped from
the activities table.

Enable DEBUG logging for troubleshooting:
    logging.getLogger("moraware_client").setLevel(logging.DEBUG)
"""

import logging
import os
import re
import time
from datetime import date, datetime
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import requests
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup

logger = logging.getLogger("moraware_client")

LOGIN_PATHS = ["/go", "/sys/login", "/login", "/sys/go", "/"]
API_ERROR_CODES = {
    "1": "SessionTimedOut",
    "2": "InsufficientSecurityPrivileges",
    "3": "UnsupportedVersion",
    "4": "InvalidRequestDocument",
    "5": "UnsupportedCommand",
    "6": "LoginFailed",
    "7": "NonExistentObject",
}

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# Keystone tenant-specific custom field IDs.
# NOTE: These values are NOT portable across Moraware tenants and should be
# rediscovered for any non-Keystone deployment.
_TP_CODE_ACTIVITY_FIELD_ID = "71"
_JOB_NUMBER_FIELD_ID = "13"

_ACTIVITY_SQ_FT_FIELD_ID = "72"


JOB_DETAIL_LABELS = {
    "job_number": [
        "job", "job number", "job no", "job num",
    ],
    "salesperson": [
        "salesperson", "sales person", "sales rep", "sales representative",
    ],
    "project_manager": [
        "keystone pm",
    ],
    "created_date": [
        "created", "created date", "date created", "job created", "creation date",
    ],
    "status": [
        "status", "job status",
    ],
}


def _normalize_label(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _match_label(normalized: str) -> str | None:
    """Return the result key if normalized matches any canonical label, else None."""
    for key, candidates in JOB_DETAIL_LABELS.items():
        if normalized in candidates:
            return key
    return None


def _normalize_phase_key(value: str) -> str:
    """Normalize phase labels for robust matching (e.g. 'ST1, ST2' tokens)."""
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _split_phase_tokens(value: str) -> list[str]:
    """Split combined phase labels like 'ST1, ST2' or 'ST1 / ST2'."""
    parts = re.split(r"\s*(?:,|/|&|\+|\band\b)\s*", value or "", flags=re.IGNORECASE)
    return [p.strip() for p in parts if p and p.strip()]


def _resolve_activity_phase_targets(activity_phase: str, job_ticket_phase_names: list[str]) -> list[str]:
    """
    Resolve one activity phase label to one-or-many Job Ticket A phase names.

    - Exact normalized match wins.
    - Otherwise split common combined delimiters and match each token.
    """
    if not activity_phase:
        return []

    name_map = {_normalize_phase_key(name): name for name in job_ticket_phase_names}
    direct = name_map.get(_normalize_phase_key(activity_phase))
    if direct:
        return [direct]

    matched = []
    for token in _split_phase_tokens(activity_phase):
        key = _normalize_phase_key(token)
        if not key:
            continue
        resolved = name_map.get(key)
        if resolved and resolved not in matched:
            matched.append(resolved)
    return matched


def _parse_jobs_table(html: str) -> list[dict]:
    """Parse Moraware jobs table HTML into normalized job dicts."""
    def _norm(text):
        t = (text or "").lower().strip()
        t = re.sub(r"[^a-z0-9]+", " ", t)
        return re.sub(r"\s+", " ", t).strip()

    soup = _make_soup(html, prefer_lxml=True)
    rows = soup.select("tbody#JobsBody tr")
    if not rows:
        rows = soup.select("#JobsBody tr")
    if not rows:
        return []

    name_col = num_col = account_col = sp_col = pm_col = -1
    for row in rows:
        header_cells = row.select(
            "td.headerSortableCol, th.headerSortableCol, td.headerCol, th.headerCol"
        )
        if not header_cells:
            continue
        all_cells = row.select("td, th")
        for i, c in enumerate(all_cells):
            norm = _norm(c.get_text(strip=True))
            if norm == "job number":
                num_col = i
            elif norm == "account":
                account_col = i
            elif norm == "job name":
                name_col = i
            elif norm in ("salesperson", "sales person", "sales rep"):
                sp_col = i
            elif norm == "keystone pm":
                pm_col = i
        break

    jobs = []
    for row in rows:
        cells = row.select("td")
        if len(cells) < 3:
            continue
        if any(cls in (c.get("class") or []) for c in cells for cls in ("headerSortableCol", "headerCol")):
            continue

        link = cells[name_col].select_one("a[href*='/sys/job/']") if 0 <= name_col < len(cells) else None
        if not link:
            for cell in cells:
                link = cell.select_one("a[href*='/sys/job/']")
                if link:
                    break
        if not link:
            continue

        href = (link.get("href") or "").strip()
        parts = href.rstrip("/").split("/")
        job_id = parts[-1] if parts else ""
        name = link.get_text(strip=True)
        if not job_id or not name:
            continue

        job_number = cells[num_col].get_text(strip=True) if 0 <= num_col < len(cells) else ""
        account_cell = cells[account_col] if 0 <= account_col < len(cells) else None
        account = ""
        if account_cell:
            acc_link = account_cell.select_one("a[href*='/sys/account/']")
            account = acc_link.get_text(strip=True) if acc_link else account_cell.get_text(strip=True)

        salesperson = (cells[sp_col].get_text(strip=True) if 0 <= sp_col < len(cells) else "").strip()
        project_manager = (cells[pm_col].get_text(strip=True) if 0 <= pm_col < len(cells) else "").strip()

        jobs.append(
            {
                "id": job_id,
                "name": name,
                "job_number": job_number,
                "account": account,
                "salesperson": salesperson,
                "project_manager": project_manager,
            }
        )
    return jobs


def _make_soup(html: str, prefer_lxml: bool = False) -> BeautifulSoup:
    """Create BeautifulSoup parser, preferring lxml in hot paths when available."""
    if prefer_lxml:
        try:
            return BeautifulSoup(html, "lxml")
        except Exception:
            logger.debug("lxml parser unavailable, falling back to html.parser")
    return BeautifulSoup(html, "html.parser")


class MorewareClient:
    """Connects to Moraware via web session and XML API."""

    MORAWARE_CUID = 29  # Moraware instance customer ID, used in AJAX form requests

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str,
        timeout: int = 15,
        use_fast_sync: bool = True,
    ):
        self.username = username
        self.password = password
        self.timeout = timeout
        self.use_fast_sync = bool(use_fast_sync)
        self.session = None
        self._api_session_id = ""

        parsed = urlparse(base_url.strip().rstrip("/"))
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        self._user_path = parsed.path.rstrip("/") if parsed.path and parsed.path != "/" else ""
        logger.info("Normalized base_url=%s, user_path=%s", self.base_url, self._user_path)

    # ------------------------------------------------------------------
    # Login (web-based, kept for session cookies)
    # ------------------------------------------------------------------
    def _login_paths(self) -> list:
        paths = []
        if self._user_path and self._user_path not in LOGIN_PATHS:
            paths.append(self._user_path)
        paths.extend(LOGIN_PATHS)
        return paths

    def _find_login_page(self) -> tuple:
        """Try each candidate path until we find one with a login form."""
        for path in self._login_paths():
            url = f"{self.base_url}{path}"
            try:
                logger.info("Probing %s for login form", url)
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200 and self._page_has_login_form(resp.text):
                    logger.info("Found login form at %s", url)
                    return url, resp.text
                logger.debug("No login form at %s (status=%d)", url, resp.status_code)
            except requests.RequestException as e:
                logger.debug("Could not reach %s: %s", url, e)
        raise ConnectionError(
            f"No login form found at any known path on {self.base_url}. "
            f"Tried: {', '.join(self._login_paths())}"
        )

    def _new_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update({"User-Agent": BROWSER_UA})
        adapter = HTTPAdapter(pool_connections=25, pool_maxsize=25)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        return s

    def login(self) -> bool:
        """Authenticate and store session cookies. Returns True on success."""
        self.session = self._new_session()

        try:
            page_url, page_html = self._find_login_page()
            fields = self._detect_form_fields(page_html, page_url)

            post_url = fields.get("action_url", page_url)
            data = {
                fields["username"]: self.username,
                fields["password"]: self.password,
            }
            data.update(fields.get("extra", {}))

            logger.info("POST %s (user_field=%s, pwd_field=%s, hidden=%s)",
                        post_url, fields["username"], fields["password"],
                        list(fields.get("extra", {}).keys()))
            resp = self.session.post(post_url, data=data, timeout=self.timeout)
            resp.raise_for_status()
            logger.info("Post-login URL: %s  Status: %d", resp.url, resp.status_code)

            if self._page_has_login_form(resp.text):
                soup = _make_soup(resp.text)
                err = soup.select_one(".error, .alert-danger, .login-error, .minimalPageMessage")
                msg = err.get_text(strip=True) if err and err.get_text(strip=True) else "Invalid credentials"
                raise ConnectionError(f"Login failed: {msg}")

            logger.info("Login successful")
            return True
        except requests.RequestException as e:
            raise ConnectionError(f"Could not connect to Moraware: {e}")

    @staticmethod
    def _page_has_login_form(html: str) -> bool:
        soup = _make_soup(html)
        return bool(soup.select_one("input[type='password']"))

    @staticmethod
    def _detect_form_fields(html: str, page_url: str = "") -> dict:
        """Parse the login form to find actual input field names and action URL."""
        soup = _make_soup(html)

        form = None
        for f in soup.select("form"):
            if f.select_one("input[type='password']"):
                form = f
                break
        if not form:
            form = soup.select_one("form")
        if not form:
            logger.warning("No <form> element found, using default field names")
            return {"username": "username", "password": "password"}

        action = form.get("action", "")
        action_url = page_url
        if action:
            if action.startswith("http"):
                action_url = action
            elif action.startswith("/"):
                parsed = urlparse(page_url)
                action_url = f"{parsed.scheme}://{parsed.netloc}{action}"
            else:
                action_url = page_url.rstrip("/") + "/" + action
        logger.info("Form action URL: %s", action_url)

        password_input = form.select_one("input[type='password']")
        pwd_name = password_input.get("name", "password") if password_input else "password"

        user_name = "username"
        for inp in form.select("input[type='text'], input[type='email'], input:not([type])"):
            name = inp.get("name", "")
            inp_type = inp.get("type", "").lower()
            if name and name != pwd_name and inp_type not in ("hidden", "submit"):
                user_name = name
                break

        extra = {}
        for inp in form.select("input[type='hidden']"):
            name = inp.get("name", "")
            val = inp.get("value", "")
            if name:
                extra[name] = val

        submit_btn = form.select_one("input[type='submit']")
        if submit_btn and submit_btn.get("name"):
            extra[submit_btn["name"]] = submit_btn.get("value", "")

        logger.info("Detected form fields: username='%s', password='%s', extra=%s, action='%s'",
                     user_name, pwd_name, list(extra.keys()), action_url)
        return {"username": user_name, "password": pwd_name, "extra": extra, "action_url": action_url}

    def test_login(self) -> tuple:
        """Non-raising login test. Returns (success: bool, message: str)."""
        try:
            self.login()
            return True, "Logged in successfully."
        except Exception as e:
            return False, str(e)

    def dump_diagnostics(self, output_dir: str) -> str:
        """Save raw HTML from key Moraware pages for debugging."""
        os.makedirs(output_dir, exist_ok=True)
        saved = []

        self.session = self._new_session()

        try:
            page_url, page_html = self._find_login_page()
            login_path = os.path.join(output_dir, "moraware_login_page.html")
            with open(login_path, "w", encoding="utf-8") as f:
                f.write(page_html)
            saved.append(f"Login page from {page_url} ({len(page_html)} bytes) -> {login_path}")
        except Exception as e:
            saved.append(f"Could not find login page: {e}")

        try:
            self.login()
        except Exception as e:
            saved.append(f"Login failed: {e}")
            summary = "Diagnostic dump (partial - login failed):\n" + "\n".join(f"  - {s}" for s in saved)
            logger.info(summary)
            return summary

        jobs_url = f"{self.base_url}/sys/jobs"
        try:
            logger.info("Diagnostics: GET %s", jobs_url)
            resp = self.session.get(jobs_url, timeout=self.timeout)
            path = os.path.join(output_dir, "moraware_jobs_page.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            saved.append(f"Jobs list page ({len(resp.text)} bytes) -> {path}")

            soup = _make_soup(resp.text)
            sample_link = soup.select_one("a[href*='/sys/job/']")
            if sample_link:
                href = sample_link.get("href", "")
                if not href.startswith("http"):
                    href = f"{self.base_url}{href}"
                logger.info("Diagnostics: GET sample job %s", href)
                resp2 = self.session.get(href, timeout=self.timeout)
                path2 = os.path.join(output_dir, "moraware_job_detail.html")
                with open(path2, "w", encoding="utf-8") as f:
                    f.write(resp2.text)
                saved.append(f"Sample job page ({len(resp2.text)} bytes) -> {path2}")
        except Exception as e:
            saved.append(f"Error fetching jobs page: {e}")

        summary = "Diagnostic dump complete:\n" + "\n".join(f"  - {s}" for s in saved)
        logger.info(summary)
        return summary

    # ------------------------------------------------------------------
    # Moraware XML API
    # ------------------------------------------------------------------
    def _api_post_raw(self, request_xml: str) -> str:
        """POST XML request to Moraware API, return raw response text."""
        if not self.session:
            raise RuntimeError("Not logged in. Call login() first.")

        url = f"{self.base_url}/api.aspx"
        logger.info("API POST %s (%d bytes)", url, len(request_xml))
        logger.debug("Request XML: %s", request_xml[:500])

        try:
            resp = self.session.post(
                url, data=request_xml,
                headers={"Content-Type": "text/xml"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Moraware API request failed: {e}") from e
        logger.debug("API response (%d bytes): %s", len(resp.text), resp.text[:500])
        return resp.text

    def _api_post(self, request_xml: str) -> ET.Element:
        """POST XML request to Moraware API, return parsed root element."""
        return ET.fromstring(self._api_post_raw(request_xml))

    @staticmethod
    def _api_error_info(root: ET.Element) -> tuple[str, str]:
        """Return (error_code, description) from API <error> response."""
        err = root if root.tag == "error" else root.find(".//error")
        if err is None:
            return "", ""

        code = (err.get("errorCode", "") or "").strip()
        description = (err.findtext("description", "") or "").strip()
        if not description:
            description = (err.get("errorCodeDescription", "") or "").strip()
        if not description:
            description = "".join(err.itertext()).strip()
        return code, description

    @staticmethod
    def _api_error_label(error_code: str) -> str:
        return API_ERROR_CODES.get((error_code or "").strip(), "UnknownError")

    def _api_connect(self):
        """Create Moraware API session (API v5) and cache session id."""
        if not self.session:
            raise RuntimeError("Not logged in. Call login() first.")
        self._api_session_id = ""
        xml = (
            f'<MorawareCommand version="5" userName="{escape(self.username)}" '
            f'password="{escape(self.password)}"><sessionCreate /></MorawareCommand>'
        )
        root = self._api_post(xml)
        code, description = self._api_error_info(root)
        if code or root.tag == "error":
            label = self._api_error_label(code)
            raise RuntimeError(f"Moraware API sessionCreate failed ({code}:{label}): {description}")

        session_el = root.find("sessionCreate/session")
        if session_el is None:
            session_el = root.find(".//sessionCreate/session")
        if session_el is None:
            raise RuntimeError("Moraware API sessionCreate returned no MorawareResponse/sessionCreate/session element.")

        session_id = (session_el.get("id", "") or "").strip()
        if not session_id:
            raise RuntimeError("Moraware API sessionCreate returned empty session id.")
        self._api_session_id = session_id

    def _api_command(self, command_name: str, command_inner_xml: str = "", retry_on_timeout: bool = True) -> ET.Element:
        """Execute one API v5 command under MorawareCommand/session context."""
        if not self._api_session_id:
            self._api_connect()

        xml = (
            f'<MorawareCommand version="5" sessionId="{escape(self._api_session_id)}">'
            f'<{command_name}>{command_inner_xml}</{command_name}>'
            f"</MorawareCommand>"
        )
        root = self._api_post(xml)
        code, description = self._api_error_info(root)

        # APIErrorCodes_Enum.SessionTimedOut = 1 in decompiled JobTrackerAPI5.
        if code == "1" and retry_on_timeout:
            logger.info("API session timed out. Reconnecting and retrying %s.", command_name)
            self._api_session_id = ""
            self._api_connect()
            return self._api_command(command_name, command_inner_xml, retry_on_timeout=False)

        if code or root.tag == "error":
            label = self._api_error_label(code)
            raise RuntimeError(f"Moraware API {command_name} failed ({code}:{label}): {description}")
        return root

    def get_job_details(self, job_id: str) -> dict:
        """Fetch job metadata by scraping the job detail page.

        Returns dict with keys: job_number, created_date, salesperson, project_manager, status.
        """
        result = {
            "job_number": "",
            "created_date": "",
            "salesperson": "",
            "project_manager": "",
            "status": "",
        }

        if not self.session:
            logger.error("get_job_details called without active session")
            return result

        resp = None
        for path in (f"/sys/job/{job_id}", f"/sys/jobs/{job_id}"):
            url = f"{self.base_url}{path}"
            try:
                logger.info("GET %s (for job details)", url)
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 404:
                    logger.info("Got 404 from %s, trying fallback", url)
                    resp = None
                    continue
                if self._page_has_login_form(resp.text):
                    logger.info("Got login form from %s, trying fallback", url)
                    resp = None
                    continue
                resp.raise_for_status()
                break
            except requests.RequestException as e:
                logger.error("Failed to fetch %s: %s", url, e)
                resp = None

        if resp is None:
            logger.error("Could not load job detail page for %s from any URL", job_id)
            return result

        if self._page_has_login_form(resp.text):
            logger.warning("Moraware session expired — got login form for job %s", job_id)
            return result

        soup = _make_soup(resp.text, prefer_lxml=True)

        for row in soup.select("tr"):
            cells = row.select("td, th")
            if len(cells) >= 2:
                label = _normalize_label(cells[0].get_text(strip=True))
                value_text = cells[1].get_text(strip=True)
                key = _match_label(label)
                if key and value_text and not result[key]:
                    result[key] = value_text

        for label_el in soup.select("label, .label, .field-label, .detailLabel"):
            label = _normalize_label(label_el.get_text(strip=True))
            sibling = label_el.find_next_sibling()
            if sibling:
                value_text = sibling.get_text(strip=True)
            else:
                parent = label_el.parent
                value_text = parent.get_text(strip=True) if parent else ""
                value_text = value_text.replace(label_el.get_text(strip=True), "", 1).strip()
            key = _match_label(label)
            if key and value_text and not result[key]:
                result[key] = value_text

        for tbl in soup.select("table#ActivitiesBody, table#activitiesBody"):
            tbl.decompose()

        for el in soup.find_all(string=True):
            text = el.strip()
            if not text or ":" not in text:
                continue
            if len(text) > 80:
                continue
            if text.count(":") != 1:
                continue
            parts = text.split(":", 1)
            label = _normalize_label(parts[0])
            value_text = parts[1].strip()
            key = _match_label(label)
            if key and value_text and not result[key]:
                result[key] = value_text

        logger.info("Job details for %s: %s", job_id, result)
        return result

    def list_jobs(self, active_only: bool = True, pagesize: int = 300, max_pages: int = 30) -> list[dict]:
        """
        Return Moraware jobs from /sys/jobs, with optional active-only filtering.

        Uses paged fetch and deduplicates by Moraware job id.
        """
        if not self.session:
            raise RuntimeError("Not logged in. Call login() first.")

        def _fetch_job_pages(status_filter: str = "", status_label: str = "") -> list[dict]:
            base_url = (
                f"{self.base_url}/sys/jobs?"
                "view=0&status=0&"
                f"pagesize={max(1, int(pagesize or 300))}"
                "&cols=JA13,CN1,JN1,JA77,JN5"
                "&sort=a2"
                f"{status_filter}"
            )
            jobs_out = []
            prev_fingerprint = None

            for page in range(1, max(1, int(max_pages or 30)) + 1):
                resp = self.session.get(f"{base_url}&page={page}", timeout=self.timeout)
                resp.raise_for_status()
                if self._page_has_login_form(resp.text):
                    raise RuntimeError("Moraware session expired while fetching jobs.")

                jobs = _parse_jobs_table(resp.text)
                if not jobs:
                    break

                fingerprint = (
                    str(jobs[0].get("job_number") or "").strip(),
                    str(jobs[-1].get("job_number") or "").strip(),
                )
                if prev_fingerprint == fingerprint:
                    logger.warning("Moraware jobs pagination repeated page fingerprint at page %s", page)
                    break
                prev_fingerprint = fingerprint

                for job in jobs:
                    item = dict(job)
                    if status_label:
                        item["status"] = status_label
                    jobs_out.append(item)

                if len(jobs) < max(1, int(pagesize or 300)):
                    break

            return jobs_out

        all_jobs = []
        seen_ids = set()
        if active_only:
            # j19 is Moraware "job status" filter.
            # PM Active Jobs parity uses: 1=Active, 3=Unscheduled, 4=30+ Days Old.
            status_filters = [
                ("&filters=2|3:0:j19:10:j19;1;0", "Active"),
                ("&filters=2|3:0:j19:10:j19;3;0", "Unscheduled"),
                ("&filters=2|3:0:j19:10:j19;4;0", "30+ Days Old"),
            ]
            for filter_value, label in status_filters:
                for job in _fetch_job_pages(status_filter=filter_value, status_label=label):
                    job_id = str(job.get("id") or "").strip()
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    all_jobs.append(job)
        else:
            for job in _fetch_job_pages():
                job_id = str(job.get("id") or "").strip()
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)
                all_jobs.append(job)

        logger.info("Fetched %d Moraware jobs (active_only=%s)", len(all_jobs), active_only)
        return all_jobs

    def get_invoice_data(self, job_id: str) -> list:
        """Fetch invoice/phase data for a Moraware job.

        1. Scrape Job Ticket A forms from the job detail page for TP Codes per phase.
        2. Scrape the activities table for Invoice activities that may override
           the Job Ticket A TP Code.

        Returns list of dicts: {phase, tp_code, invoice_date, invoice_status, source}
        """
        url = f"{self.base_url}/sys/job/{job_id}"
        try:
            logger.info("GET %s (for invoice data)", url)
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to fetch job detail page for invoice data: %s", e)
            return []

        soup = _make_soup(resp.text, prefer_lxml=True)

        phases = self._get_job_ticket_a_phases(job_id)
        invoice_overrides = self._get_invoice_activities(job_id, soup)

        for activity_phase, inv_data in invoice_overrides.items():
            targets = _resolve_activity_phase_targets(activity_phase, list(phases.keys()))

            # If no phase tokens map to Job Ticket A, keep the legacy fallback row.
            if not targets:
                targets = [activity_phase]
                if activity_phase not in phases:
                    phases[activity_phase] = {
                        "tp_code": None,
                        "sq_ft": None,
                        "template_date": None,
                        "install_date": None,
                        "contact_customer_date": None,
                        "contact_customer_notes": "",
                        "invoice_date": None,
                        "invoice_status": "Pending",
                        "source": inv_data.get("source", "invoice_activity"),
                    }

            for phase_key in targets:
                if phase_key not in phases:
                    continue

                # Keep per-phase TP from Job Ticket A; only fill TP when phase TP is missing.
                if (
                    (phases[phase_key].get("tp_code") is None or phases[phase_key].get("tp_code") == "")
                    and inv_data.get("tp_code") not in (None, "")
                ):
                    phases[phase_key]["tp_code"] = inv_data["tp_code"]
                if inv_data.get("tp_code") not in (None, ""):
                    phases[phase_key]["source"] = "invoice_activity"

                # Only invoice activities can set invoice date/status.
                if inv_data.get("has_invoice_activity"):
                    if inv_data.get("invoice_date"):
                        phases[phase_key]["invoice_date"] = inv_data.get("invoice_date")
                    phases[phase_key]["invoice_status"] = inv_data.get("invoice_status", "Pending")

                if phases[phase_key].get("sq_ft") is None and inv_data.get("sq_ft") is not None:
                    phases[phase_key]["sq_ft"] = inv_data["sq_ft"]
                if inv_data.get("template_date"):
                    phases[phase_key]["template_date"] = inv_data["template_date"]
                if inv_data.get("install_date"):
                    phases[phase_key]["install_date"] = inv_data["install_date"]
                if inv_data.get("contact_customer_date"):
                    phases[phase_key]["contact_customer_date"] = inv_data["contact_customer_date"]
                if inv_data.get("contact_customer_notes"):
                    phases[phase_key]["contact_customer_notes"] = inv_data["contact_customer_notes"]

        result = []
        for phase_name in sorted(phases.keys()):
            p = phases[phase_name]
            result.append({
                "phase": phase_name,
                "tp_code": p.get("tp_code"),
                "sq_ft": p.get("sq_ft"),
                "template_date": p.get("template_date"),
                "install_date": p.get("install_date"),
                "contact_customer_date": p.get("contact_customer_date"),
                "contact_customer_notes": p.get("contact_customer_notes"),
                "invoice_date": p.get("invoice_date"),
                "invoice_status": p.get("invoice_status", "Pending"),
                "source": p.get("source", "job_ticket_a"),
            })

        logger.info("get_invoice_data for job %s: %d phases", job_id, len(result))
        return result

    def _get_job_ticket_a_phases(self, job_id: str) -> dict:
        """Fetch Job Ticket A form content via the Moraware AJAX endpoint.

        Moraware loads form content lazily via a POST to the base job URL with
        the Dialog_GetJobFormContentForExpand action. First scrapes the main job
        page to find Job Ticket A form IDs, then POSTs to fetch each form's
        content and parses the formRowTable structure.

        Returns {phase_name: {tp_code, invoice_date, invoice_status, source}}.
        """
        import time

        base_url = self.base_url
        job_url = f"{base_url}/sys/job/{job_id}"

        logger.info("GET %s (for Job Ticket A form IDs)", job_url)
        resp = self.session.get(job_url)
        resp.raise_for_status()
        soup = _make_soup(resp.text, prefer_lxml=True)

        form_ids = []
        for span in soup.find_all("span", onclick=True):
            if "job ticket a" in span.get_text(strip=True).lower():
                onclick = span.get("onclick", "")
                match = re.search(r"toggleJobFormDisplay\(\d+,(\d+)\)", onclick)
                if match:
                    form_ids.append(match.group(1))

        logger.info("Found %d Job Ticket A form(s) for job %s: %s", len(form_ids), job_id, form_ids)

        phases = {}
        timestamp = int(time.time() * 1000)

        for form_id in form_ids:
            payload = (
                f"C=mjtrs1&X=1&cuid={self.MORAWARE_CUID}&F=Dialog_GetJobFormContentForExpand"
                f"&P0=[{job_id}]&P1=[{form_id}]"
            )
            ajax_url = f"{base_url}/sys/job/{job_id}?U={timestamp}"
            logger.info("POST %s (for Job Ticket A form %s)", ajax_url, form_id)

            try:
                form_resp = self.session.post(
                    ajax_url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                form_resp.raise_for_status()
            except Exception as e:
                logger.error("Failed to fetch Job Ticket A form %s: %s", form_id, e)
                continue

            form_soup = _make_soup(form_resp.text, prefer_lxml=True)

            phase_name = None
            tp_code = None
            sq_ft = None

            for td in form_soup.select("table.formRowTable td"):
                divs = td.select("div")
                if len(divs) < 2:
                    continue
                label = divs[0].get_text(strip=True).replace(":", "").strip().lower()
                value = divs[1].get_text(strip=True)
                if not value or value == "\xa0":
                    continue
                if "job phase name" in label:
                    phase_name = value
                elif "tp code" in label:
                    try:
                        tp_code = float(value.replace(",", "").replace("$", "").strip())
                    except ValueError:
                        tp_code = None
                elif "phase total sq" in label:
                    try:
                        sq_ft = float(value.replace(",", "").strip())
                    except ValueError:
                        sq_ft = None

            if not phase_name:
                logger.debug("No phase name found in Job Ticket A form %s, skipping", form_id)
                continue

            phases[phase_name] = {
                "tp_code": tp_code,
                "sq_ft": sq_ft,
                "template_date": None,
                "install_date": None,
                "contact_customer_date": None,
                "contact_customer_notes": "",
                "invoice_date": None,
                "invoice_status": "Pending",
                "source": "job_ticket_a",
            }
            logger.info("Job Ticket A form %s: phase=%s tp_code=%s sq_ft=%s", form_id, phase_name, tp_code, sq_ft)

        logger.info("Found %d phases from Job Ticket A forms for job %s", len(phases), job_id)
        return phases

    def _get_invoice_activities(self, job_id: str, soup: BeautifulSoup = None) -> dict:
        """Fetch key activities from the job detail page's activities table.

        Captures Invoice, Template, Install, and Contact Customer rows by phase.
        Returns {phase: {tp_code, sq_ft, invoice_date, invoice_status, template_date,
        install_date, contact_customer_date, contact_customer_notes, source}}.
        """
        if soup is None:
            url = f"{self.base_url}/sys/job/{job_id}"
            try:
                logger.info("GET %s (for invoice activities)", url)
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
            except requests.RequestException as e:
                logger.error("Failed to fetch job detail for invoice activities: %s", e)
                return {}
            soup = _make_soup(resp.text, prefer_lxml=True)
        table = soup.select_one("table#ActivitiesBody")
        if not table:
            logger.warning("No ActivitiesBody table found for job %s", job_id)
            return {}

        tp_col = None
        sq_ft_col = None
        notes_col = None
        for row in table.select("tr"):
            headers = row.select("td")
            if any("headerSortableCol" in (c.get("class") or []) for c in headers):
                for i, h in enumerate(headers):
                    label = h.get_text(strip=True).lower()
                    if "tp code" in label:
                        tp_col = i
                    elif "activity sqft" in label or "sq ft" in label or "sqft" in label:
                        sq_ft_col = i
                    elif "notes" in label:
                        notes_col = i
                break

        overrides = {}
        for row in table.select("tr"):
            cells = row.select("td")
            if len(cells) < 3:
                continue
            if any("headerSortableCol" in (c.get("class") or []) for c in cells):
                continue

            activity_name = cells[0].get_text(strip=True)
            if not activity_name:
                continue
            activity_lower = activity_name.lower()
            is_invoice = "invoice" in activity_lower
            is_template = "template" in activity_lower
            is_install = "install" in activity_lower
            is_contact_customer = "contact customer" in activity_lower
            if not (is_invoice or is_template or is_install or is_contact_customer):
                continue

            phase = cells[1].get_text(strip=True)
            if not phase:
                continue

            if phase not in overrides:
                overrides[phase] = {
                    "tp_code": None,
                    "sq_ft": None,
                    "template_date": None,
                    "install_date": None,
                    "contact_customer_date": None,
                    "contact_customer_notes": "",
                    "invoice_date": None,
                    "invoice_status": None,
                    "has_invoice_activity": False,
                    "source": "invoice_activity",
                }

            tp_code_raw = cells[tp_col].get_text(strip=True) if tp_col is not None and len(cells) > tp_col else ""
            tp_code = _parse_currency(tp_code_raw)

            sq_ft_raw = cells[sq_ft_col].get_text(strip=True) if sq_ft_col is not None and len(cells) > sq_ft_col else ""
            try:
                sq_ft = float(sq_ft_raw.replace(",", "").strip()) if sq_ft_raw else None
            except ValueError:
                sq_ft = None

            start_date = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            if start_date:
                start_date = "".join(c for c in start_date if c.isdigit() or c == "/")
            invoice_date = start_date if start_date else None

            raw_status = cells[2].get_text(strip=True).lower()
            invoice_status = "Complete" if "complete" in raw_status else "Pending"

            notes = cells[notes_col].get_text(strip=True) if notes_col is not None and len(cells) > notes_col else ""

            if is_invoice:
                overrides[phase]["has_invoice_activity"] = True
                overrides[phase]["tp_code"] = tp_code
                overrides[phase]["invoice_date"] = invoice_date
                overrides[phase]["invoice_status"] = invoice_status
                if sq_ft is not None:
                    overrides[phase]["sq_ft"] = sq_ft
                logger.debug(
                    "  Invoice activity %s: tp_code=%s date=%s status=%s sq_ft=%s",
                    phase, tp_code, invoice_date, invoice_status, sq_ft
                )
            elif is_template:
                overrides[phase]["template_date"] = invoice_date
            elif is_install:
                overrides[phase]["install_date"] = invoice_date
            elif is_contact_customer:
                overrides[phase]["contact_customer_date"] = invoice_date
                if notes:
                    overrides[phase]["contact_customer_notes"] = notes

        logger.info("Found %d invoice activity overrides for job %s", len(overrides), job_id)
        return overrides

    @staticmethod
    def _coerce_ymd(value) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        text = str(value).strip()
        if not text:
            return ""
        try:
            if "/" in text:
                parsed = datetime.strptime(text, "%m/%d/%Y")
                return parsed.strftime("%Y-%m-%d")
            parsed = datetime.fromisoformat(text[:10])
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            return text

    @staticmethod
    def _ymd_to_mdy(value: str | None) -> str | None:
        if not value:
            return None
        text = (value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text[:10])
            return parsed.strftime("%m/%d/%Y")
        except Exception:
            return text

    @staticmethod
    def _iter_custom_field_values(node: ET.Element) -> list[tuple[str, str]]:
        out = []
        for cf in node.findall(".//customField"):
            field_id = (cf.get("id", "") or "").strip()
            value = (cf.get("value", "") or "").strip()
            if not value:
                value = (cf.text or "").strip()
            if field_id:
                out.append((field_id, value))
        for cf in node.findall(".//jobCustomField"):
            field_id = (cf.get("id", "") or "").strip()
            value = (cf.get("value", "") or "").strip() or (cf.findtext("value", "") or "").strip()
            if not value:
                value = (cf.text or "").strip()
            if field_id:
                out.append((field_id, value))
        for cf in node.findall(".//jobActivityCustomField"):
            field_id = (cf.get("id", "") or "").strip()
            value = (cf.get("value", "") or "").strip() or (cf.findtext("value", "") or "").strip()
            if not value:
                value = (cf.text or "").strip()
            if field_id:
                out.append((field_id, value))
        for v in node.findall(".//customFieldValue"):
            field_id = (v.get("id", "") or "").strip()
            if not field_id:
                field_el = v.find("customField")
                if field_el is not None:
                    field_id = (field_el.get("id", "") or "").strip()
            value = (v.get("value", "") or "").strip()
            if not value:
                value = (v.findtext("value", "") or "").strip() or (v.text or "").strip()
            if field_id:
                out.append((field_id, value))
        return out

    def _extract_custom_field_value(self, node: ET.Element, target_id: str) -> str:
        for field_id, value in self._iter_custom_field_values(node):
            if field_id == str(target_id):
                return value
        return ""

    def _fetch_calendar_activity_ids(self, start_date=None, end_date=None, activity_type: int = 16) -> list[str]:
        """
        Discover invoice activity IDs from calendar index using API-first commands.

        This is the fast-path index step used before batched activity pulls.
        """
        # SDK schema for jobActivityQuery filter requires job/jobActivity/jobActivitySeries.
        # Date/type-only calendar discovery is not available in this tenant's API schema,
        # so the fast flow now uses a batched-per-job API query path directly.
        unique_ids: list[str] = []
        start_ymd = self._coerce_ymd(start_date)
        end_ymd = self._coerce_ymd(end_date)
        logger.info(
            "Fast sync calendar index found %d activity ids (activity_type=%s, start=%s, end=%s)",
            len(unique_ids),
            activity_type,
            start_ymd or "any",
            end_ymd or "any",
        )
        return unique_ids

    def _api_get_job_activities(self, activity_ids: list[str], batch_size: int = 250) -> list[dict]:
        """Fetch job activities in batches via API v5."""
        cleaned_ids = [str(a).strip() for a in (activity_ids or []) if str(a).strip()]
        if not cleaned_ids:
            return []

        results = []
        for i in range(0, len(cleaned_ids), max(1, int(batch_size or 250))):
            batch = cleaned_ids[i:i + max(1, int(batch_size or 250))]
            filter_xml = "".join(f'<jobActivity id="{escape(activity_id)}" />' for activity_id in batch)
            include_xml = (
                "<activityType><name /></activityType>"
                "<notes />"
                "<schedTime />"
                "<duration />"
                f'<jobActivityCustomField><id id="{_TP_CODE_ACTIVITY_FIELD_ID}" /></jobActivityCustomField>'
                "<jobActivitySeries />"
                "<assignee><all /></assignee>"
                "<jobPhase><all /></jobPhase>"
            )
            root = self._api_command("jobActivityQuery", f"<filter>{filter_xml}</filter><include>{include_xml}</include>")
            for el in root.findall(".//jobActivityQuery/jobActivity"):
                activity_id = (el.get("id", "") or "").strip()
                job_el = el.find("job")
                job_id = (job_el.get("id", "") if job_el is not None else "").strip()
                if not job_id and len(batch) == 1:
                    job_id = batch[0]

                activity_type_el = el.find("activityType")
                activity_type_name = (activity_type_el.findtext("name", "") if activity_type_el is not None else "").strip()

                status_el = el.find("status")
                status_name = (status_el.findtext("name", "") if status_el is not None else "").strip()

                phase_name = ""
                job_phases_node = el.find("jobPhases")
                if job_phases_node is not None:
                    phase_el = job_phases_node.find("jobPhase")
                    if phase_el is not None:
                        phase_name = (phase_el.findtext("name", "") or "").strip()
                if not phase_name:
                    phase_el = el.find("jobPhase")
                    if phase_el is not None:
                        phase_name = (phase_el.findtext("name", "") or "").strip()

                row = {
                    "activity_id": activity_id,
                    "job_id": job_id,
                    "activity_type": activity_type_name,
                    "status": status_name,
                    "start_date": (el.findtext("startDate", "") or "").strip(),
                    "notes": (el.findtext("notes", "") or "").strip(),
                    "phase": phase_name,
                    "tp_code": _parse_currency(self._extract_custom_field_value(el, _TP_CODE_ACTIVITY_FIELD_ID)),
                    "sq_ft": _parse_currency(self._extract_custom_field_value(el, _ACTIVITY_SQ_FT_FIELD_ID)),
                }
                results.append(row)
        logger.info("Fast sync fetched %d job activities across %d ids", len(results), len(cleaned_ids))
        return results

    def _api_get_job_activities_for_jobs(
        self,
        job_ids: list[str],
        start_date=None,
        end_date=None,
        batch_size: int = 60,
    ) -> list[dict]:
        """Fetch job activities in batches by job id and filter locally."""
        cleaned_ids = [str(j).strip() for j in (job_ids or []) if str(j).strip()]
        if not cleaned_ids:
            return []

        start_ymd = self._coerce_ymd(start_date)
        end_ymd = self._coerce_ymd(end_date)
        start_mdy = self._ymd_to_mdy(start_ymd) if start_ymd else None
        end_mdy = self._ymd_to_mdy(end_ymd) if end_ymd else None
        start_dt = datetime.strptime(start_mdy, "%m/%d/%Y").date() if start_mdy else None
        end_dt = datetime.strptime(end_mdy, "%m/%d/%Y").date() if end_mdy else None

        out: list[dict] = []
        for i in range(0, len(cleaned_ids), max(1, int(batch_size or 60))):
            batch = cleaned_ids[i:i + max(1, int(batch_size or 60))]
            filter_xml = "".join(f'<job id="{escape(job_id)}" />' for job_id in batch)
            include_xml = (
                "<activityType><name /></activityType>"
                "<notes />"
                "<schedTime />"
                "<duration />"
                f'<jobActivityCustomField><id id="{_TP_CODE_ACTIVITY_FIELD_ID}" /></jobActivityCustomField>'
                "<jobActivitySeries />"
                "<assignee><all /></assignee>"
                "<jobPhase><all /></jobPhase>"
            )
            try:
                root = self._api_command("jobActivityQuery", f"<filter>{filter_xml}</filter><include>{include_xml}</include>")
            except Exception:
                # Some tenants reject jobPhase include; retry without it.
                include_xml = (
                    "<activityType><name /></activityType>"
                    "<notes />"
                    "<schedTime />"
                    "<duration />"
                    f'<jobActivityCustomField><id id="{_TP_CODE_ACTIVITY_FIELD_ID}" /></jobActivityCustomField>'
                    "<jobActivitySeries />"
                    "<assignee><all /></assignee>"
                )
                root = self._api_command("jobActivityQuery", f"<filter>{filter_xml}</filter><include>{include_xml}</include>")

            for el in root.findall(".//jobActivityQuery/jobActivity"):
                activity_type_name = (el.findtext("activityType/name", "") or "").strip()
                if "invoice" not in activity_type_name.lower() and "template" not in activity_type_name.lower() \
                        and "install" not in activity_type_name.lower() and "contact customer" not in activity_type_name.lower():
                    continue

                start_date_val = (el.findtext("startDate", "") or "").strip()
                if start_date_val and (start_dt or end_dt):
                    try:
                        row_dt = datetime.strptime(start_date_val, "%m/%d/%Y").date()
                    except Exception:
                        row_dt = None
                    if row_dt is not None:
                        if start_dt and row_dt < start_dt:
                            continue
                        if end_dt and row_dt > end_dt:
                            continue

                phase_name = (el.findtext("jobPhase/name", "") or "").strip()
                status_name = (el.findtext("status/name", "") or "").strip()
                job_el = el.find("job")
                job_id = (job_el.get("id", "") if job_el is not None else "").strip()

                out.append(
                    {
                        "activity_id": (el.get("id", "") or "").strip(),
                        "job_id": job_id,
                        "activity_type": activity_type_name,
                        "status": status_name,
                        "start_date": start_date_val,
                        "notes": (el.findtext("notes", "") or "").strip(),
                        "phase": phase_name,
                        "tp_code": _parse_currency(self._extract_custom_field_value(el, _TP_CODE_ACTIVITY_FIELD_ID)),
                        "sq_ft": _parse_currency(self._extract_custom_field_value(el, _ACTIVITY_SQ_FT_FIELD_ID)),
                    }
                )
        logger.info("Fast sync fetched %d job activities across %d jobs", len(out), len(cleaned_ids))
        return out

    def _api_get_jobs_metadata(self, job_ids: list[str], batch_size: int = 200) -> dict[str, dict]:
        """Fetch job metadata in batches via API v5."""
        cleaned_ids = [str(j).strip() for j in (job_ids or []) if str(j).strip()]
        if not cleaned_ids:
            return {}

        out: dict[str, dict] = {}
        for i in range(0, len(cleaned_ids), max(1, int(batch_size or 200))):
            batch = cleaned_ids[i:i + max(1, int(batch_size or 200))]
            filter_xml = "".join(f'<job id="{escape(job_id)}" />' for job_id in batch)
            include_xml = (
                "<name />"
                "<jobStatus />"
                "<creationDate />"
                "<salesperson><name /></salesperson>"
                f'<jobCustomField><id id="{_JOB_NUMBER_FIELD_ID}" /></jobCustomField>'
            )
            root = self._api_command("jobQuery", f"<filter>{filter_xml}</filter><include>{include_xml}</include>")
            for el in root.findall(".//jobQuery/job"):
                job_id = (el.get("id", "") or "").strip()
                if not job_id:
                    continue
                raw_status = (el.get("jobStatus", "") or "").strip()
                status_text = "Complete" if "complete" in raw_status.lower() else ("Active" if raw_status else "")
                out[job_id] = {
                    "job_name": (el.findtext("name", "") or "").strip(),
                    "job_number": self._extract_custom_field_value(el, _JOB_NUMBER_FIELD_ID),
                    "created_date": (el.findtext("creationDate", "") or "").strip(),
                    "salesperson": (el.findtext("salesperson/name", "") or "").strip(),
                    "project_manager": "",
                    "status": status_text,
                }
        logger.info("Fast sync fetched metadata for %d jobs", len(out))
        return out

    def sync_invoice_data_fast(self, linked_jobs, start_date=None, end_date=None, progress_cb=None) -> dict:
        """
        Bulk invoice sync API-first flow with legacy fallback safety.

        Returns:
          {
            "rows_by_job_id": dict[str, list[dict]],
            "meta_by_job_id": dict[str, dict],
            "issues": list[dict],
            "stats": dict,
          }
        """
        t0 = time.perf_counter()
        rows_by_job_id: dict[str, list[dict]] = {}
        meta_by_job_id: dict[str, dict] = {}
        issues: list[dict] = []
        linked_list = list(linked_jobs or [])
        job_ids = []
        for item in linked_list:
            if isinstance(item, dict):
                jid = str(item.get("moraware_job_id") or item.get("job_id") or "").strip()
            else:
                jid = str(item or "").strip()
            if jid and jid not in job_ids:
                job_ids.append(jid)

        if not job_ids:
            return {
                "rows_by_job_id": {},
                "meta_by_job_id": {},
                "issues": [],
                "stats": {"jobs_total": 0, "elapsed_ms": 0, "fast_enabled": self.use_fast_sync},
            }

        if not self.use_fast_sync:
            for idx, job_id in enumerate(job_ids, start=1):
                if callable(progress_cb):
                    progress_cb(idx, len(job_ids))
                try:
                    rows_by_job_id[job_id] = self.get_invoice_data(job_id)
                    details = self.get_job_details(job_id)
                    details["status"] = self.get_job_status(job_id) or details.get("status", "")
                    meta_by_job_id[job_id] = details
                except Exception as e:
                    issues.append({"job_id": job_id, "reason": "legacy_fallback_failed", "error": str(e)})
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            return {
                "rows_by_job_id": rows_by_job_id,
                "meta_by_job_id": meta_by_job_id,
                "issues": issues,
                "stats": {
                    "jobs_total": len(job_ids),
                    "jobs_with_rows": sum(1 for rows in rows_by_job_id.values() if rows),
                    "activity_ids_found": 0,
                    "rows_kept": sum(len(rows) for rows in rows_by_job_id.values()),
                    "fallback_hits": len(job_ids),
                    "elapsed_ms": elapsed_ms,
                    "fast_enabled": False,
                },
            }

        activity_ids = []
        try:
            activity_ids = self._fetch_calendar_activity_ids(start_date=start_date, end_date=end_date, activity_type=16)
        except Exception as e:
            issues.append({"reason": "calendar_index_failed", "error": str(e)})

        activities = []
        try:
            if activity_ids:
                activities = self._api_get_job_activities(activity_ids)
            else:
                activities = self._api_get_job_activities_for_jobs(
                    job_ids=job_ids,
                    start_date=start_date,
                    end_date=end_date,
                    batch_size=1,
                )
        except Exception as e:
            issues.append({"reason": "activity_batch_fetch_failed", "error": str(e)})

        try:
            meta_by_job_id = self._api_get_jobs_metadata(job_ids)
        except Exception as e:
            issues.append({"reason": "job_metadata_fetch_failed", "error": str(e)})
            meta_by_job_id = {}

        activities_by_job: dict[str, list[dict]] = {}
        for act in activities:
            job_id = str(act.get("job_id") or "").strip()
            if not job_id or job_id not in job_ids:
                continue
            activities_by_job.setdefault(job_id, []).append(act)

        fallback_hits = 0
        rows_kept = 0
        for idx, job_id in enumerate(job_ids, start=1):
            if callable(progress_cb):
                progress_cb(idx, len(job_ids))
            phase_rows = {}

            for act in activities_by_job.get(job_id, []):
                activity_type = (act.get("activity_type") or "").strip()
                lower_type = activity_type.lower()
                is_invoice = "invoice" in lower_type
                is_template = "template" in lower_type
                is_install = "install" in lower_type
                is_contact_customer = "contact customer" in lower_type
                if not (is_invoice or is_template or is_install or is_contact_customer):
                    continue

                status_name = (act.get("status") or "").strip().lower()
                if is_invoice and "cancel" in status_name:
                    continue

                phase = (act.get("phase") or "").strip()
                if not phase:
                    issues.append(
                        {
                            "job_id": job_id,
                            "activity_id": act.get("activity_id"),
                            "reason": "missing_phase",
                        }
                    )
                    continue

                if phase not in phase_rows:
                    phase_rows[phase] = {
                        "phase": phase,
                        "tp_code": None,
                        "sq_ft": None,
                        "invoice_date": None,
                        "template_date": None,
                        "install_date": None,
                        "contact_customer_date": None,
                        "contact_customer_notes": "",
                        "invoice_status": "Pending",
                        "source": "job_activity_api",
                    }

                start_date_mdy = self._ymd_to_mdy(act.get("start_date"))
                if is_invoice:
                    if act.get("tp_code") not in (None, ""):
                        phase_rows[phase]["tp_code"] = act.get("tp_code")
                        phase_rows[phase]["source"] = "invoice_activity"
                    if act.get("sq_ft") not in (None, ""):
                        phase_rows[phase]["sq_ft"] = act.get("sq_ft")
                    phase_rows[phase]["invoice_date"] = start_date_mdy
                    phase_rows[phase]["invoice_status"] = "Complete" if "complete" in status_name else "Pending"
                elif is_template:
                    phase_rows[phase]["template_date"] = start_date_mdy
                elif is_install:
                    phase_rows[phase]["install_date"] = start_date_mdy
                elif is_contact_customer:
                    phase_rows[phase]["contact_customer_date"] = start_date_mdy
                    if (act.get("notes") or "").strip():
                        phase_rows[phase]["contact_customer_notes"] = (act.get("notes") or "").strip()

            needs_tp_fallback = any(v.get("tp_code") in (None, "") for v in phase_rows.values())
            if not phase_rows:
                try:
                    legacy_rows = self.get_invoice_data(job_id)
                    rows_by_job_id[job_id] = legacy_rows
                    rows_kept += len(legacy_rows)
                    fallback_hits += 1
                except Exception as e:
                    issues.append({"job_id": job_id, "reason": "legacy_rows_fallback_failed", "error": str(e)})
                    rows_by_job_id[job_id] = []
                meta = meta_by_job_id.get(job_id) or {}
                if not (meta.get("job_number") or "").strip():
                    try:
                        details = self.get_job_details(job_id)
                    except Exception:
                        details = {}
                    meta_by_job_id[job_id] = {
                        "job_name": (meta.get("job_name") or "").strip(),
                        "job_number": (meta.get("job_number") or details.get("job_number") or "").strip(),
                        "created_date": (meta.get("created_date") or details.get("created_date") or "").strip(),
                        "salesperson": (meta.get("salesperson") or details.get("salesperson") or "").strip(),
                        "project_manager": (meta.get("project_manager") or details.get("project_manager") or "").strip(),
                        "status": (meta.get("status") or "").strip(),
                    }
                continue

            if not phase_rows or needs_tp_fallback:
                try:
                    fallback_phases = self._get_job_ticket_a_phases(job_id)
                except Exception as e:
                    fallback_phases = {}
                    issues.append({"job_id": job_id, "reason": "job_ticket_a_fallback_failed", "error": str(e)})
                if fallback_phases:
                    fallback_hits += 1
                for phase_name, fp in fallback_phases.items():
                    if phase_name not in phase_rows:
                        phase_rows[phase_name] = {
                            "phase": phase_name,
                            "tp_code": fp.get("tp_code"),
                            "sq_ft": fp.get("sq_ft"),
                            "invoice_date": fp.get("invoice_date"),
                            "template_date": fp.get("template_date"),
                            "install_date": fp.get("install_date"),
                            "contact_customer_date": fp.get("contact_customer_date"),
                            "contact_customer_notes": fp.get("contact_customer_notes", ""),
                            "invoice_status": fp.get("invoice_status", "Pending"),
                            "source": "job_ticket_a",
                        }
                    elif phase_rows[phase_name].get("tp_code") in (None, "") and fp.get("tp_code") not in (None, ""):
                        phase_rows[phase_name]["tp_code"] = fp.get("tp_code")
                        if phase_rows[phase_name].get("source") != "invoice_activity":
                            phase_rows[phase_name]["source"] = "job_ticket_a"
                    if phase_rows[phase_name].get("sq_ft") in (None, "") and fp.get("sq_ft") not in (None, ""):
                        phase_rows[phase_name]["sq_ft"] = fp.get("sq_ft")

            rows = [phase_rows[k] for k in sorted(phase_rows.keys())]
            rows_by_job_id[job_id] = rows
            rows_kept += len(rows)
            if job_id not in meta_by_job_id:
                meta_by_job_id[job_id] = {
                    "job_name": "",
                    "job_number": "",
                    "created_date": "",
                    "salesperson": "",
                    "project_manager": "",
                    "status": "",
                }

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "rows_by_job_id": rows_by_job_id,
            "meta_by_job_id": meta_by_job_id,
            "issues": issues,
            "stats": {
                "jobs_total": len(job_ids),
                "jobs_with_rows": sum(1 for rows in rows_by_job_id.values() if rows),
                "activity_ids_found": len(activity_ids),
                "rows_kept": rows_kept,
                "fallback_hits": fallback_hits,
                "elapsed_ms": elapsed_ms,
                "fast_enabled": True,
            },
        }

    def get_live_reference_totals(self, job_ids, start_date=None, end_date=None) -> dict[str, dict]:
        """
        Live-fetch TP/SF reference totals for job IDs without DB writes.

        Returns:
          {
            "<job_id>": {
              "reference_tp_total": float,
              "reference_sq_ft_total": float,
              "job_name": str,
              "job_number": str,
              "source": "live"
            }
          }
        """
        cleaned = []
        for raw in job_ids or []:
            jid = str(raw or "").strip()
            if jid and jid not in cleaned:
                cleaned.append(jid)
        if not cleaned:
            return {}

        result = self.sync_invoice_data_fast(
            linked_jobs=[{"moraware_job_id": jid} for jid in cleaned],
            start_date=start_date,
            end_date=end_date,
            progress_cb=None,
        )
        rows_by_job_id = result.get("rows_by_job_id", {}) or {}
        meta_by_job_id = result.get("meta_by_job_id", {}) or {}

        out: dict[str, dict] = {}
        for jid in cleaned:
            rows = rows_by_job_id.get(jid, []) or []
            tp_total = 0.0
            sq_total = 0.0
            for row in rows:
                try:
                    tp_total += float((row or {}).get("tp_code") or 0)
                except Exception:
                    pass
                try:
                    sq_total += float((row or {}).get("sq_ft") or 0)
                except Exception:
                    pass
            meta = meta_by_job_id.get(jid) or {}
            out[jid] = {
                "reference_tp_total": float(tp_total),
                "reference_sq_ft_total": float(sq_total),
                "job_name": str(meta.get("job_name") or "").strip(),
                "job_number": str(meta.get("job_number") or "").strip(),
                "source": "live",
            }
        return out

    def get_job_status(self, job_id: str) -> str:
        """Read job status via API v5 jobQuery and normalize to Active/Complete."""
        try:
            root = self._api_command(
                "jobQuery",
                f'<filter><job id="{escape(str(job_id))}" /></filter><include><jobStatus /></include>',
            )
            job_el = root.find(".//jobQuery/job")
            if job_el is None:
                return ""

            raw_status = (job_el.get("jobStatus", "") or "").strip()
            if not raw_status:
                return ""
            return "Complete" if "complete" in raw_status.lower() else "Active"
        except Exception as e:
            logger.warning("get_job_status API call failed for job %s: %s", job_id, e)
            return ""


def _parse_currency(val: str):
    """Parse a currency string like '$3,206.00' into a float, or None."""
    if not val:
        return None
    cleaned = val.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None
