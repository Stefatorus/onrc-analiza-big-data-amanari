import argparse
import json
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from downloadBulletinsSafe import PoliteClient, Blocked, TokenExpired, SlowResponse, INITIAL_PAUSE, MAX_PAUSE, MAX_TRIPS

CLIENT_URL = "https://api.berc.onrc.ro/client/api"
BACKOFFICE_URL = "https://api.berc.onrc.ro/backoffice/api"
REQUEST_TIMEOUT = 180  # large pages take ~10s server side
RETRY_PAGE_SIZE = 200  # deferred (slow) items are retried at the end with lighter pages
OVERLOAD_STREAK, OVERLOAD_PAUSE = 4, 300  # short breather after several slow queries in a row
# Categories holding registration decisions; the rest are rare publicity notices
DECISION_CATEGORIES = "CERERE265,INMATRIC265,AUTO_AMANARI,CERERE_HJ265"

stop_event = threading.Event()
breaker = {"pause": INITIAL_PAUSE, "trips": MAX_TRIPS}  # overridable from the command line
slow = {"streak": 0}
deferred = []
deferred_lock = threading.Lock()


class Deferred(Exception):
    """A query the server answers too slowly; skipped now and retried at the end of the run."""


def server_alive(client):
    try:
        client.request("GET", f"{BACKOFFICE_URL}/health", timeout=20)
        return True
    except (Blocked, SlowResponse):
        return False


def window_model(start, end):
    # Note: the API returns articles published the day AFTER this window; publishedAt is the true date
    return {
        "county": {"id": "", "name": "", "siruta": ""},
        "fiscalCode": "",
        "applicationNumber": "",
        "applicationYear": "",
        "name": "",
        "listType": "notAll",
        "startDate": f"{start.isoformat()}T00:00:00.000Z",
        "endDate": f"{end.isoformat()}T23:59:59.999Z",
    }


def with_breaker(client, func):
    """Retry func through block-like failures, pausing every thread in between."""
    pause = breaker["pause"]
    for trip in range(1, breaker["trips"] + 1):
        if stop_event.is_set():
            raise Blocked("Stopped")
        try:
            result = func()
            slow["streak"] = 0
            return result
        except SlowResponse as e:
            if server_alive(client):
                slow["streak"] += 1
                if slow["streak"] >= OVERLOAD_STREAK:
                    logging.warning(f"{slow['streak']} slow queries in a row; short {OVERLOAD_PAUSE // 60} min breather")
                    client.pause_all(OVERLOAD_PAUSE)
                    slow["streak"] = 0
                raise Deferred(str(e))
            logging.warning(f"Looks blocked (slow query and health check failed). Pausing all workers {pause // 60} min (trip {trip}/{breaker['trips']})")
            client.pause_all(pause)
            pause = min(pause * 2, max(MAX_PAUSE, breaker["pause"] * 2))
        except Blocked as e:
            logging.warning(f"Looks blocked ({e}). Pausing all workers {pause // 60} min (trip {trip}/{breaker['trips']})")
            client.pause_all(pause)
            pause = min(pause * 2, max(MAX_PAUSE, breaker["pause"] * 2))
    raise Blocked(f"Gave up after {breaker['trips']} trips")


def get_categories(client, start, end):
    response = client.request("POST", f"{CLIENT_URL}/publicitySituations", headers=client.api_headers(),
                              json=window_model(start, end), timeout=REQUEST_TIMEOUT)
    return response.json()


def categories_from_disk(output_dir):
    """Category ids from already-saved articles, so no expensive lookup is needed."""
    found = {}
    for name in os.listdir(output_dir):
        identifier = name[11:-5] if name.endswith(".json") else None
        if not identifier or identifier in found:
            continue
        with open(os.path.join(output_dir, name), encoding="utf-8") as f:
            articles = json.load(f)
        if articles and articles[0].get("publicitySituation"):
            found[identifier] = articles[0]["publicitySituation"]
    return list(found.values())


def get_page(client, day, publicity_id, page, page_size):
    model = dict(window_model(day, day), publicityId=publicity_id)
    response = client.request("POST", f"{BACKOFFICE_URL}/article/filter-article", headers=client.api_headers(),
                              params={"all": "notAll", "page": page, "pageSize": page_size},
                              json=model, timeout=REQUEST_TIMEOUT)
    return response.json(), int(response.headers.get("X-Total-Count") or 0)


def crawl_day(client, day, output_dir, page_size, categories, mark_done):
    if categories is None:
        categories = with_breaker(client, lambda: get_categories(client, day, day))
    day_deferred = False
    for category in categories:
        try:
            crawl_category(client, day, category, output_dir, page_size)
        except Deferred as e:
            day_deferred = True
            logging.warning(f"{day} {category['identifier']}: slow response, deferred to end of run ({e})")
            with deferred_lock:
                deferred.append((day, category))
    if mark_done and not day_deferred:
        # Marks the day as fully checked, so "no file" for a small category means "none published", not "not tried"
        with open(os.path.join(output_dir, f"{day.isoformat()}_ALLDAY.done"), "w") as f:
            f.write(",".join(c["identifier"] for c in categories))


