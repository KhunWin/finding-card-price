"""
=============================================================================
  YUYU-TEI RATE LIMIT TEST
=============================================================================

PURPOSE
-------
Find the practical request limits of yuyu-tei.jp so the main scraper never
hits them during real runs.

TEST PLAN
---------
The website has two distinct request surfaces:

  A)  Search page  – /sell/<ws>/s/search?vers[]=<group>
      Returns a listing of all cards in one group.

  B)  Card detail  – /sell/<ws>/card/<game>/<id>
      One page per card (data + image URL live here).

  C)  Image CDN    – image URLs embedded in each detail page.
      Separate host; tracked independently.

WHAT WE WANT TO LEARN
---------------------
  1.  How many requests before 429/403/redirect?
  2.  How long does a cool-down need to be before requests succeed again?
  3.  Does adding a delay (0 / 0.5 / 1 / 2 s) change the limit?
  4.  How many cards can be scraped in 5 min and 10 min?

TEST PHASES
-----------
  Phase 0 – Connection check
  Phase 1 – Search-page burst (delay=0s)
  Phase 2 – Cool-down discovery (how long to wait after a rate-limit)
  Phase 3 – Card-detail burst (delay=0s)
  Phase 4 – Sustainable rate benchmark (0.5s / 1s / 2s)
  Phase 5 – Image CDN burst
  Phase 6 – 5-min and 10-min endurance test

USAGE
-----
  python yuyu_tei_rate_test.py

  Optional flags:
    --group   GROUP_CODE   e.g. dcext1.0  (default: dcext1.0)
    --ws      WS           e.g. ws        (default: ws)
    --outdir  PATH         log output dir (default: ./rate_test_results)
    --phases  1,2,3,4,5,6  subset of phases to run
    --skip-burst           skip phases 1,3,5 to be polite
=============================================================================
"""

import requests
import time
import json
import os
import sys
import re
import argparse
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL            = "https://yuyu-tei.jp"
DEFAULT_GROUP       = "dcext1.0"
DEFAULT_WS          = "ws"
DEFAULT_OUTDIR      = "rate_test_results"
MAX_BURST_REQUESTS  = 80
DETAIL_LIMIT        = 60
BURST_TIMEOUT       = 15
NORMAL_TIMEOUT      = 20
MAX_COOLDOWN_WAIT   = 300
ENDURANCE_DELAYS    = [0.5, 1.0, 2.0]
ENDURANCE_WINDOWS   = [300, 600]


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _ts() -> float:
    return time.time()

