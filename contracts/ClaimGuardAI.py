# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
import json


class ClaimGuardAI(gl.Contract):
    policy_holders: TreeMap[u256, str]
    policy_types: TreeMap[u256, str]
    policy_covered_events: TreeMap[u256, str]
    policy_evidence_sources: TreeMap[u256, str]
    policy_premiums: TreeMap[u256, u256]
    policy_payouts: TreeMap[u256, u256]
    policy_statuses: TreeMap[u256, str]
    policy_reserved: TreeMap[u256, u256]
    policy_disbursed: TreeMap[u256, u256]
    policy_count: u256

    claim_policy_ids: TreeMap[u256, u256]
    claim_claimants: TreeMap[u256, str]
    claim_incident_summaries: TreeMap[u256, str]
    claim_primary_evidence_urls: TreeMap[u256, str]
    claim_extra_evidence_urls: TreeMap[u256, str]
    claim_amounts: TreeMap[u256, u256]
    claim_statuses: TreeMap[u256, str]
    claim_verdicts: TreeMap[u256, str]
    claim_confidences: TreeMap[u256, u256]
    claim_risk_scores: TreeMap[u256, u256]
    claim_reasons: TreeMap[u256, str]
    claim_count: u256

    treasury_recipients: DynArray[str]
    treasury_amounts: DynArray[u256]
    treasury_claim_ids: DynArray[u256]
    treasury_reasons: DynArray[str]
    treasury_count: u256

    appeal_claim_ids: DynArray[u256]
    appeal_reasons: DynArray[str]
    appeal_panel_json: DynArray[str]
    appeal_outcomes: DynArray[str]
    appeal_count: u256

    def __init__(self):
        self.policy_count = u256(0)
        self.claim_count = u256(0)
        self.treasury_count = u256(0)
        self.appeal_count = u256(0)

    @gl.public.write
    def create_policy(
        self,
        holder: str,
        policy_type: str,
        covered_event: str,
        evidence_source: str,
        premium_amount: u256,
        payout_amount: u256,
    ) -> typing.Any:
        if len(holder) == 0:
            return "MISSING_HOLDER"
        if len(policy_type) == 0:
            return "MISSING_POLICY_TYPE"
        if len(covered_event) == 0:
            return "MISSING_COVERED_EVENT"
        if len(evidence_source) == 0:
            return "MISSING_EVIDENCE_SOURCE"
        if premium_amount == u256(0):
            return "ZERO_PREMIUM"
        if payout_amount == u256(0):
            return "ZERO_PAYOUT"

        policy_id = self.policy_count
        self.policy_holders[policy_id] = holder
        self.policy_types[policy_id] = policy_type
        self.policy_covered_events[policy_id] = covered_event
        self.policy_evidence_sources[policy_id] = evidence_source
        self.policy_premiums[policy_id] = premium_amount
        self.policy_payouts[policy_id] = payout_amount
        self.policy_statuses[policy_id] = "ACTIVE"
        self.policy_reserved[policy_id] = payout_amount
        self.policy_disbursed[policy_id] = u256(0)
        self.policy_count = policy_id + u256(1)
        return policy_id

    @gl.public.write
    def close_policy(self, policy_id: u256) -> typing.Any:
        if policy_id >= self.policy_count:
            return "INVALID_POLICY_ID"
        if self.policy_statuses[policy_id] != "ACTIVE":
            return "POLICY_NOT_ACTIVE"
        self.policy_statuses[policy_id] = "CLOSED"
        return "CLOSED"

    @gl.public.write
    def submit_claim(
        self,
        policy_id: u256,
        claimant: str,
        incident_summary: str,
        evidence_url: str,
        claimed_amount: u256,
    ) -> typing.Any:
        if policy_id >= self.policy_count:
            return "INVALID_POLICY_ID"
        if self.policy_statuses[policy_id] != "ACTIVE":
            return "POLICY_NOT_ACTIVE"
        if len(claimant) == 0:
            return "MISSING_CLAIMANT"
        if len(incident_summary) == 0:
            return "MISSING_INCIDENT_SUMMARY"
        if len(evidence_url) == 0:
            return "MISSING_EVIDENCE_URL"
        if claimed_amount == u256(0):
            return "ZERO_CLAIM"
        max_payout = self.policy_payouts[policy_id]
        if claimed_amount > max_payout:
            return "EXCEEDS_POLICY_PAYOUT"
        already_disbursed = self.policy_disbursed[policy_id]
        available = self.policy_reserved[policy_id] - already_disbursed
        if claimed_amount > available:
            return "INSUFFICIENT_POLICY_RESERVE"

        claim_id = self.claim_count
        self.claim_policy_ids[claim_id] = policy_id
        self.claim_claimants[claim_id] = claimant
        self.claim_incident_summaries[claim_id] = incident_summary
        self.claim_primary_evidence_urls[claim_id] = evidence_url
        self.claim_extra_evidence_urls[claim_id] = "[]"
        self.claim_amounts[claim_id] = claimed_amount
        self.claim_statuses[claim_id] = "PENDING"
        self.claim_verdicts[claim_id] = ""
        self.claim_confidences[claim_id] = u256(0)
        self.claim_risk_scores[claim_id] = u256(0)
        self.claim_reasons[claim_id] = ""
        self.claim_count = claim_id + u256(1)
        return claim_id

    @gl.public.write
    def add_evidence(self, claim_id: u256, evidence_url: str) -> typing.Any:
        if claim_id >= self.claim_count:
            return "INVALID_CLAIM_ID"
        status = self.claim_statuses[claim_id]
        if status != "PENDING" and status != "NEED_MORE_EVIDENCE":
            return "CANNOT_ADD_EVIDENCE"
        if len(evidence_url) == 0:
            return "MISSING_EVIDENCE_URL"
        raw = self.claim_extra_evidence_urls[claim_id]
        items = json.loads(raw) if len(raw) > 0 else []
        items.append(evidence_url)
        self.claim_extra_evidence_urls[claim_id] = json.dumps(
            items, sort_keys=True, separators=(",", ":")
        )
        self.claim_statuses[claim_id] = "PENDING"
        return "EVIDENCE_ADDED"

    @gl.public.write
    def evaluate_claim(self, claim_id: u256) -> typing.Any:
        if claim_id >= self.claim_count:
            return "INVALID_CLAIM_ID"
        status = self.claim_statuses[claim_id]
        if status != "PENDING":
            return "INVALID_STATUS"

        policy_id = self.claim_policy_ids[claim_id]
        if self.policy_statuses[policy_id] != "ACTIVE":
            return "POLICY_NOT_ACTIVE"
        amount = self.claim_amounts[claim_id]
        max_payout = self.policy_payouts[policy_id]
        if amount > max_payout:
            return "EXCEEDS_POLICY_PAYOUT"
        already_disbursed = self.policy_disbursed[policy_id]
        available = self.policy_reserved[policy_id] - already_disbursed
        if amount > available:
            return "INSUFFICIENT_POLICY_RESERVE"

        holder = self.policy_holders[policy_id]
        policy_type = self.policy_types[policy_id]
        covered_event = self.policy_covered_events[policy_id]
        official_source = self.policy_evidence_sources[policy_id]
        claimant = self.claim_claimants[claim_id]
        incident_summary = self.claim_incident_summaries[claim_id]
        primary_evidence_url = self.claim_primary_evidence_urls[claim_id]
        extra_evidence_raw = self.claim_extra_evidence_urls[claim_id]
        extra_evidence_urls = json.loads(extra_evidence_raw) if len(extra_evidence_raw) > 0 else []

        def truncate(text, limit):
            if len(text) > limit:
                return text[:limit]
            return text

        def run_evaluation() -> str:
            official_content = ""
            if len(official_source) > 0:
                try:
                    resp = gl.nondet.web.get(official_source)
                    official_content = resp.body.decode("utf-8")
                except Exception:
                    official_content = "[FETCH_FAILED:official_source]"

            primary_content = ""
            if len(primary_evidence_url) > 0:
                try:
                    resp = gl.nondet.web.get(primary_evidence_url)
                    primary_content = resp.body.decode("utf-8")
                except Exception:
                    primary_content = "[FETCH_FAILED:primary_evidence]"

            extra_sections = []
            for idx in range(len(extra_evidence_urls)):
                url = extra_evidence_urls[idx]
                if len(url) > 0:
                    try:
                        r = gl.nondet.web.get(url)
                        body = r.body.decode("utf-8")
                        extra_sections.append(
                            "=== Extra Evidence {} ({}) ===\n{}".format(
                                idx + 1, url, truncate(body, 2500)
                            )
                        )
                    except Exception:
                        extra_sections.append(
                            "=== Extra Evidence {} ({}) === [FETCH_FAILED]".format(
                                idx + 1, url
                            )
                        )
            extra_evidence_block = "\n\n".join(extra_sections)

            prompt = (
                "You are ClaimGuardAI, a GenLayer insurance adjudicator. "
                "Your decision releases or blocks a real policy payout, so be strict, "
                "evidence-based, and conservative when evidence is weak.\n\n"
                "=== POLICY ===\n"
                "Policy Holder: " + holder + "\n"
                "Policy Type: " + policy_type + "\n"
                "Covered Event: " + covered_event + "\n"
                "Maximum Payout: " + str(amount) + " requested of " + str(max_payout) + "\n\n"
                "=== CLAIM ===\n"
                "Claimant: " + claimant + "\n"
                "Incident Summary: " + incident_summary + "\n"
                "Primary Evidence URL: " + primary_evidence_url + "\n\n"
                "=== OFFICIAL SOURCE (" + official_source + ") ===\n"
                + truncate(official_content, 4000) + "\n\n"
                "=== PRIMARY EVIDENCE ===\n"
                + truncate(primary_content, 4000) + "\n\n"
                "=== EXTRA EVIDENCE ===\n"
                + extra_evidence_block + "\n\n"
                "=== SCORING ===\n"
                "event_match_score: 0-100, whether the web evidence proves the covered event happened.\n"
                "claimant_match_score: 0-100, whether evidence links the claimant/policy to the event.\n"
                "source_reliability_score: 0-100, official carrier/event/logistics source quality.\n"
                "fraud_risk_score: 0-100, contradictions, suspicious timing, forged-looking evidence.\n"
                "confidence: 1-10.\n\n"
                "Decision thresholds:\n"
                "APPROVE if event_match_score >= 80, claimant_match_score >= 60, "
                "source_reliability_score >= 65, fraud_risk_score < 35, and confidence >= 7.\n"
                "NEED_MORE_EVIDENCE if event_match_score >= 50 but claimant_match_score < 60, "
                "or confidence is 4-6, or critical official pages failed to load.\n"
                "REJECT otherwise.\n\n"
                "Respond with ONLY this JSON, no other text or explanation:\n"
                '{"decision":"APPROVE|REJECT|NEED_MORE_EVIDENCE",'
                '"event_match_score":N,'
                '"claimant_match_score":N,'
                '"source_reliability_score":N,'
                '"fraud_risk_score":N,'
                '"confidence":N,'
                '"payout_recommendation":"FULL|NONE|MORE_EVIDENCE",'
                '"reason":"1-2 sentence evidence-based reason"}'
            )
            answer = gl.nondet.exec_prompt(prompt)
            return answer.replace("```json", "").replace("```", "").strip()

        evaluation_json = gl.eq_principle.strict_eq(run_evaluation)

        try:
            data = json.loads(evaluation_json)
        except Exception:
            return "INVALID_EVALUATION_JSON"

        decision = str(data.get("decision", ""))
        if decision not in ["APPROVE", "REJECT", "NEED_MORE_EVIDENCE"]:
            return "INVALID_DECISION"
        confidence = int(data.get("confidence", 0))
        fraud_risk = int(data.get("fraud_risk_score", 100))
        if confidence < 1 or confidence > 10:
            return "INVALID_CONFIDENCE"
        if fraud_risk < 0 or fraud_risk > 100:
            return "INVALID_RISK_SCORE"

        self.claim_verdicts[claim_id] = json.dumps(data, sort_keys=True, separators=(",", ":"))
        self.claim_confidences[claim_id] = u256(confidence)
        self.claim_risk_scores[claim_id] = u256(fraud_risk)
        self.claim_reasons[claim_id] = str(data.get("reason", ""))

        if decision == "APPROVE":
            self.claim_statuses[claim_id] = "APPROVED"
        elif decision == "NEED_MORE_EVIDENCE":
            self.claim_statuses[claim_id] = "NEED_MORE_EVIDENCE"
        else:
            self.claim_statuses[claim_id] = "REJECTED"

        return self.claim_verdicts[claim_id]

    @gl.public.write
    def execute_payout(self, claim_id: u256) -> typing.Any:
        if claim_id >= self.claim_count:
            return "INVALID_CLAIM_ID"
        status = self.claim_statuses[claim_id]
        if status != "APPROVED":
            return "NOT_APPROVED"

        policy_id = self.claim_policy_ids[claim_id]
        amount = self.claim_amounts[claim_id]
        max_payout = self.policy_payouts[policy_id]
        if amount > max_payout:
            return "EXCEEDS_POLICY_PAYOUT"

        already_disbursed = self.policy_disbursed[policy_id]
        reserve = self.policy_reserved[policy_id]
        new_disbursed = already_disbursed + amount
        if new_disbursed > reserve:
            return "INSUFFICIENT_POLICY_RESERVE"

        self.policy_disbursed[policy_id] = new_disbursed
        self.treasury_recipients.append(self.claim_claimants[claim_id])
        self.treasury_amounts.append(amount)
        self.treasury_claim_ids.append(claim_id)
        self.treasury_reasons.append(self.claim_reasons[claim_id])
        self.treasury_count = self.treasury_count + u256(1)
        self.claim_statuses[claim_id] = "PAID"
        return "PAID"

    @gl.public.write
    def challenge_claim(self, claim_id: u256, reason: str) -> typing.Any:
        if claim_id >= self.claim_count:
            return "INVALID_CLAIM_ID"
        status = self.claim_statuses[claim_id]
        if status != "REJECTED" and status != "NEED_MORE_EVIDENCE":
            return "NOT_CHALLENGEABLE"
        if len(reason) == 0:
            return "MISSING_CHALLENGE_REASON"
        self.claim_statuses[claim_id] = "CHALLENGED"
        appeal_id = self.appeal_count
        self.appeal_claim_ids.append(claim_id)
        self.appeal_reasons.append(reason)
        self.appeal_panel_json.append("")
        self.appeal_outcomes.append("PENDING")
        self.appeal_count = appeal_id + u256(1)
        return appeal_id

    @gl.public.write
    def resolve_challenge(self, claim_id: u256) -> typing.Any:
        if claim_id >= self.claim_count:
            return "INVALID_CLAIM_ID"
        if self.claim_statuses[claim_id] != "CHALLENGED":
            return "NOT_IN_CHALLENGE"

        policy_id = self.claim_policy_ids[claim_id]
        covered_event = self.policy_covered_events[policy_id]
        official_source = self.policy_evidence_sources[policy_id]
        incident_summary = self.claim_incident_summaries[claim_id]
        evidence_url = self.claim_primary_evidence_urls[claim_id]
        original_verdict = self.claim_verdicts[claim_id]
        amount = self.claim_amounts[claim_id]

        def challenge_panel() -> str:
            official_content = ""
            try:
                resp = gl.nondet.web.get(official_source)
                official_content = resp.body.decode("utf-8")
            except Exception:
                official_content = "[FETCH_FAILED:official_source]"
            evidence_content = ""
            try:
                resp = gl.nondet.web.get(evidence_url)
                evidence_content = resp.body.decode("utf-8")
            except Exception:
                evidence_content = "[FETCH_FAILED:evidence]"
            prompt = (
                "You are an insurance appeal panel for ClaimGuardAI. "
                "Review the original verdict for semantic correctness, not JSON format.\n\n"
                "Covered Event: " + covered_event + "\n"
                "Claimed Amount: " + str(amount) + "\n"
                "Incident: " + incident_summary + "\n"
                "Original Verdict: " + original_verdict + "\n\n"
                "Official Source:\n" + official_content[:4000] + "\n\n"
                "Claim Evidence:\n" + evidence_content[:4000] + "\n\n"
                "Respond with ONLY this JSON:\n"
                '{"appeal_decision":"UPHOLD|OVERTURN_APPROVE|OVERTURN_REJECT",'
                '"confidence":N,'
                '"reason":"1-2 sentence reason"}'
            )
            return gl.nondet.exec_prompt(prompt).replace("```json", "").replace("```", "").strip()

        panel_json = gl.eq_principle.strict_eq(challenge_panel)
        try:
            panel = json.loads(panel_json)
        except Exception:
            return "INVALID_PANEL_JSON"
        appeal_decision = str(panel.get("appeal_decision", ""))
        if appeal_decision not in ["UPHOLD", "OVERTURN_APPROVE", "OVERTURN_REJECT"]:
            return "INVALID_APPEAL_DECISION"

        idx = self.appeal_count
        self.appeal_claim_ids.append(claim_id)
        self.appeal_reasons.append("RESOLUTION")
        self.appeal_panel_json.append(json.dumps(panel, sort_keys=True, separators=(",", ":")))
        self.appeal_outcomes.append(appeal_decision)
        self.appeal_count = idx + u256(1)

        if appeal_decision == "OVERTURN_APPROVE":
            self.claim_statuses[claim_id] = "APPROVED"
        elif appeal_decision == "OVERTURN_REJECT":
            self.claim_statuses[claim_id] = "REJECTED"
        else:
            original_status = "REJECTED"
            try:
                original = json.loads(original_verdict)
                if str(original.get("decision", "")) == "NEED_MORE_EVIDENCE":
                    original_status = "NEED_MORE_EVIDENCE"
            except Exception:
                original_status = "REJECTED"
            self.claim_statuses[claim_id] = original_status
        return self.claim_statuses[claim_id]

    @gl.public.view
    def get_policy(self, policy_id: u256) -> str:
        if policy_id >= self.policy_count:
            return json.dumps({"error": "INVALID_POLICY_ID"}, sort_keys=True, separators=(",", ":"))
        obj = {
            "covered_event": self.policy_covered_events[policy_id],
            "disbursed": str(self.policy_disbursed[policy_id]),
            "evidence_source": self.policy_evidence_sources[policy_id],
            "holder": self.policy_holders[policy_id],
            "payout": str(self.policy_payouts[policy_id]),
            "policy_id": str(policy_id),
            "policy_type": self.policy_types[policy_id],
            "premium": str(self.policy_premiums[policy_id]),
            "reserved": str(self.policy_reserved[policy_id]),
            "status": self.policy_statuses[policy_id],
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"))

    @gl.public.view
    def get_claim(self, claim_id: u256) -> str:
        if claim_id >= self.claim_count:
            return json.dumps({"error": "INVALID_CLAIM_ID"}, sort_keys=True, separators=(",", ":"))
        obj = {
            "amount": str(self.claim_amounts[claim_id]),
            "claim_id": str(claim_id),
            "claimant": self.claim_claimants[claim_id],
            "confidence": str(self.claim_confidences[claim_id]),
            "evidence_url": self.claim_primary_evidence_urls[claim_id],
            "extra_evidence_urls": json.loads(self.claim_extra_evidence_urls[claim_id]),
            "incident_summary": self.claim_incident_summaries[claim_id],
            "policy_id": str(self.claim_policy_ids[claim_id]),
            "reason": self.claim_reasons[claim_id],
            "risk_score": str(self.claim_risk_scores[claim_id]),
            "status": self.claim_statuses[claim_id],
            "verdict": self.claim_verdicts[claim_id],
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"))

    @gl.public.view
    def get_policy_count(self) -> u256:
        return self.policy_count

    @gl.public.view
    def get_claim_count(self) -> u256:
        return self.claim_count

    @gl.public.view
    def get_claim_status(self, claim_id: u256) -> str:
        if claim_id >= self.claim_count:
            return "INVALID_CLAIM_ID"
        return self.claim_statuses[claim_id]

    @gl.public.view
    def get_treasury_count(self) -> u256:
        return self.treasury_count

    @gl.public.view
    def get_treasury_record(self, index: u256) -> str:
        if index >= self.treasury_count:
            return json.dumps({"error": "INVALID_TREASURY_INDEX"}, sort_keys=True, separators=(",", ":"))
        obj = {
            "amount": str(self.treasury_amounts[index]),
            "claim_id": str(self.treasury_claim_ids[index]),
            "reason": self.treasury_reasons[index],
            "recipient": self.treasury_recipients[index],
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"))
