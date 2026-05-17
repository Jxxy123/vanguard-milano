import json
import hashlib
import asyncio
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

import google.generativeai as genai

from src.config import config
from src.models import RerouteManifest


# ─────────────────────────────────────────────────────────────────────────────
#  STATE MANAGER  — thread-safe enough for single-worker hackathon deployment
# ─────────────────────────────────────────────────────────────────────────────
class VanguardState:
    is_demo:     bool = False
    agent_steps: list = []

    @classmethod
    def reset(cls):
        cls.agent_steps = []
        cls.is_demo     = False

    @classmethod
    def log(cls, title: str, detail: str, status: str = "ok") -> None:
        """Appends a structured step to the trace log and prints for server stdout."""
        cls.agent_steps.append({
            "step":   title,
            "detail": detail,
            "status": status,
            "ts":     datetime.now(timezone.utc).strftime("%H:%M:%S"),
        })
        print(f"[VANGUARD][{status.upper():7s}] {title} | {detail}")


# ─────────────────────────────────────────────────────────────────────────────
#  NEWS FEED CONFIG
#  Using ANSA (Italian national news agency) + BBC Europe as primary sources.
#  Keywords cover both English and Italian transport terminology.
# ─────────────────────────────────────────────────────────────────────────────
_NEWS_FEEDS = [
    "https://www.ansa.it/sito/notizie/economia/economia_rss.xml",   # ANSA Economy
    "https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml",     # ANSA News
    "http://feeds.bbci.co.uk/news/world/europe/rss.xml",            # BBC Europe
]
_TRANSPORT_KEYWORDS = [
    "strike", "sciopero", "transport", "trasporto", "rail", "railway",
    "ferroviario", "freight", "merci", "port", "porto", "logistics",
    "logistica", "disruption", "delay", "ritardo", "blocked", "union",
    "sindacato", "autotrasporto", "trenitalia", "genoa", "genova",
    "milan", "milano", "turin", "torino",
]


# ─────────────────────────────────────────────────────────────────────────────
#  AGENT TOOLS  — registered with Gemini via enable_automatic_function_calling
# ─────────────────────────────────────────────────────────────────────────────

def search_live_news(query: str) -> str:
    """
    Searches live Italian and European news feeds for active transport strikes,
    port disruptions, or rail delays affecting Northern Italy.
    Returns a plain-text summary of relevant headlines.
    """
    VanguardState.log("🔍 Scanning Live News Feeds", f"Query: '{query}'", "running")

    # ── DEMO PATH ──────────────────────────────────────────────────────────
    if VanguardState.is_demo:
        VanguardState.log("🎬 Demo Scenario Loaded", "Injected 48-hr national rail & road strike", "ok")
        return (
            "BREAKING — DEMO SCENARIO: Italian transport unions (CGIL/CISL/UIL) have declared "
            "a 48-hour national rail and road-freight strike effective May 17-18, 2026, severely "
            "impacting the Milan-Genoa-Turin logistics triangle. Port of Genoa operating at 15% "
            "capacity. All Trenitalia Frecciarossa north of Bologna suspended. Motorway A7 "
            "(Milan-Genoa) sees 40km tailbacks from blockades at Serravalle Scrivia."
        )

    # ── LIVE PATH ──────────────────────────────────────────────────────────
    VanguardState.log("🌐 Polling RSS Feeds", "ANSA Economy · ANSA News · BBC Europe", "running")
    collected = []

    for feed_url in _NEWS_FEEDS:
        try:
            resp = requests.get(
                feed_url,
                timeout=7,
                headers={"User-Agent": "VanguardMilano/2.0 (hackathon agent)"}
            )
            root = ET.fromstring(resp.content)
            for item in root.findall("./channel/item")[:10]:
                title = (item.findtext("title") or "").strip()
                desc  = (item.findtext("description") or "").strip()
                if any(kw in f"{title} {desc}".lower() for kw in _TRANSPORT_KEYWORDS):
                    collected.append(f"• {title}: {desc[:140]}")
        except Exception as exc:
            VanguardState.log("⚠️ Feed Unavailable", f"{feed_url[:45]}… — {exc}", "warning")

    if collected:
        VanguardState.log("✅ Transport Intelligence Retrieved", f"{len(collected)} relevant articles indexed", "ok")
        return "LIVE TRANSPORT INTELLIGENCE:\n" + "\n".join(collected[:6])

    VanguardState.log("✅ All Feeds Clear", "No active transport disruptions in Italian news", "ok")
    return "No current transport strikes or disruptions found in Italian news feeds."


