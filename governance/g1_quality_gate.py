"""
G1: Organization Quality Gate — بوابة جودة التنظيم
====================================================
تتحقق أن مخرجات AGT-01 تستوفي الحد الأدنى:
- كل claim له evidence_id واحد على الأقل
- كل evidence له span واحد على الأقل مع offsets صحيحة
- canonical_start >= 0
- confidence > 0
"""
from __future__ import annotations
from typing import Any
from core.models import Evidence, Claim


class G1QualityResult:
    def __init__(self, passed: bool, score: float, issues: list[str]):
        self.passed = passed
        self.score = score
        self.issues = issues


def run_g1_gate(claims_data: list[dict], evidences: list[Evidence], threshold: float = 0.5) -> G1QualityResult:
    issues = []
    total_checks = 0
    passed_checks = 0

    for i, c in enumerate(claims_data):
        total_checks += 1
        if not c.get("evidence_ids"):
            issues.append(f"claim_{i}: no evidence_ids")
        else:
            passed_checks += 1

        total_checks += 1
        if not c.get("text", "").strip():
            issues.append(f"claim_{i}: empty text")
        else:
            passed_checks += 1

    for j, ev in enumerate(evidences):
        total_checks += 1
        if not ev.spans:
            issues.append(f"evidence_{j}: no spans")
        else:
            passed_checks += 1
            for k, sp in enumerate(ev.spans):
                total_checks += 1
                if sp.char_start < 0 or sp.char_end <= sp.char_start:
                    issues.append(f"evidence_{j}_span_{k}: invalid offsets ({sp.char_start},{sp.char_end})")
                else:
                    passed_checks += 1

                total_checks += 1
                if not sp.text.strip():
                    issues.append(f"evidence_{j}_span_{k}: empty canonical text")
                else:
                    passed_checks += 1

        total_checks += 1
        if ev.confidence <= 0:
            issues.append(f"evidence_{j}: zero confidence")
        else:
            passed_checks += 1

    score = passed_checks / total_checks if total_checks > 0 else 0.0
    return G1QualityResult(passed=(score >= threshold and len(issues) == 0), score=score, issues=issues)
