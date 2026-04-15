#!/usr/bin/env python3
"""
familysearch_api.py — Portable FamilySearch API client.

Wraps the FamilySearch REST API for use in genealogy research pipelines.
All requests go to api.familysearch.org (NOT www.familysearch.org — the www
host blocks scripted requests with a WAF/errorCode 15 response).

Authentication:
    The FS session token is read from the environment variable FS_TOKEN, or
    from a .playwright-secrets.env file in the project root (KEY=VALUE format).
    Tokens are obtained by logging in to FamilySearch in a browser and copying
    the `fssessionid` cookie value. Tokens expire in approximately 2 hours;
    refresh by logging in again and re-copying the cookie.

Usage example:
    from familysearch_api import FamilySearchClient

    client = FamilySearchClient()   # reads token from env / .playwright-secrets.env

    # Fetch a person record
    person = client.get_person("LH7S-R3T")
    print(person["display"]["name"])

    # Fetch attached sources
    sources = client.get_sources("LH7S-R3T")
    for s in sources:
        print(s["tier"], s["title"])

    # Fetch parents
    parents = client.get_parents("LH7S-R3T")
    if parents:
        print("Father PID:", parents.get("parent1_id"))

    # Full-text search across all records
    hits = client.search_full_text(["john smith", "virginia"])
    for h in hits:
        print(h.get("id"), h.get("title"))

    # Create a parent-child relationship (use with caution — see docstring)
    ok = client.create_parent_child_relationship("AAAA-001", "BBBB-002")

Run as a script to do a quick connectivity test:
    python3 familysearch_api.py
"""

import os
import sys
import time
import json
import re
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FS_API_BASE = "https://api.familysearch.org"

# Token env var name and the .playwright-secrets.env key
TOKEN_ENV_VAR = "FS_TOKEN"
SECRETS_FILE = ".playwright-secrets.env"

# Request delay between API calls (seconds). 0.3s is sufficient; do not go
# below 0.2s or sustained batch runs may trigger throttling.
DEFAULT_REQUEST_DELAY = 0.3

# Retry config for transient errors (429 Too Many Requests, 503 Unavailable)
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0   # seconds — doubles each retry

# Tier-5 title patterns: sources whose titles match these are online trees /
# patron submissions and should be treated as tier 5 (leads, not evidence).
TIER5_PATTERNS = [
    "family tree",
    "pedigree",
    "ancestry.com tree",
    "patron submitted",
    "user submitted",
    "community tree",
    "member tree",
    "collaborative tree",
]


# ---------------------------------------------------------------------------
# Token loading
# ---------------------------------------------------------------------------

def _load_token_from_env_file(path: Path) -> Optional[str]:
    """Parse a KEY=VALUE secrets file and return the FS_TOKEN value if found."""
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                if key.strip() == TOKEN_ENV_VAR:
                    return value.strip().strip('"').strip("'")
    return None


def load_fs_token() -> str:
    """Load the FamilySearch session token.

    Search order:
    1. FS_TOKEN environment variable
    2. .playwright-secrets.env file in the current working directory

    Raises RuntimeError if no token is found.
    """
    token = os.environ.get(TOKEN_ENV_VAR)
    if token:
        return token

    secrets_path = Path(SECRETS_FILE)
    token = _load_token_from_env_file(secrets_path)
    if token:
        return token

    raise RuntimeError(
        f"FamilySearch token not found. Set the {TOKEN_ENV_VAR} environment "
        f"variable or add {TOKEN_ENV_VAR}=<value> to {SECRETS_FILE}.\n"
        "Obtain the token by logging in to FamilySearch in a browser and "
        "copying the 'fssessionid' cookie value. Tokens expire in ~2 hours."
    )


# ---------------------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------------------

def _classify_tier(title: str) -> Optional[int]:
    """Return tier 5 if the title matches a known online-tree pattern.

    Returns None for titles that should be classified by the caller based on
    the source collection (e.g., census → tier 2, vital record → tier 1).
    """
    lower = title.lower()
    for pattern in TIER5_PATTERNS:
        if pattern in lower:
            return 5
    return None


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------

def _build_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "AI-Genealogy-Starter-Kit/1.0",
    }