def crawl_category(client, day, category, output_dir, page_size):
    output_path = os.path.join(output_dir, f"{day.isoformat()}_{category['identifier']}.json")
    if os.path.exists(output_path):
        return

    articles = {}
    page, total = 0, None
    while total is None or page * page_size < total:
        batch, total = with_breaker(client, lambda: get_page(client, day, category["id"], page, page_size))
        for article in batch:
            articles[article["id"]] = article
        if not batch:
            break
        page += 1

    if len(articles) != total:
        logging.warning(f"{day} {category['identifier']}: got {len(articles)} unique of {total} reported")
    tmp_path = output_path + ".part"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(list(articles.values()), f, ensure_ascii=False)
    os.replace(tmp_path, output_path)
    logging.info(f"{day} {category['identifier']}: {len(articles)} articles in {page} pages")


def crawl_day_safe(client, day, output_dir, page_size, categories, mark_done):
    if stop_event.is_set():
        return
    try:
        crawl_day(client, day, output_dir, page_size, categories, mark_done)
    except TokenExpired:
        logging.error(f"Token expired or rejected at {day}. Rerun with a fresh token to resume.")
        stop_event.set()
    except Blocked as e:
        logging.error(f"Stopping at {day}: {e}")
        stop_event.set()
    except Deferred:
        logging.warning(f"{day}: category lookup too slow; day skipped, rerun to retry")
    except Exception:
        logging.exception(f"Unexpected error at {day}; skipping, rerun to retry")


def main():
    parser = argparse.ArgumentParser(description="Bulk BERC article crawler by publication day")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--reverse", action="store_true", help="Crawl newest days first")
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument("--rate", type=float, default=0.5, help="Max requests per second, shared by all workers")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--categories", default=DECISION_CATEGORIES,
                        help="Comma-separated category identifiers, 'known' for every category already saved in "
                             "--categories-from (no slow per-day lookup), or 'all' to look them up per day")
    parser.add_argument("--out", default="results/articles")
    parser.add_argument("--categories-from", help="Folder of saved articles to read category ids from (default: --out)")
    parser.add_argument("--pause-min", type=float, help="Minutes to pause all workers after a block-like failure")
    parser.add_argument("--max-trips", type=int, help="Consecutive block-like failures before stopping")
    parser.add_argument("--token-file", required=True)
    parser.add_argument("--log")
    args = parser.parse_args()
    if args.pause_min:
        breaker["pause"] = int(args.pause_min * 60)
    if args.max_trips:
        breaker["trips"] = args.max_trips

    handlers = [logging.StreamHandler(sys.stdout)]
    if args.log:
        handlers.append(logging.FileHandler(args.log, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=handlers)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    with open(args.token_file) as f:
        client = PoliteClient(f.read().strip(), args.rate)

    categories = None
    mark_done = args.categories in ("all", "known")
    if args.categories == "known":
        categories = categories_from_disk(args.categories_from or args.out)
        logging.info(f"Crawling {len(categories)} known categories: {[c['identifier'] for c in categories]}")
    elif args.categories != "all":
        wanted = args.categories.split(",")
        source = args.categories_from or args.out
        known = categories_from_disk(source) if os.path.isdir(source) else []
        if not set(wanted) <= {c["identifier"] for c in known}:
            # A single-week lookup; a whole-year window times out server side
            known = with_breaker(client, lambda: get_categories(client, args.end - timedelta(days=6), args.end))
        categories = [c for c in known if c["identifier"] in wanted]
        missing = set(wanted) - {c["identifier"] for c in categories}
        if missing:
            logging.warning(f"Categories not found for this range: {missing}")
        logging.info(f"Crawling categories: {[c['identifier'] for c in categories]}")

    days = [args.start + timedelta(days=i) for i in range((args.end - args.start).days + 1)]
    if args.reverse:
        days.reverse()
    os.makedirs(args.out, exist_ok=True)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for day in days:
            executor.submit(crawl_day_safe, client, day, args.out, args.page_size, categories, mark_done)

    # Second pass over the slow items, one at a time with lighter pages; anything still failing is left for a rerun
    if deferred and not stop_event.is_set():
        logging.info(f"Retrying {len(deferred)} deferred items with {RETRY_PAGE_SIZE}-record pages")
        for day, category in sorted(deferred, key=lambda x: x[0], reverse=args.reverse):
            if stop_event.is_set():
                break
            try:
                crawl_category(client, day, category, args.out, RETRY_PAGE_SIZE)
            except Deferred:
                logging.warning(f"{day} {category['identifier']}: still slow; left for a later rerun")
            except TokenExpired:
                logging.error("Token expired or rejected during retries. Rerun with a fresh token to resume.")
                stop_event.set()
            except Blocked as e:
                logging.error(f"Stopping retries: {e}")
                stop_event.set()
    logging.info("Done" if not stop_event.is_set() else "Stopped early (block or token); rerun to resume")
    sys.exit(2 if stop_event.is_set() else 0)


if __name__ == "__main__":
    main()
