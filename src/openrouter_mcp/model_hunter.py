import os
import json
import argparse

import httpx
from dotenv import load_dotenv

BASE_URL = "https://openrouter.ai/api/v1/models"

# Load .env so OPENROUTER_API_KEY / REQUEST_TIMEOUT are picked up when run as a CLI
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 30.0))


def fetch_models() -> list[dict]:
  if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set.")

  headers = {
    "Authorization": f"Bearer {API_KEY}",
    "HTTP-Referer": "https://github.com/klim4-bot/openrouter-mcp",
    "X-Title": "OpenRouter-Model-Hunter",
  }

  with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
    resp = client.get(BASE_URL, headers=headers)
    resp.raise_for_status()
    data = resp.json()

  if "data" not in data or not isinstance(data["data"], list):
    raise RuntimeError("Invalid response from OpenRouter /models API.")

  return data["data"]


def parse_price(model: dict) -> float:
  try:
    raw = model.get("pricing", {}).get("prompt")
    if raw is None:
      return float("inf")
    # OpenRouter pricing is usually per 1M tokens (string), e.g. "0.1000"
    return float(raw)
  except (ValueError, TypeError):
    return float("inf")


def filter_and_sort_models(models: list[dict], *, free_only: bool, max_prompt: float | None, limit: int) -> list[dict]:
  filtered: list[dict] = []
  for m in models:
    price = parse_price(m)
    if free_only and price != 0.0:
      continue
    if max_prompt is not None and price > max_prompt:
      continue
    filtered.append(m)

  filtered.sort(key=parse_price)
  return filtered[:limit]


def format_summary(models: list[dict], *, free_only: bool, max_prompt: float | None) -> str:
  lines: list[str] = []
  lines.append("[OpenRouter Model Hunter]")
  lines.append("")

  if free_only:
    lines.append("Free models (prompt price = 0):")
  elif max_prompt is not None:
    lines.append(f"Models with prompt price <= {max_prompt}: (cheapest first)")
  else:
    lines.append("Cheapest models (by prompt price):")

  free_count = 0
  for idx, m in enumerate(models, start=1):
    mid = m.get("id", "<unknown>")
    ctx = m.get("context_length", "N/A")
    price = m.get("pricing", {}).get("prompt", "N/A")
    if price in (None, ""):
      price = "N/A"
    try:
      p_val = float(price)
      if p_val == 0.0:
        free_count += 1
    except (ValueError, TypeError):
      pass

    lines.append(f"{idx}. {mid} (context: {ctx}, prompt: {price})")

  lines.append("")
  lines.append(f"Total listed: {len(models)} (free: {free_count})")

  return "\n".join(lines)


def main() -> None:
  parser = argparse.ArgumentParser(description="OpenRouter Model Hunter - list free/low-cost models.")
  parser.add_argument("--free-only", action="store_true", help="Show only free models (prompt price = 0).")
  parser.add_argument("--max-prompt", type=float, default=None, help="Maximum prompt price to include (e.g. 0.5).")
  parser.add_argument("--limit", type=int, default=20, help="Maximum number of models to display.")

  args = parser.parse_args()

  limit = max(1, min(100, args.limit))

  try:
    models = fetch_models()
  except Exception as e:
    print(f"Error fetching models: {e}")
    raise SystemExit(1)

  filtered = filter_and_sort_models(models, free_only=args.free_only, max_prompt=args.max_prompt, limit=limit)

  if not filtered:
    print("No models found for the given criteria.")
    raise SystemExit(0)

  summary = format_summary(filtered, free_only=args.free_only, max_prompt=args.max_prompt)
  print(summary)


if __name__ == "__main__":
  main()
