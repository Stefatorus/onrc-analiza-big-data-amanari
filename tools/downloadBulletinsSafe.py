import argparse
import base64
import json
import logging
import os
import random
import re
import sys
import threading
import time

import requests

API_URL = "https://api.berc.onrc.ro/backoffice/api/publication"
DMS_URL = "https://dms.berc.onrc.ro"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

# Circuit breaker: on a block-like failure pause everything, then probe once
INITIAL_PAUSE = 300  # seconds
MAX_PAUSE = 3600
MAX_TRIPS = 6  # consecutive trips without a success before giving up
TOKEN_EXPIRY_MARGIN = 120  # stop this many seconds before the token expires


class Blocked(Exception):
    """Raised for failures that look like rate limiting / firewall blocks."""


class TokenExpired(Exception):
    pass


class SlowResponse(Exception):
    """Connected, but the server did not answer in time: a heavy query, not necessarily a block."""


class PoliteClient:
    """Single shared session with a global rate limit and a circuit breaker."""

    def __init__(self, token, rate):
        self.token = token
        self.min_interval = 1.0 / rate
        self.last_request = 0.0
        self.blocked_until = 0.0  # shared pause, so one blocked thread stops all of them
        self.lock = threading.Lock()
        self._local = threading.local()
        self.token_exp = self._token_expiry(token)

    @property
    def session(self):
        # One keep-alive session per thread; requests.Session is not thread-safe
        if not hasattr(self._local, "session"):
            self._local.session = requests.Session()
            self._local.session.headers.update({"User-Agent": USER_AGENT})
        return self._local.session

    def pause_all(self, seconds):
        with self.lock:
            self.blocked_until = max(self.blocked_until, time.time() + seconds)

    @staticmethod
    def _token_expiry(token):
        try:
            payload = token.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            return json.loads(base64.urlsafe_b64decode(payload))["exp"]
        except Exception:
            return None

    def _wait_turn(self):
        if self.token_exp and time.time() > self.token_exp - TOKEN_EXPIRY_MARGIN:
            raise TokenExpired()
        while time.time() < self.blocked_until:
            time.sleep(min(5, self.blocked_until - time.time()))
        with self.lock:
            # Jitter keeps the traffic from looking like a fixed-interval bot
            delay = self.last_request + self.min_interval * random.uniform(0.8, 1.4) - time.time()
            if delay > 0:
                time.sleep(delay)
            self.last_request = time.time()

    def request(self, method, url, **kwargs):
        self._wait_turn()
        kwargs.setdefault("timeout", 30)
        try:
            response = self.session.request(method, url, **kwargs)
        except requests.exceptions.ReadTimeout as e:
            raise SlowResponse(f"{type(e).__name__}: {e}")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            raise Blocked(f"{type(e).__name__}: {e}")
        if response.status_code == 401:
            raise TokenExpired()
        if response.status_code in (403, 429) or response.status_code >= 500:
            retry_after = response.headers.get("Retry-After")
            raise Blocked(f"HTTP {response.status_code} (Retry-After: {retry_after})")
        response.raise_for_status()
        return response

    def api_headers(self):
        return {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://portal.berc.onrc.ro",
            "Referer": "https://portal.berc.onrc.ro/",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }


def get_publication_info(client, year, number):
    response = client.request("POST", f"{API_URL}/getPublicationByYearAndNumber",
                              headers=client.api_headers(), json={"number": number, "year": year})
    if not response.text.strip():
        return None
    data = response.json()
    if isinstance(data, list):
        return data[0] if data else None
    return data or None


def get_download_link(client, version_id):
    response = client.request("POST", f"{API_URL}/viewPublication",
                              headers=client.api_headers(), json={"documentId": version_id, "type": "BULETIN"})
    return response.json().get("downloadLink")