def _request(
    method: str,
    url: str,
    token: str,
    delay: float = DEFAULT_REQUEST_DELAY,
    **kwargs,
) -> Optional[requests.Response]:
    """Make an HTTP request with retry logic for transient errors.

    Returns the Response on success.
    Returns None on 404 (person/resource not found — normal in genealogy work).
    Raises on unexpected errors after MAX_RETRIES attempts.
    """
    time.sleep(delay)
    headers = _build_headers(token)
    # Merge caller-supplied headers if any
    if "headers" in kwargs:
        headers.update(kwargs.pop("headers"))

    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE ** attempt)
            continue

        if resp.status_code == 404:
            return None  # Normal: resource simply does not exist

        if resp.status_code in (429, 503):
            # Throttled or temporarily unavailable — back off and retry
            wait = RETRY_BACKOFF_BASE ** attempt
            print(
                f"  [{resp.status_code}] rate-limited on {url} — "
                f"waiting {wait:.1f}s (attempt {attempt}/{MAX_RETRIES})",
                file=sys.stderr,
            )
            time.sleep(wait)
            continue

        if resp.status_code == 204:
            # No content — success with empty body
            return resp

        resp.raise_for_status()
        return resp

    if last_exc:
        raise last_exc
    raise RuntimeError(f"Request to {url} failed after {MAX_RETRIES} attempts")


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

