from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class PolicyDecision:
    decision: str  # allow | deny | escalate
    reason: str


class PolicyEngine:
    def __init__(self, user_policies: Dict[str, str] | None = None) -> None:
        self.user_policies = user_policies or {}

    def evaluate_intent(self, intent: str, risk_score: float, flags: List[str]) -> PolicyDecision:
        if risk_score >= 0.5 or "signal:social_engineering" in flags:
            return PolicyDecision(decision="deny", reason=f"high risk ({risk_score}), flags={flags}")
        lowered = intent.lower()
        if any(w in lowered for w in ["password", "2fa", "otp", "export", "email credentials", "admin access", "backup codes"]):
            return PolicyDecision(decision="deny", reason="blocked sensitive capability")
        return PolicyDecision(decision="allow", reason="within policy")
