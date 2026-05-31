#!/usr/bin/env python3
"""Headless Tolaria verifier. Drives the read-only MCP server over stdio against an
arbitrary set of vault roots and prints note count, discovered types, and search hits.

Usage:
    tolaria_verify.py --query "WikiTree ID" <vaultRoot> [<vaultRoot> ...]

Read-only: only calls get_vault_context + search_notes. Nothing is written.
"""
import argparse
import json
import os
import select
import subprocess
import sys
import time

SERVER = "/usr/lib/Tolaria/mcp-server/index.js"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+", help="vault root directories")
    ap.add_argument("--query", default="WikiTree", help="search_notes query")
    ap.add_argument("--limit", type=int, default=8)
    args = ap.parse_args()

    env = {**os.environ, "VAULT_PATHS": json.dumps([os.path.abspath(r) for r in args.roots])}
    proc = subprocess.Popen(
        ["node", SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env=env, text=True, bufsize=1,
    )

    def send(obj):
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    def read_resp(want_id, timeout=120):
        deadline = time.time() + timeout
        while time.time() < deadline:
            r, _, _ = select.select([proc.stdout], [], [], deadline - time.time())
            if not r:
                break
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("id") == want_id:
                return obj
        return None

    t0 = time.time()
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                     "clientInfo": {"name": "verify", "version": "0"}}})
    if not read_resp(1, 30):
        print("[init] FAILED"); print(proc.stderr.read()[:1500]); proc.kill(); sys.exit(1)
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
          "params": {"name": "list_vaults", "arguments": {}}})
    lv = read_resp(2)
    if lv:
        print("[list_vaults]", json.dumps(lv.get("result", lv))[:600])

    send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
          "params": {"name": "get_vault_context", "arguments": {}}})
    ctx = read_resp(3)
    if ctx:
        try:
            body = json.loads(ctx["result"]["content"][0]["text"])
            if "vaults" in body:  # multi-vault: server returns a per-vault array
                vaults = body["vaults"]
                total = sum(v.get("noteCount", 0) for v in vaults)
                types = sorted({t for v in vaults for t in (v.get("types") or [])})
                print(f"[get_vault_context] noteCount={total} "
                      f"across {len(vaults)} vaults; types={types}")
                for v in vaults:
                    print(f"     - {v.get('label') or v.get('path')}: "
                          f"{v.get('noteCount')} {v.get('types')}")
            else:
                print(f"[get_vault_context] noteCount={body.get('noteCount')} "
                      f"types={body.get('types')}")
        except Exception:
            print("[get_vault_context]", json.dumps(ctx.get("result", ctx))[:800])

    send({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
          "params": {"name": "search_notes", "arguments": {"query": args.query, "limit": args.limit}}})
    res = read_resp(4)
    if res:
        try:
            text = res["result"]["content"][0]["text"]
        except Exception:
            text = json.dumps(res.get("result", res))
        # print the path lines so dedup is visible
        print(f"[search_notes '{args.query}']")
        for line in text.splitlines():
            if line.strip().startswith("**") or "/" in line[:80]:
                print("   ", line[:160])

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    print(f"[total] {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()