class FamilySearchClient:
    """Portable FamilySearch API client.

    Instantiate once per script run. The token is loaded from the environment
    or .playwright-secrets.env at construction time.

        client = FamilySearchClient()
        client = FamilySearchClient(token="explicit-token", delay=0.5)
    """

    def __init__(
        self,
        token: Optional[str] = None,
        delay: float = DEFAULT_REQUEST_DELAY,
    ):
        self.token = token or load_fs_token()
        self.delay = delay

    def _get(self, path: str, **params) -> Optional[dict]:
        """GET a JSON endpoint. Returns parsed dict or None on 404."""
        url = f"{FS_API_BASE}{path}"
        resp = _request("GET", url, self.token, delay=self.delay, params=params)
        if resp is None:
            return None
        return resp.json()

    def _post(self, path: str, payload: dict) -> Optional[dict]:
        """POST a JSON payload. Returns parsed response dict or None on 404."""
        url = f"{FS_API_BASE}{path}"
        resp = _request(
            "POST",
            url,
            self.token,
            delay=self.delay,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if resp is None:
            return None
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    # -----------------------------------------------------------------------
    # Public API methods
    # -----------------------------------------------------------------------

    def get_person(self, pid: str) -> Optional[dict]:
        """Fetch a person record by FamilySearch person ID.

        Returns the full API response dict, or None if the person is not found.

        The person's display-friendly name is at result["display"]["name"].
        """
        data = self._get(f"/platform/tree/persons/{pid}")
        if data is None:
            return None
        # The API wraps the person in a "persons" list
        persons = data.get("persons") or []
        return persons[0] if persons else None

    def get_sources(self, pid: str) -> list[dict]:
        """Fetch sources attached to a person on the FamilySearch tree.

        Returns a list of dicts with keys:
            title (str)    — human-readable source title
            ark   (str)    — persistent ARK URL (may be None for older sources)
            citation (str) — formatted citation string (may be None)
            tier  (int or None) — 5 if title matches an online-tree pattern,
                                  None otherwise (caller should classify)

        Filters out sources with None or empty titles.
        Deduplicates by ARK URL and lowercased title to avoid double-counting.
        """
        data = self._get(f"/platform/tree/persons/{pid}/sources")
        if not data:
            return []

        raw_sources = data.get("sourceDescriptions") or []
        results = []
        seen_arks: set[str] = set()
        seen_titles: set[str] = set()

        for src in raw_sources:
            titles = src.get("titles") or []
            title = titles[0]["value"].strip() if titles and titles[0].get("value") else ""
            if not title:
                continue

            # ARK identifier — check both 'about' and nested identifiers
            ark = src.get("about") or ""
            if not ark:
                for ident in src.get("identifiers", {}).values():
                    if isinstance(ident, list) and ident:
                        ark = ident[0]
                        break

            # Deduplicate
            title_key = title.lower()
            if ark and ark in seen_arks:
                continue
            if title_key in seen_titles:
                continue
            if ark:
                seen_arks.add(ark)
            seen_titles.add(title_key)

            citations = src.get("citations") or []
            citation = citations[0]["value"] if citations and citations[0].get("value") else None

            results.append({
                "title": title,
                "ark": ark or None,
                "citation": citation,
                "tier": _classify_tier(title),
            })

        return results

    def get_parents(self, pid: str) -> Optional[dict]:
        """Fetch the parent relationship for a person.

        Returns a dict with:
            parent1_id (str or None) — ID of first parent (typically father)
            parent2_id (str or None) — ID of second parent (typically mother)
            relationship_id (str or None) — the FS relationship record ID

        Returns None if the person has no recorded parents on the FS tree.
        """
        data = self._get(f"/platform/tree/persons/{pid}/parents")
        if not data:
            return None

        # The response wraps results in a "childAndParentsRelationships" list
        rels = data.get("childAndParentsRelationships") or []
        if not rels:
            return None

        rel = rels[0]  # take the first (primary) parent relationship

        def _extract_id(ref: Optional[dict]) -> Optional[str]:
            if not ref:
                return None
            resource = ref.get("resourceId") or ref.get("resource") or ""
            # Extract PID from URL like .../persons/XXXX-XXX or plain ID
            match = re.search(r"/persons/([A-Z0-9]{4}-[A-Z0-9]{3,4})$", resource)
            if match:
                return match.group(1)
            # If it looks like a bare PID already
            if re.match(r"^[A-Z0-9]{4}-[A-Z0-9]{3,4}$", resource):
                return resource
            return resource or None

        return {
            "parent1_id": _extract_id(rel.get("father")),
            "parent2_id": _extract_id(rel.get("mother")),
            "relationship_id": rel.get("id"),
        }

    def create_parent_child_relationship(
        self,
        parent_pid: str,
        child_pid: str,
        parent_role: str = "parent1",
    ) -> bool:
        """Create a parent-child relationship on the FamilySearch tree.

        IMPORTANT: Use POST /platform/tree/child-and-parents-relationships.
        DO NOT use POST /platform/tree/relationships — that endpoint creates
        COUPLE relationships (spouse pairings), NOT parent-child links. Using
        the wrong endpoint will silently create incorrect couple relationships
        that must be manually reverted. This is a known API design gotcha.

        Args:
            parent_pid: FamilySearch person ID of the parent.
            child_pid:  FamilySearch person ID of the child.
            parent_role: "parent1" (typically father) or "parent2" (typically
                         mother). The FS API uses these generic role names.

        Returns True on success, False on failure.

        Note: The FamilySearch tree requires you to have contributor access to
        both the parent and child profiles. The operation may fail silently on
        restricted profiles (living persons, private trees).
        """
        if parent_role not in ("parent1", "parent2"):
            raise ValueError(f"parent_role must be 'parent1' or 'parent2', got {parent_role!r}")

        payload = {
            "childAndParentsRelationships": [
                {
                    "child": {"resourceId": child_pid},
                    parent_role: {"resourceId": parent_pid},
                }
            ]
        }

        try:
            result = self._post("/platform/tree/child-and-parents-relationships", payload)
            return result is not None
        except Exception as exc:
            print(f"ERROR creating parent-child rel ({parent_pid} → {child_pid}): {exc}", file=sys.stderr)
            return False

    def search_full_text(
        self,
        query_terms: list[str],
        collection_id: Optional[str] = None,
    ) -> list[dict]:
        """Search FamilySearch records using full-text OCR search.

        More powerful than the person-tree search for pre-1856 handwritten
        records. Searches across digitized record images.

        Args:
            query_terms: List of terms to search. Each term is wrapped in
                         REQUIRED (+) operators to enforce AND logic. Without
                         the + prefix, FS silently applies OR, returning
                         irrelevant results.
            collection_id: Optional FS collection ID to restrict the search
                           (e.g., "1410696" for 1850 US Census). If None,
                           searches all indexed collections.

        Returns a list of hit dicts from the API response. Each hit may have:
            id, title, score, content (extracted text), links, etc.
        """
        if not query_terms:
            return []

        # Wrap each term in REQUIRED (+) operators — critical for AND behavior.
        # Example: ["john smith", "virginia"] → '+"john smith" +"virginia"'
        formatted_query = " ".join(f'+"{term}"' for term in query_terms)

        params: dict = {
            "q.textAvailable": "true",
            "q": formatted_query,
            "count": 20,
        }
        if collection_id:
            params["collectionId"] = collection_id

        data = self._get("/platform/records/search", **params)
        if not data:
            return []

        # Results are in the "entries" list within the response
        return data.get("entries") or []


# ---------------------------------------------------------------------------
# Quick connectivity test (run as script)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("FamilySearch API — connectivity test")
    try:
        client = FamilySearchClient()
        print("Token loaded successfully.")
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Try a known stable public profile (George Washington — always present)
    test_pid = "KWJR-SKF"
    print(f"Fetching person {test_pid} (George Washington) ...")
    person = client.get_person(test_pid)
    if person:
        display = person.get("display") or {}
        print(f"  Name: {display.get('name', '?')}")
        print(f"  Birth: {display.get('birthDate', '?')} — {display.get('birthPlace', '?')}")
        print("  OK")
    else:
        print(f"  Person {test_pid} not found (unexpected)")
        sys.exit(1)

    print(f"\nFetching sources for {test_pid} ...")
    sources = client.get_sources(test_pid)
    print(f"  {len(sources)} source(s) found")
    for src in sources[:3]:
        print(f"  [{src['tier'] or '?'}] {src['title'][:80]}")

    print("\nAll checks passed.")
