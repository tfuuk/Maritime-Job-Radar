"""
Maritime Job Radar - daily digest script.

For every company on the watchlist, asks Claude (with web search enabled)
to find:
  1. Direct signals: hires, promotions, funding, job postings
  2. General industry news mentioning the company

Compiles everything into one HTML email and sends it via Resend.

Required environment variables (set as GitHub Actions secrets):
  ANTHROPIC_API_KEY
  RESEND_API_KEY
  DIGEST_TO_EMAIL
"""

import os
import json
import time
import requests
from datetime import date
from watchlist import build_company_list

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
TO_EMAIL = os.environ.get("DIGEST_TO_EMAIL")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
RESEND_URL = "https://api.resend.com/emails"

MODEL = "claude-sonnet-4-6"

PROMPT_TEMPLATE = """You are researching the maritime technology company "{company}" for a
daily job-search intelligence digest. Search the web for anything published
in roughly the last 24-48 hours.

Return ONLY a JSON object, no preamble, no markdown fences, in this exact shape:

{{
  "direct_signals": "1-3 sentences on hires, promotions, funding rounds, or job postings found. Empty string if nothing found.",
  "general_news": "1-3 sentences on any other news mentioning the company. Empty string if nothing found."
}}

If you find nothing relevant and recent for a field, return an empty string
for that field. Do not pad with old or generic company-description content."""


def search_company(company):
    """Call the Anthropic API with web search enabled for one company."""
    body = {
        "model": MODEL,
        "max_tokens": 500,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [
            {"role": "user", "content": PROMPT_TEMPLATE.format(company=company)}
        ],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    resp = requests.post(ANTHROPIC_URL, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    raw = text_blocks[-1] if text_blocks else "{}"
    raw = raw.strip().strip("`")
    if raw.startswith("json"):
        raw = raw[4:].strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"direct_signals": "", "general_news": ""}

    return {
        "direct_signals": parsed.get("direct_signals", "").strip(),
        "general_news": parsed.get("general_news", "").strip(),
    }


def build_digest():
    """Search every company on the watchlist and collect results by tier."""
    results = {"tier1": [], "tier2": []}
    for entry in build_company_list():
        name, tier = entry["name"], entry["tier"]
        try:
            findings = search_company(name)
        except Exception as exc:
            findings = {"direct_signals": "", "general_news": f"(search failed: {exc})"}

        if findings["direct_signals"] or findings["general_news"]:
            results["tier1" if tier == 1 else "tier2"].append({"name": name, **findings})

        time.sleep(0.5)

    return results


def render_company_block(company):
    has_signal = bool(company["direct_signals"])
    accent = "#0a7d3e" if has_signal else "#94a3b8"  # green if direct signal, grey if just news
    bg = "#f0fdf4" if has_signal else "#f8fafc"

    parts = [
        f'<div style="border-left:4px solid {accent}; background:{bg}; '
        f'border-radius:6px; padding:14px 18px; margin-bottom:14px;">',
        f'<h3 style="margin:0 0 8px 0; font-family:Arial,sans-serif; '
        f'font-size:16px; color:#111827;">{company["name"]}</h3>',
    ]
    if company["direct_signals"]:
        parts.append(
            '<p style="margin:0 0 6px 0; font-family:Arial,sans-serif; font-size:14px; '
            'color:#1f2937; line-height:1.5;">'
            '<span style="display:inline-block; background:#0a7d3e; color:#ffffff; '
            'font-size:11px; font-weight:bold; padding:2px 8px; border-radius:10px; '
            'margin-right:8px;">DIRECT SIGNAL</span>'
            f'{company["direct_signals"]}</p>'
        )
    if company["general_news"]:
        parts.append(
            '<p style="margin:0; font-family:Arial,sans-serif; font-size:14px; '
            f'color:#4b5563; line-height:1.5;">{company["general_news"]}</p>'
        )
    parts.append('</div>')
    return "\n".join(parts)


def render_html(results):
    today = date.today().strftime("%A %d %B %Y")

    def tier_header(label, count):
        return (
            f'<h2 style="font-family:Arial,sans-serif; font-size:13px; '
            f'text-transform:uppercase; letter-spacing:1px; color:#ffffff; '
            f'background:#1e3a5f; padding:8px 14px; border-radius:4px; '
            f'margin:28px 0 14px 0;">{label} &nbsp;'
            f'<span style="opacity:0.7; font-weight:normal;">({count})</span></h2>'
        )

    sections = [
        '<div style="max-width:640px; margin:0 auto; padding:20px; '
        'background:#ffffff;">',
        f'<h1 style="font-family:Arial,sans-serif; font-size:22px; '
        f'color:#111827; border-bottom:3px solid #1e3a5f; padding-bottom:10px; '
        f'margin-bottom:4px;">Maritime Job Radar</h1>',
        f'<p style="font-family:Arial,sans-serif; font-size:13px; color:#6b7280; '
        f'margin-top:0;">{today}</p>',
    ]

    sections.append(tier_header("Tier 1", len(results["tier1"])))
    if results["tier1"]:
        sections += [render_company_block(c) for c in results["tier1"]]
    else:
        sections.append(
            '<p style="font-family:Arial,sans-serif; color:#9ca3af; '
            'font-size:14px;">No updates today.</p>'
        )

    sections.append(tier_header("Tier 2", len(results["tier2"])))
    if results["tier2"]:
        sections += [render_company_block(c) for c in results["tier2"]]
    else:
        sections.append(
            '<p style="font-family:Arial,sans-serif; color:#9ca3af; '
            'font-size:14px;">No updates today.</p>'
        )

    sections.append('</div>')
    return "\n".join(sections)


def send_email(html_body):
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": "Maritime Job Radar <onboarding@resend.dev>",
        "to": [TO_EMAIL],
        "subject": f"Maritime Job Radar — {date.today().strftime('%d %b %Y')}",
        "html": html_body,
    }
    resp = requests.post(RESEND_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    if not TO_EMAIL:
        raise SystemExit("DIGEST_TO_EMAIL environment variable is not set.")

    digest_results = build_digest()
    html = render_html(digest_results)
    send_result = send_email(html)
    print("Email sent:", send_result)