def check_hub_capacity(hub_name: str) -> str:
    """
    Checks real-time freight slot availability at alternative Northern Italian logistics hubs.
    In production this connects to TimoCom / Teleroute freight-exchange APIs.
    """
    VanguardState.log("📦 Checking Hub Capacity", f"Hub: {hub_name}", "running")

    capacities = {
        "Turin":    "Available — 450 TEU capacity, 24-hr operations, fast customs lane",
        "Verona":   "Limited — 20 TEU residual capacity, priority cargo only",
        "Genoa":    "Blocked — Port workers' strike active, no intake until further notice",
        "Piacenza": "Available — 310 TEU capacity, multimodal rail/road connection open",
        "Bologna":  "Available — 520 TEU capacity, Interporto Bologna fully operational",
        "Brescia":  "Available — 180 TEU capacity, 12-hr operations",
    }
    status = capacities.get(
        hub_name,
        f"Hub '{hub_name}' not in network registry — manual verification required"
    )
    VanguardState.log("✅ Capacity Data Retrieved", f"{hub_name}: {status[:65]}", "ok")
    return status


def execute_x402_settlement(amount: float, recipient: str, reason: str) -> dict:
    """
    Executes a programmable X402 USDC smart-contract payment to instantly secure
    emergency logistics capacity at an alternative hub.
    (Simulation layer — production integrates with Coinbase CDP Wallet API.)
    """
    VanguardState.log("💸 Initiating X402 Settlement", f"{amount:,.2f} USDC → {recipient}", "running")

    # Deterministic, reproducible IDs using hashlib (no Python hash() randomisation)
    payload_str = f"{recipient}|{amount}|{reason}"
    tx_id    = "X402-" + hashlib.sha256(payload_str.encode()).hexdigest()[:8].upper() + "-VANGUARD"
    block_ref = "0x"   + hashlib.md5(tx_id.encode()).hexdigest()[:16]

    result = {
        "transaction_id": tx_id,
        "amount":         amount,
        "currency":       "USDC",
        "recipient":      recipient,
        "status":         "Settled Instantaneously",
        "block_ref":      block_ref,
        "reason":         reason,
    }
    VanguardState.log("✅ Settlement Confirmed", f"TX: {tx_id} | {amount:,.2f} USDC", "ok")
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  AGENT CLASS
# ─────────────────────────────────────────────────────────────────────────────
class VanguardAgent:
    def __init__(self):
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=[search_live_news, check_hub_capacity, execute_x402_settlement],
            system_instruction=(
                "You are VANGUARD MILANO, an autonomous logistics orchestrator protecting "
                "Northern Italian supply chains. Your strict execution order:\n"
                "1. ALWAYS call search_live_news first with query 'Italy transport strike today'.\n"
                "2. Based on the news, call check_hub_capacity for each candidate alternative hub.\n"
                "3. ONLY IF a strike is confirmed AND threat level is High or Critical: "
                "call execute_x402_settlement to secure emergency capacity.\n"
                "4. Return your final assessment as a single raw JSON object — "
                "no markdown fences, no preamble, just valid JSON."
            )
        )

    async def analyze_strikes(
        self,
        demo_mode:      bool            = False,
        document_bytes: Optional[bytes] = None,
        mime_type:      Optional[str]   = None,
    ) -> RerouteManifest:

        VanguardState.reset()
        VanguardState.is_demo = demo_mode
        VanguardState.log(
            "🚀 Agent Initialized",
            f"VANGUARD v2.0 online — {'🎬 Demo' if demo_mode else '🌍 Live'} Mode",
            "ok"
        )

        # ── Build multimodal payload ───────────────────────────────────────
        payload = []

        if document_bytes and mime_type:
            VanguardState.log(
                "📄 Cargo Manifest Uploaded",
                f"Analysing via Gemini Vision ({mime_type})",
                "running"
            )
            payload.append({"mime_type": mime_type, "data": document_bytes})
            payload.append(
                "A shipping manifest has been uploaded. "
                "Analyse the cargo contents first — identify high-value or perishable items. "
                "Factor these into your threat assessment and elevate strike_level to Critical "
                "if the cargo cannot tolerate any delay."
            )

        if demo_mode:
            payload.append(
                "SIMULATION CONTEXT: A Critical national strike is confirmed. "
                "Check Turin and Bologna hub capacities. "
                "Execute X402 payment of 2500 USDC to 'Turin Interporto' to secure emergency slots."
            )

        payload.append(
            "Execute your full autonomous threat assessment now. "
            "Return a single raw JSON object matching this schema exactly:\n"
            "{\n"
            '  "strike_detected": bool,\n'
            '  "strike_level": "None|Low|Medium|High|Critical",\n'
            '  "affected_routes": ["string"],\n'
            '  "alternative_hubs": [{"name":"string","location":"string","capacity_status":"string"}],\n'
            '  "rerouting_plan": "string",\n'
            '  "payment_settlement": null | {"transaction_id":"string","amount":number,'
            '"currency":"USDC","recipient":"string","status":"string","reason":"string"},\n'
            f'  "timestamp": "{datetime.now(timezone.utc).isoformat()}"\n'
            "}"
        )

        try:
            VanguardState.log(
                "🧠 Agentic Loop Started",
                "Gemini 2.5 Flash — automatic tool-call execution enabled",
                "running"
            )

            # ── Retry loop — handles 429 quota exceeded with exponential backoff ──
            _MAX_RETRIES = 3
            response = None
            for _attempt in range(_MAX_RETRIES):
                try:
                    chat     = self.model.start_chat(enable_automatic_function_calling=True)
                    response = chat.send_message(payload)
                    break   # success — exit retry loop
                except Exception as _exc:
                    _err = str(_exc).lower()
                    _is_quota = any(kw in _err for kw in ["429", "quota", "resource exhausted", "rate limit"])
                    if _is_quota and _attempt < _MAX_RETRIES - 1:
                        _wait = 20 * (2 ** _attempt)   # 20 s → 40 s → 80 s
                        VanguardState.log(
                            "⏳ API Rate Limit — Retrying",
                            f"Quota exceeded. Waiting {_wait}s (attempt {_attempt + 1}/{_MAX_RETRIES - 1})",
                            "warning"
                        )
                        await asyncio.sleep(_wait)
                    else:
                        raise   # non-quota error or out of retries — propagate

            VanguardState.log("📊 Compiling Reroute Manifest", "Parsing structured agent output", "running")

            text  = response.text.strip()
            start = text.find("{")
            end   = text.rfind("}") + 1
            if start != -1 and end > start:
                text = text[start:end]

            data     = json.loads(text)
            manifest = RerouteManifest(**data)

            if manifest.strike_detected:
                VanguardState.log(
                    "🎯 Mission Complete",
                    f"Threat Level: {manifest.strike_level} — Supply chain secured",
                    "ok"
                )
            else:
                VanguardState.log("✅ All Clear", "No active disruptions — Network nominal", "ok")

            return manifest

        except Exception as exc:
            VanguardState.log("🔥 Agent Error", str(exc), "error")
            try:
                print(f"[VANGUARD][DEBUG] Raw model output: {response.text}")
            except Exception:
                pass
            return RerouteManifest(
                strike_detected=False,
                strike_level="Error",
                affected_routes=[],
                alternative_hubs=[],
                rerouting_plan=f"Agent error: {exc}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )


agent = VanguardAgent()