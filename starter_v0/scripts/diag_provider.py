"""Fail-fast diagnostics for a model provider.

`preflight_provider.py` runs the full tool-calling smoke test. When that appears
to hang, run this first: it isolates each layer (env key -> DNS -> TCP -> auth ->
model -> tool calling) with short timeouts and prints where it actually breaks.

    python scripts/diag_provider.py --provider nim
"""
from __future__ import annotations

import argparse
import os
import socket
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider

load_lab_env(ROOT)

OK = "OK  "
BAD = "FAIL"


def step(label: str) -> None:
    print(f"\n--- {label} ---")


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose a provider connection.")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    provider = make_provider(args.provider)
    base_url = getattr(provider, "base_url", None) or "https://api.openai.com/v1"
    key_env = getattr(provider, "api_key_env", "?")
    model = args.model or getattr(provider, "default_model", None)

    step("1. Config")
    print(f"     provider   = {args.provider}")
    print(f"     base_url   = {base_url}")
    print(f"     model      = {model}")

    step("2. API key")
    key = os.getenv(key_env)
    if not key:
        print(f"{BAD} {key_env} is not set.")
        print("     Copy .env.example to .env and fill it in, then re-run.")
        return
    print(f"{OK} {key_env} is set (len={len(key)}, starts with {key[:6]!r})")
    if args.provider == "nim" and not key.startswith("nvapi-"):
        print("     WARNING: NVIDIA NIM keys normally start with 'nvapi-'.")

    host = urlparse(base_url).hostname or ""
    port = urlparse(base_url).port or 443

    step("3. DNS")
    try:
        addrs = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        print(f"{OK} {host} -> {addrs[0][4][0]}")
    except Exception as exc:
        print(f"{BAD} cannot resolve {host}: {exc}")
        print("     Likely no internet, or DNS/VPN/firewall is blocking it.")
        return

    step(f"4. TCP connect (timeout {args.timeout}s)")
    started = time.time()
    try:
        with socket.create_connection((host, port), timeout=args.timeout):
            print(f"{OK} connected to {host}:{port} in {time.time() - started:.2f}s")
    except Exception as exc:
        print(f"{BAD} cannot reach {host}:{port}: {exc}")
        print("     A corporate proxy or firewall is the usual cause.")
        print("     If you use a proxy, set HTTPS_PROXY before running.")
        return

    step(f"5. Chat completion, no tools (timeout {args.timeout}s)")
    provider.timeout = args.timeout
    provider.max_retries = 0
    started = time.time()
    try:
        resp = provider.complete(
            [{"role": "user", "content": "Reply with the single word: pong"}],
            model=model,
            temperature=0.0,
        )
        print(f"{OK} responded in {time.time() - started:.2f}s: {(resp.text or '').strip()[:80]!r}")
    except Exception as exc:
        print(f"{BAD} {type(exc).__name__}: {exc}")
        hint = str(exc).lower()
        if "temperature" in hint:
            print("     This model rejects temperature=0. Pick another model via --model / NIM_MODEL.")
        elif "401" in hint or "unauthor" in hint or "api key" in hint:
            print("     The key was rejected. Check for typos or a trailing space in .env.")
        elif "404" in hint or "not found" in hint or "model" in hint:
            print(f"     Model {model!r} may not exist on this endpoint. Check the model id.")
        return

    step(f"6. Structured tool calling (timeout {args.timeout}s)")
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }]
    started = time.time()
    try:
        resp = provider.complete(
            [{"role": "user", "content": "What is the weather in Hanoi right now?"}],
            tools,
            model=model,
            temperature=0.0,
        )
    except Exception as exc:
        print(f"{BAD} {type(exc).__name__}: {exc}")
        return

    if not resp.tool_calls:
        print(f"{BAD} model replied with text instead of a tool call ({time.time() - started:.2f}s)")
        print(f"     text = {(resp.text or '')[:120]!r}")
        print("     This model does not do function calling. Pick another model.")
        return

    call = resp.tool_calls[0]
    print(f"{OK} tool={call.name} args={call.args} ({time.time() - started:.2f}s)")
    print(f"\nAll checks passed. Now run: python scripts/preflight_provider.py --provider {args.provider}")


if __name__ == "__main__":
    main()
