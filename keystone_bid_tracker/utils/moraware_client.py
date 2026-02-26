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
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import requests
from urllib.parse import urlparse
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


JOB_DETAIL_LABELS = {
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


class MorewareClient:
    """Connects to Moraware via web session and XML API."""

    MORAWARE_CUID = 29  # Moraware instance customer ID, used in AJAX form requests

    def __init__(self, username: str, password: str, base_url: str, timeout: int = 15):
        self.username = username
        self.password = password
        self.timeout = timeout
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
                soup = BeautifulSoup(resp.text, "html.parser")
                err = soup.select_one(".error, .alert-danger, .login-error, .minimalPageMessage")
                msg = err.get_text(strip=True) if err and err.get_text(strip=True) else "Invalid credentials"
                raise ConnectionError(f"Login failed: {msg}")

            logger.info("Login successful")
            return True
        except requests.RequestException as e:
            raise ConnectionError(f"Could not connect to Moraware: {e}")

    @staticmethod
    def _page_has_login_form(html: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        return bool(soup.select_one("input[type='password']"))

    @staticmethod
    def _detect_form_fields(html: str, page_url: str = "") -> dict:
        """Parse the login form to find actual input field names and action URL."""
        soup = BeautifulSoup(html, "html.parser")

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

            soup = BeautifulSoup(resp.text, "html.parser")
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
        """Fetch job created date, salesperson, and PM by scraping the job detail page.

        Returns dict with keys: created_date, salesperson, project_manager, status.
        """
        result = {"created_date": "", "salesperson": "", "project_manager": "", "status": ""}

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

        soup = BeautifulSoup(resp.text, "html.parser")

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

        soup = BeautifulSoup(resp.text, "html.parser")

        phases = self._get_job_ticket_a_phases(job_id)
        invoice_overrides = self._get_invoice_activities(job_id, soup)

        for phase_key, inv_data in invoice_overrides.items():
            if phase_key not in phases:
                phases[phase_key] = {
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
            if inv_data.get("tp_code") is not None and inv_data["tp_code"] != "":
                if phase_key in phases:
                    phases[phase_key]["tp_code"] = inv_data["tp_code"]
                    phases[phase_key]["source"] = "invoice_activity"
                phases[phase_key]["invoice_date"] = inv_data.get("invoice_date")
                phases[phase_key]["invoice_status"] = inv_data.get("invoice_status", "Pending")
            elif phase_key in phases:
                phases[phase_key]["invoice_date"] = inv_data.get("invoice_date")
                phases[phase_key]["invoice_status"] = inv_data.get("invoice_status", "Pending")

            if phase_key in phases:
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
        soup = BeautifulSoup(resp.text, "html.parser")

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

            form_soup = BeautifulSoup(form_resp.text, "html.parser")

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
            soup = BeautifulSoup(resp.text, "html.parser")
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
                    "invoice_status": "Pending",
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