def _fmt_dur(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def timed_get(session: requests.Session, url: str, timeout: int = NORMAL_TIMEOUT,
              params: dict = None) -> Dict:
    """Single GET with full instrumentation. Never raises."""
    result = {
        "url": url,
        "params": params,
        "timestamp": _now_str(),
        "status_code": None,
        "response_bytes": 0,
        "latency_ms": None,
        "error": None,
        "is_rate_limited": False,
        "is_success": False,
    }
    t0 = _ts()
    try:
        r = session.get(url, params=params, timeout=timeout, allow_redirects=True)
        result["latency_ms"] = round((_ts() - t0) * 1000, 1)
        result["status_code"] = r.status_code
        result["response_bytes"] = len(r.content)
        result["final_url"] = r.url

        if r.status_code in (429, 503):
            result["is_rate_limited"] = True
        elif r.status_code == 200 and len(r.content) < 500:
            result["is_rate_limited"] = True
            result["error"] = "tiny_response_possible_rate_limit"
        elif r.status_code == 200:
            result["is_success"] = True
        else:
            result["error"] = f"http_{r.status_code}"

        if result["is_success"]:
            # NOTE: do NOT truncate – card-product divs can appear late in large pages
            result["_text"] = r.text

    except requests.exceptions.Timeout:
        result["latency_ms"] = round((_ts() - t0) * 1000, 1)
        result["error"] = "timeout"
    except requests.exceptions.ConnectionError as e:
        result["latency_ms"] = round((_ts() - t0) * 1000, 1)
        result["error"] = f"connection_error: {e}"
    except Exception as e:
        result["latency_ms"] = round((_ts() - t0) * 1000, 1)
        result["error"] = f"unexpected: {e}"

    return result


# ---------------------------------------------------------------------------
# URL / HTML helpers
# ---------------------------------------------------------------------------

def search_url(ws: str, group: str) -> Tuple[str, dict]:
    url = f"{BASE_URL}/sell/{ws}/s/search"
    params = {"search_word": "", "vers[]": group, "rare": "", "type": "", "kizu": "0"}
    return url, params


def extract_card_links(html_text: str, ws: str) -> List[str]:
    soup  = BeautifulSoup(html_text, "html.parser")
    seen  = set()
    links = []
    for container in soup.find_all("div", class_="card-product"):
        a = container.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        if f"/sell/{ws}/card/" not in href:
            continue
        # Href may already be a full URL or a path – normalise to full URL
        full = href if href.startswith("http") else urljoin(BASE_URL, href)
        if full not in seen:
            seen.add(full)
            links.append(full)
    return links


def extract_image_url(html_text: str) -> Optional[str]:
    soup = BeautifulSoup(html_text, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict) and data.get("@type") == "Product":
                return data.get("image", "")
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

class RateTestLogger:
    def __init__(self, outdir: str):
        self.outdir   = Path(outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.outdir / "rate_test_log.json"
        self.txt_file = self.outdir / "rate_test_summary.txt"
        self.run_id   = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_data = {"run_id": self.run_id, "started": _now_str(),
                         "finished": None, "phases": {}}
        self._pw(f"\n{'='*70}")
        self._pw(f"  YUYU-TEI RATE LIMIT TEST  |  Run: {self.run_id}")
        self._pw(f"  Started: {_now_str()}")
        self._pw(f"{'='*70}\n")

    def _pw(self, line: str):
        print(line)
        with open(self.txt_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def log(self, msg: str):
        self._pw(f"  {msg}")

    def header(self, msg: str):
        self._pw(f"\n{'─'*70}")
        self._pw(f"  {msg}")
        self._pw(f"{'─'*70}")

    def save_phase(self, name: str, data: dict):
        self.run_data["phases"][name] = data
        self._flush_json()

    def finish(self):
        self.run_data["finished"] = _now_str()
        self._flush_json()
        self._pw(f"\n{'='*70}")
        self._pw(f"  Finished: {_now_str()}")
        self._pw(f"  JSON log : {self.log_file}")
        self._pw(f"  Summary  : {self.txt_file}")
        self._pw(f"{'='*70}\n")

    def _flush_json(self):
        history = []
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
                if not isinstance(history, list):
                    history = [history]
            except Exception:
                history = []
        history = [r for r in history if r.get("run_id") != self.run_id]
        history.append(self.run_data)
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    return s



# ---------------------------------------------------------------------------
# Phase 0 – connection check
# ---------------------------------------------------------------------------

def phase_connection_check(session, ws, group, logger: RateTestLogger) -> bool:
    logger.header("PHASE 0 – Connection Check")
    url, params = search_url(ws, group)
    logger.log(f"URL: {url}  params={params}")
    r = timed_get(session, url, timeout=BURST_TIMEOUT, params=params)
    ok = r["is_success"]
    logger.log(f"Status={r['status_code']}  latency={r.get('latency_ms')}ms  bytes={r['response_bytes']}")
    logger.log("✓ Site reachable." if ok else f"✗ FAILED – {r['error']}")
    logger.save_phase("phase_0_connection",
                      {"ok": ok, "result": {k: v for k, v in r.items() if k != "_text"}})
    return ok


# ---------------------------------------------------------------------------
# Phase 1 – search-page burst
# ---------------------------------------------------------------------------

def phase_search_burst(session, ws, group, logger: RateTestLogger) -> dict:
    logger.header("PHASE 1 – Search-Page Burst Test  (delay=0s)")
    url, params = search_url(ws, group)
    results, card_links = [], []
    t_start = _ts()
    logger.log(f"Sending up to {MAX_BURST_REQUESTS} requests as fast as possible …")
    for i in range(1, MAX_BURST_REQUESTS + 1):
        r     = timed_get(session, url, timeout=BURST_TIMEOUT, params=params)
        entry = {k: v for k, v in r.items() if k != "_text"}
        entry["seq"] = i
        results.append(entry)
        flag = "✓" if r["is_success"] else ("🚫" if r["is_rate_limited"] else "⚠")
        logger.log(f"[{i:>3}] {flag} status={r['status_code']}  latency={r.get('latency_ms')}ms  bytes={r['response_bytes']}")
        if r.get("is_success") and not card_links and r.get("_text"):
            card_links = extract_card_links(r["_text"], ws)
            logger.log(f"      → {len(card_links)} card links extracted")
        if r["is_rate_limited"]:
            logger.log(f"⛔ Rate limit at #{i}  elapsed={_fmt_dur(_ts()-t_start)}")
            break
    elapsed   = _ts() - t_start
    successes = sum(1 for r in results if r["is_success"])
    first_fail= next((r["seq"] for r in results if not r["is_success"]), None)
    logger.log(f"\n  Sent={len(results)}  OK={successes}  first_fail=#{first_fail}  "
               f"elapsed={_fmt_dur(elapsed)}  "
               f"RPS={round(len(results)/elapsed,2) if elapsed>0 else 'N/A'}")
    summary = {
        "total_requests": len(results), "successes": successes,
        "failures": len(results)-successes, "first_failure_at_seq": first_fail,
        "elapsed_seconds": round(elapsed, 2),
        "card_links_found": card_links[:100],
        "per_request_log": results,
    }
    logger.save_phase("phase_1_search_burst",
                      {k: v for k, v in summary.items() if k != "per_request_log"})
    return summary


# ---------------------------------------------------------------------------
# Phase 2 – cool-down discovery
# ---------------------------------------------------------------------------

def phase_cooldown(session, ws, group, logger: RateTestLogger) -> dict:
    logger.header("PHASE 2 – Cool-Down Discovery")
    url, params = search_url(ws, group)
    wait = 10
    attempts = []
    logger.log("Doubling wait time until we get a 200 back …")
    while wait <= MAX_COOLDOWN_WAIT:
        logger.log(f"  Waiting {wait}s …")
        time.sleep(wait)
        r     = timed_get(session, url, timeout=NORMAL_TIMEOUT, params=params)
        entry = {k: v for k, v in r.items() if k != "_text"}
        entry["wait_before"] = wait
        attempts.append(entry)
        flag = "✓ RECOVERED" if r["is_success"] else "✗ still blocked"
        logger.log(f"  {flag}  status={r['status_code']}")
        if r["is_success"]:
            logger.log(f"  ✅ Minimum cool-down: {wait}s")
            break
        wait *= 2
    else:
        logger.log(f"  ❌ Did not recover within {MAX_COOLDOWN_WAIT}s")
    recovered_after = next((a["wait_before"] for a in attempts if a.get("is_success")), None)
    result = {"recovered": recovered_after is not None,
              "min_cooldown_seconds": recovered_after, "attempts": attempts}
    logger.save_phase("phase_2_cooldown", result)
    return result


# ---------------------------------------------------------------------------
# Phase 3 – card-detail burst
# ---------------------------------------------------------------------------

def phase_detail_burst(session, ws, card_links: List[str], logger: RateTestLogger) -> dict:
    logger.header("PHASE 3 – Card-Detail Burst Test  (delay=0s)")
    if not card_links:
        logger.log("No card links – skipping.")
        result = {"skipped": True, "reason": "no_card_links"}
        logger.save_phase("phase_3_detail_burst", result)
        return result
    limit = min(DETAIL_LIMIT, len(card_links))
    results, image_urls = [], []
    t_start = _ts()
    logger.log(f"Fetching {limit} card detail pages …")
    for i, link in enumerate(card_links[:limit], 1):
        r     = timed_get(session, link, timeout=BURST_TIMEOUT)
        entry = {k: v for k, v in r.items() if k != "_text"}
        entry["seq"] = i
        results.append(entry)
        if r.get("is_success") and r.get("_text"):
            img = extract_image_url(r["_text"])
            if img:
                image_urls.append(img)
        flag = "✓" if r["is_success"] else ("🚫" if r["is_rate_limited"] else "⚠")
        logger.log(f"[{i:>3}] {flag} {r['status_code']}  {r.get('latency_ms')}ms")
        if r["is_rate_limited"]:
            logger.log(f"⛔ Rate limit at #{i}  elapsed={_fmt_dur(_ts()-t_start)}")
            break
    elapsed   = _ts() - t_start
    successes = sum(1 for r in results if r["is_success"])
    first_fail= next((r["seq"] for r in results if not r["is_success"]), None)
    logger.log(f"\n  Sent={len(results)}  OK={successes}  first_fail=#{first_fail}  "
               f"elapsed={_fmt_dur(elapsed)}  image_urls={len(image_urls)}")
    summary = {
        "total_requests": len(results), "successes": successes,
        "failures": len(results)-successes, "first_failure_at_seq": first_fail,
        "elapsed_seconds": round(elapsed, 2),
        "image_urls_collected": image_urls[:50],
        "per_request_log": results,
    }
    logger.save_phase("phase_3_detail_burst",
                      {k: v for k, v in summary.items() if k not in ("per_request_log","image_urls_collected")})
    return summary



# ---------------------------------------------------------------------------
# Phase 4 – sustainable rate benchmark
# ---------------------------------------------------------------------------

def phase_sustainable(session, card_links: List[str], logger: RateTestLogger) -> dict:
    logger.header("PHASE 4 – Sustainable Rate Benchmark")
    if not card_links:
        logger.log("No card links – skipping.")
        result = {"skipped": True}
        logger.save_phase("phase_4_sustainable", result)
        return result

    benchmark = {}
    for delay in ENDURANCE_DELAYS:
        logger.log(f"\n  ── delay={delay}s ──────────────────────────────────────")
        test_links = card_links[:DETAIL_LIMIT]
        results = []
        t_start = _ts()
        for i, link in enumerate(test_links, 1):
            r     = timed_get(session, link, timeout=NORMAL_TIMEOUT)
            entry = {k: v for k, v in r.items() if k != "_text"}
            entry["seq"] = i
            results.append(entry)
            flag = "✓" if r["is_success"] else ("🚫" if r["is_rate_limited"] else "⚠")
            logger.log(f"  [{i:>3}] {flag} {r['status_code']}  {r.get('latency_ms')}ms")
            if r["is_rate_limited"]:
                logger.log(f"  ⛔ Rate limit at #{i}  delay={delay}s")
                break
            if i < len(test_links):
                time.sleep(delay)
        elapsed   = _ts() - t_start
        successes = sum(1 for r in results if r["is_success"])
        rps       = round(successes / elapsed, 3) if elapsed > 0 else 0
        rpm       = round(rps * 60, 1)
        logger.log(f"  Sent={len(results)}  OK={successes}  "
                   f"elapsed={_fmt_dur(elapsed)}  rate={rps}req/s={rpm}req/min")
        benchmark[str(delay)] = {
            "delay_seconds": delay, "total_requests": len(results),
            "successes": successes, "failures": len(results)-successes,
            "elapsed_seconds": round(elapsed, 2),
            "requests_per_second": rps, "requests_per_minute": rpm,
            "rate_limited": any(r["is_rate_limited"] for r in results),
        }

    logger.save_phase("phase_4_sustainable", benchmark)
    return benchmark


# ---------------------------------------------------------------------------
# Phase 5 – image CDN burst
# ---------------------------------------------------------------------------

def phase_image_cdn(session, image_urls: List[str], logger: RateTestLogger) -> dict:
    logger.header("PHASE 5 – Image CDN Rate Test")
    if not image_urls:
        logger.log("No image URLs – skipping.")
        result = {"skipped": True, "reason": "no_image_urls"}
        logger.save_phase("phase_5_image_cdn", result)
        return result
    limit   = min(30, len(image_urls))
    results = []
    t_start = _ts()
    logger.log(f"Fetching {limit} card images (burst) …")
    for i, img_url in enumerate(image_urls[:limit], 1):
        r     = timed_get(session, img_url, timeout=BURST_TIMEOUT)
        entry = {k: v for k, v in r.items() if k != "_text"}
        entry["seq"] = i
        results.append(entry)
        flag = "✓" if r["is_success"] else ("🚫" if r["is_rate_limited"] else "⚠")
        logger.log(f"[{i:>3}] {flag} {r['status_code']}  {r.get('latency_ms')}ms  {r['response_bytes']}B")
        if r["is_rate_limited"]:
            logger.log(f"⛔ CDN rate limit at #{i}")
            break
    elapsed     = _ts() - t_start
    successes   = sum(1 for r in results if r["is_success"])
    total_bytes = sum(r["response_bytes"] for r in results if r["is_success"])
    summary = {
        "total_requests": len(results), "successes": successes,
        "failures": len(results)-successes,
        "first_failure_at_seq": next((r["seq"] for r in results if not r["is_success"]), None),
        "elapsed_seconds": round(elapsed, 2),
        "total_mb_downloaded": round(total_bytes/(1024*1024), 2),
    }
    logger.log(f"\n  Fetched={len(results)}  OK={successes}  "
               f"data={summary['total_mb_downloaded']}MB  elapsed={_fmt_dur(elapsed)}")
    logger.save_phase("phase_5_image_cdn", summary)
    return summary



# ---------------------------------------------------------------------------
# Phase 6 – endurance (5-min / 10-min windows)
# ---------------------------------------------------------------------------

def phase_endurance(session, card_links: List[str], logger: RateTestLogger) -> dict:
    logger.header("PHASE 6 – Endurance Test  (5 min + 10 min windows)")
    if not card_links:
        logger.log("No card links – skipping.")
        result = {"skipped": True}
        logger.save_phase("phase_6_endurance", result)
        return result

    delay = 1.0   # conservative safe default
    endurance_results = {}

    for window_secs in ENDURANCE_WINDOWS:
        label = f"{window_secs // 60}_min"
        logger.log(f"\n  ── {window_secs//60}-minute window  (delay={delay}s) ──────────────")
        results, rate_events = [], []
        t_start  = _ts()
        deadline = t_start + window_secs
        link_idx = 0

        while _ts() < deadline:
            link = card_links[link_idx % len(card_links)]
            link_idx += 1
            r   = timed_get(session, link, timeout=NORMAL_TIMEOUT)
            elapsed_now = round(_ts() - t_start, 1)
            entry = {k: v for k, v in r.items() if k != "_text"}
            entry["elapsed_s"] = elapsed_now
            entry["seq"]       = len(results) + 1
            results.append(entry)
            flag = "✓" if r["is_success"] else ("🚫" if r["is_rate_limited"] else "⚠")
            logger.log(f"  [{len(results):>4}] {flag}  t+{elapsed_now}s  "
                       f"status={r['status_code']}  {r.get('latency_ms')}ms")
            if r["is_rate_limited"]:
                ev = {"seq": len(results), "elapsed_s": elapsed_now, "status": r["status_code"]}
                rate_events.append(ev)
                logger.log(f"  ⛔ Rate-limit!  seq={len(results)}  t+{elapsed_now}s — pausing 30s …")
                time.sleep(30)
            time_left = deadline - _ts()
            if time_left <= 0:
                break
            time.sleep(min(delay, time_left))

        total_elapsed = round(_ts() - t_start, 1)
        successes     = sum(1 for r in results if r["is_success"])
        total_bytes   = sum(r["response_bytes"] for r in results if r["is_success"])
        cpm = round(successes / (total_elapsed / 60), 1) if total_elapsed > 0 else 0
        logger.log(f"\n  ── {window_secs//60}-min Results ─────────────────────────────")
        logger.log(f"  Requests={len(results)}  OK={successes}  RL-events={len(rate_events)}")
        logger.log(f"  Data={round(total_bytes/(1024*1024),2)}MB  elapsed={_fmt_dur(total_elapsed)}  {cpm} cards/min")
        endurance_results[label] = {
            "window_seconds": window_secs, "delay_seconds": delay,
            "total_requests": len(results), "successes": successes,
            "failures": len(results)-successes,
            "rate_limit_events": len(rate_events), "rate_limit_detail": rate_events,
            "total_bytes": total_bytes, "total_mb": round(total_bytes/(1024*1024), 2),
            "actual_elapsed_s": total_elapsed, "cards_per_minute": cpm,
        }

    logger.save_phase("phase_6_endurance", endurance_results)
    return endurance_results



# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------

def print_final_summary(logger: RateTestLogger, all_data: dict):
    logger.header("FINAL SUMMARY")
    p1 = all_data.get("phase_1_search_burst", {})
    p2 = all_data.get("phase_2_cooldown",     {})
    p3 = all_data.get("phase_3_detail_burst", {})
    p4 = all_data.get("phase_4_sustainable",  {})
    p6 = all_data.get("phase_6_endurance",    {})

    logger.log(f"Search burst limit : ~{p1.get('first_failure_at_seq','N/A')} requests before 1st fail")
    logger.log(f"Detail burst limit : ~{p3.get('first_failure_at_seq','N/A')} requests before 1st fail")
    logger.log(f"Min cool-down      : {p2.get('min_cooldown_seconds','N/A')} seconds")

    if isinstance(p4, dict):
        logger.log("\nSustainable rate (card detail pages):")
        for delay, data in p4.items():
            if isinstance(data, dict):
                rl = "YES – not safe" if data.get("rate_limited") else "No"
                logger.log(f"  delay={delay}s → {data.get('requests_per_minute','?')} req/min  rl={rl}")

    if isinstance(p6, dict):
        logger.log("\nEndurance results:")
        for label, data in p6.items():
            if isinstance(data, dict):
                logger.log(f"  {label.replace('_',' ')}: {data.get('successes','?')} cards "
                           f"({data.get('cards_per_minute','?')}/min)  "
                           f"RL-events={data.get('rate_limit_events','?')}")

    safe_delay = None
    if isinstance(p4, dict):
        for d in ["2.0", "1.0", "0.5"]:
            entry = p4.get(d, {})
            if isinstance(entry, dict) and not entry.get("rate_limited") and entry.get("successes",0)>0:
                safe_delay = float(d)
                break

    logger.log("\nRECOMMENDATIONS:")
    if safe_delay is not None:
        rpm = p4.get(str(safe_delay), {}).get("requests_per_minute")
        logger.log(f"  ✓ Safest delay     : {safe_delay}s between requests")
        if rpm:
            logger.log(f"  ✓ Throughput       : ~{rpm} pages/min")
            logger.log(f"  ✓ Cards in  5 min  : ~{round(rpm*5)}")
            logger.log(f"  ✓ Cards in 10 min  : ~{round(rpm*10)}")
    else:
        logger.log("  ⚠ Could not determine safe delay – review logs manually.")
    cooldown = p2.get("min_cooldown_seconds")
    if cooldown:
        logger.log(f"  ✓ After RL hit     : wait ≥ {cooldown}s before retrying")



# ---------------------------------------------------------------------------
# CLI + main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Yuyu-Tei rate limit tester")
    p.add_argument("--group",      default=DEFAULT_GROUP, help="Card group (default: dcext1.0)")
    p.add_argument("--ws",         default=DEFAULT_WS,    help="WS id (default: ws)")
    p.add_argument("--outdir",     default=DEFAULT_OUTDIR,help="Log output dir")
    p.add_argument("--phases",     default="0,1,2,3,4,5,6",
                   help="Comma-separated phases to run (default: all)")
    p.add_argument("--skip-burst", action="store_true",
                   help="Skip burst phases 1,3,5 to be polite")
    return p.parse_args()


def main():
    args   = parse_args()
    ws, group, outdir = args.ws, args.group, args.outdir
    wanted = set(int(x.strip()) for x in args.phases.split(","))
    if args.skip_burst:
        wanted -= {1, 3, 5}

    logger  = RateTestLogger(outdir)
    logger.log(f"Group={group}  WS={ws}  Phases={sorted(wanted)}")
    session = make_session()
    all_data: dict        = {}
    card_links: List[str] = []
    image_urls: List[str] = []
    # Keep phase-0 response text so we can reuse it for card-link extraction
    _phase0_html: str     = ""

    try:
        if 0 in wanted:
            ok = phase_connection_check(session, ws, group, logger)
            all_data["phase_0"] = ok
            if not ok:
                logger.log("Aborting – site unreachable.")
                return
            # Re-fetch with _text to reuse (phase_connection_check discards it)
            url, params = search_url(ws, group)
            _r0 = timed_get(session, url, timeout=NORMAL_TIMEOUT, params=params)
            if _r0.get("is_success"):
                _phase0_html = _r0.get("_text", "")

        if 1 in wanted:
            p1 = phase_search_burst(session, ws, group, logger)
            all_data["phase_1_search_burst"] = p1
            card_links = p1.get("card_links_found", [])
        else:
            # Reuse phase-0 HTML if available, otherwise do a quiet fetch
            if _phase0_html:
                card_links = extract_card_links(_phase0_html, ws)
                logger.log(f"\n(Card links from Phase 0 response: {len(card_links)} found)")
            else:
                logger.log("\n(Quiet single search fetch for card links …)")
                url, params = search_url(ws, group)
                r = timed_get(session, url, timeout=NORMAL_TIMEOUT, params=params)
                if r.get("is_success") and r.get("_text"):
                    card_links = extract_card_links(r["_text"], ws)
                    logger.log(f"  Collected {len(card_links)} card links.")

        if 2 in wanted:
            p1_data = all_data.get("phase_1_search_burst", {})
            if p1_data.get("failures", 0) > 0:
                p2 = phase_cooldown(session, ws, group, logger)
                all_data["phase_2_cooldown"] = p2
            else:
                logger.header("PHASE 2 – Cool-Down Discovery")
                logger.log("Phase 1 had no failures – skipping cool-down test.")
                skip = {"skipped": True, "reason": "no_rate_limit_in_phase1"}
                all_data["phase_2_cooldown"] = skip
                logger.save_phase("phase_2_cooldown", skip)

        if 3 in wanted:
            p3 = phase_detail_burst(session, ws, card_links, logger)
            all_data["phase_3_detail_burst"] = p3
            image_urls = p3.get("image_urls_collected", [])

        if 4 in wanted:
            p4 = phase_sustainable(session, card_links, logger)
            all_data["phase_4_sustainable"] = p4

        if 5 in wanted:
            if not image_urls and card_links:
                logger.header("PHASE 5 – collecting image URLs (quiet) …")
                for link in card_links[:20]:
                    r = timed_get(session, link, timeout=NORMAL_TIMEOUT)
                    if r.get("is_success") and r.get("_text"):
                        img = extract_image_url(r["_text"])
                        if img:
                            image_urls.append(img)
                    time.sleep(1.0)
            p5 = phase_image_cdn(session, image_urls, logger)
            all_data["phase_5_image_cdn"] = p5

        if 6 in wanted:
            p6 = phase_endurance(session, card_links, logger)
            all_data["phase_6_endurance"] = p6

        print_final_summary(logger, all_data)

    except KeyboardInterrupt:
        logger.log("\n⚠️  Interrupted – saving partial results.")
        print_final_summary(logger, all_data)
    except Exception:
        logger.log(f"\n❌ Error:\n{traceback.format_exc()}")
    finally:
        logger.finish()


if __name__ == "__main__":
    main()