def download_pdf(client, download_link, output_path):
    page = client.request("GET", download_link)
    match = re.search(r"util\.getCSRF\s*=\s*function\s*\(\)\s*{\s*return\s*'([^']+)';", page.text)
    if not match:
        logging.warning("No CSRF token on DMS page")
        return False
    temp_token = download_link.split("token=")[1].split("&")[0]
    file_response = client.request(
        "POST", f"{DMS_URL}/download_file",
        data={"X-CSRF-Token": match.group(1), "tempToken": temp_token, "location": "FILE", "nullContentType": "false"},
        headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": download_link},
    )
    if "application/pdf" not in file_response.headers.get("Content-Type", "").lower():
        logging.warning(f"Not a PDF: {file_response.headers.get('Content-Type')}")
        return False
    tmp_path = output_path + ".part"
    with open(tmp_path, "wb") as f:
        f.write(file_response.content)
    os.replace(tmp_path, output_path)
    return True


def process_bulletin(client, year, number, output_dir):
    info = get_publication_info(client, year, number)
    if not info:
        return "missing"
    link = get_download_link(client, info["versionId"])
    if not link:
        logging.warning(f"No download link for {year}/{number}")
        return "failed"
    return "ok" if download_pdf(client, link, os.path.join(output_dir, f"{number}.pdf")) else "failed"


def run(client, year, numbers, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    existing = {int(f[:-4]) for f in os.listdir(output_dir) if f.endswith(".pdf") and f[:-4].isdigit()}
    todo = [n for n in numbers if n not in existing]
    logging.info(f"{len(todo)} bulletins to fetch ({len(numbers) - len(todo)} already present)")

    counts = {"ok": 0, "missing": 0, "failed": 0}
    pause = INITIAL_PAUSE
    trips = 0
    started = time.time()
    i = 0
    while i < len(todo):
        number = todo[i]
        try:
            result = process_bulletin(client, year, number, output_dir)
        except Blocked as e:
            trips += 1
            if trips > MAX_TRIPS:
                logging.error(f"Blocked {trips} times in a row, giving up at {year}/{number}: {e}")
                break
            logging.warning(f"Looks blocked at {year}/{number} ({e}). Pausing {pause // 60} min (trip {trips}/{MAX_TRIPS})")
            time.sleep(pause)
            pause = min(pause * 2, MAX_PAUSE)
            continue  # retry the same bulletin as the probe
        except TokenExpired:
            logging.error(f"Token expired or rejected at {year}/{number}. Rerun with a fresh token to resume.")
            break
        except SlowResponse as e:
            logging.warning(f"Slow response for {year}/{number}, skipping for now: {e}")
            counts["failed"] += 1
            i += 1
            continue
        except Exception:
            logging.exception(f"Unexpected error at {year}/{number}; skipping, rerun to retry")
            counts["failed"] += 1
            i += 1
            continue

        trips = 0
        pause = INITIAL_PAUSE
        counts[result] += 1
        i += 1
        if i % 50 == 0:
            rate = i / (time.time() - started) * 3600
            logging.info(f"Progress {i}/{len(todo)} | {counts} | {rate:.0f} bulletins/hour | last {year}/{number}")

    logging.info(f"Finished: {counts}, {len(todo) - i} left")


def main():
    parser = argparse.ArgumentParser(description="Rate-limited BERC bulletin downloader")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    parser.add_argument("--numbers-file", help="File with one bulletin number per line (instead of --start/--end)")
    parser.add_argument("--step", type=int, default=1, help="Take every Nth bulletin (sampling pass)")
    parser.add_argument("--offset", type=int, default=0, help="Offset within each step, to fill gaps later")
    parser.add_argument("--reverse", action="store_true", help="Fetch newest bulletins first")
    parser.add_argument("--rate", type=float, default=1.0, help="Max requests per second across all hosts")
    parser.add_argument("--out", default="bulletins")
    parser.add_argument("--token-file", required=True)
    parser.add_argument("--log")
    args = parser.parse_args()

    handlers = [logging.StreamHandler(sys.stdout)]
    if args.log:
        handlers.append(logging.FileHandler(args.log, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=handlers)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    with open(args.token_file) as f:
        client = PoliteClient(f.read().strip(), args.rate)

    if args.numbers_file:
        numbers = [int(line) for line in open(args.numbers_file) if line.strip()]
    else:
        numbers = [n for n in range(args.start, args.end + 1) if (n - args.start) % args.step == args.offset]
    if args.reverse:
        numbers.reverse()
    run(client, args.year, numbers, os.path.join(args.out, str(args.year)))


if __name__ == "__main__":
    main()
