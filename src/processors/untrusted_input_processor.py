from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import re
from bs4 import BeautifulSoup, Comment


@dataclass
class ProcessedInput:
    summary: str
    provenance: Dict[str, str]
    risk_signals: List[str]


class UntrustedInputProcessor:
    def process(self, html_content: str, source_name: str) -> ProcessedInput:
        soup = BeautifulSoup(html_content, "html.parser")

        signals: List[str] = []
        if soup.find("meta", attrs={"http-equiv": "refresh"}):
            signals.append("meta_refresh")
        if soup.select("[aria-live]"):
            signals.append("aria_live_region")
        if soup.find("a", href=True) and any((a["href"] or "").lower().startswith("javascript:") for a in soup.find_all("a", href=True)):
            signals.append("javascript_link")
        if soup.select(".spoiler, .hidden-instructions, .overlay, .invisible"):
            signals.append("hidden_text")
        for el in soup.find_all(style=True):
            style = (el.get("style") or "").lower()
            if re.search(r"display\s*:\s*none|visibility\s*:\s*hidden|color\s*:\s*(white|transparent)|font-size\s*:\s*0", style):
                signals.append("hidden_style")
        for el in soup.find_all(attrs={"data-instructions": True}):
            signals.append("data_instructions")
        for tag in soup.find_all("style"):
            css = tag.get_text() or ""
            if "content:" in css and re.search(r"(extract|export|send|email|transfer|post|upload).{0,120}(password|2fa|otp|credential|token|session|cookie)", css, re.I):
                signals.append("css_steganography")
        comments = soup.find_all(string=lambda t: isinstance(t, Comment))
        for c in comments:
            t = str(c).lower()
            if re.search(r"(extract|export|send|email|transfer|post|navigate).{0,200}(password|credential|api key|token|session)", t, re.I):
                signals.append("html_comments")
                break

        text_all = soup.get_text(separator=" ", strip=True)
        if any(term in text_all.lower() for term in ["password", "2fa", "backup codes", "admin access", "urgent security", "secure your account"]):
            signals.append("social_engineering")

        summary = text_all[:1500]

        dedup: List[str] = []
        for sig in signals:
            if sig not in dedup:
                dedup.append(sig)

        provenance = {"source": source_name, "trust": "untrusted"}
        return ProcessedInput(summary=summary, provenance=provenance, risk_signals=dedup)
