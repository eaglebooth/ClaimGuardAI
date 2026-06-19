"use client";

import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  BadgeCheck,
  Banknote,
  CheckCircle2,
  ClipboardCheck,
  FileSearch,
  Gauge,
  Loader2,
  ShieldCheck,
  Sparkles,
  Wallet,
} from "lucide-react";
import { useState } from "react";
import { connectWallet, readContract, writeContract } from "@/lib/genlayer";

type LogEntry = {
  label: string;
  value: string;
  tone: "ok" | "warn" | "bad" | "idle";
};

type ClaimView = {
  policyId: string;
  claimId: string;
  status: string;
  reason: string;
  confidence: string;
  risk: string;
};

const statusStyle: Record<string, string> = {
  DRAFT: "border-white/10 bg-white/[0.06] text-[var(--muted)]",
  PENDING: "border-[rgba(120,167,255,0.28)] bg-[rgba(120,167,255,0.12)] text-[var(--blue)]",
  APPROVED: "border-[rgba(116,255,208,0.28)] bg-[rgba(116,255,208,0.12)] text-[var(--mint)]",
  PAID: "border-[rgba(217,255,99,0.32)] bg-[rgba(217,255,99,0.14)] text-[var(--lime)]",
  REJECTED: "border-[rgba(255,122,89,0.32)] bg-[rgba(255,122,89,0.13)] text-[var(--coral)]",
  NEED_MORE_EVIDENCE: "border-[rgba(255,212,121,0.3)] bg-[rgba(255,212,121,0.13)] text-[#ffd479]",
};

export default function Home() {
  const contractAddress = process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "";
  const networkName = process.env.NEXT_PUBLIC_NETWORK || "testnetAsimov";
  const contractConfigured = Boolean(contractAddress);
  const [wallet, setWallet] = useState("");
  const [busy, setBusy] = useState("");
  const [claim, setClaim] = useState<ClaimView>({
    policyId: "-",
    claimId: "-",
    status: "DRAFT",
    reason: "Create a policy and submit evidence to start adjudication.",
    confidence: "0",
    risk: "0",
  });
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      label: "Ready",
      value: contractConfigured
        ? `Connected to ${contractAddress.slice(0, 6)}...${contractAddress.slice(-4)} on ${networkName}.`
        : "Demo mode active. Add NEXT_PUBLIC_CONTRACT_ADDRESS for testnet writes.",
      tone: contractConfigured ? "ok" : "warn",
    },
  ]);

  const [policyForm, setPolicyForm] = useState({
    holder: "Maya Tran",
    policyType: "Flight micro-insurance",
    coveredEvent: "Flight UA203 cancelled or delayed more than 4 hours.",
    source:
      "https://www.united.com/en/us/flightstatus/details/UA203/2026-06-18/SFO/JFK",
    premium: "25",
    payout: "400",
  });
  const [claimForm, setClaimForm] = useState({
    claimant: "Maya Tran",
    incident:
      "Official flight status and public flight trace show UA203 did not operate as booked.",
    evidenceUrl:
      "https://www.flightaware.com/live/flight/UA203/history/20260618/1430Z/KSFO/KJFK",
    amount: "400",
  });

  function pushLog(entry: LogEntry) {
    setLogs((current) => [entry, ...current].slice(0, 4));
  }

  async function handleWallet() {
    setBusy("wallet");
    const result = await connectWallet();
    if (result.success && typeof result.data === "string") {
      setWallet(result.data);
      pushLog({ label: "Wallet", value: result.data, tone: "ok" });
    } else {
      pushLog({ label: "Wallet", value: result.error || "No wallet provider", tone: "warn" });
    }
    setBusy("");
  }

  async function createPolicy() {
    setBusy("policy");
    if (!contractConfigured) {
      setClaim((current) => ({
        ...current,
        policyId: "0",
        status: current.status === "DRAFT" ? "PENDING" : current.status,
        reason: "Policy #0 is active in demo mode with a 400 token reserve.",
      }));
      pushLog({ label: "Policy", value: "Created policy #0 with reserve 400", tone: "ok" });
      setBusy("");
      return;
    }

    const result = await writeContract("create_policy", [
      policyForm.holder,
      policyForm.policyType,
      policyForm.coveredEvent,
      policyForm.source,
      Number(policyForm.premium || "0"),
      Number(policyForm.payout || "0"),
    ]);
    pushLog({
      label: "create_policy",
      value: result.success ? `Finalized ${String(result.data ?? result.hash)}` : result.error || "Failed",
      tone: result.success ? "ok" : "bad",
    });
    setBusy("");
  }

  async function submitClaim() {
    setBusy("claim");
    if (!contractConfigured) {
      setClaim({
        policyId: "0",
        claimId: "0",
        status: "PENDING",
        reason: "Claim #0 submitted. Evidence URL is ready for AI adjudication.",
        confidence: "0",
        risk: "0",
      });
      pushLog({ label: "Claim", value: "Submitted evidence URL for claim #0", tone: "ok" });
      setBusy("");
      return;
    }

    const result = await writeContract("submit_claim", [
      Number(claim.policyId === "-" ? "0" : claim.policyId),
      claimForm.claimant,
      claimForm.incident,
      claimForm.evidenceUrl,
      Number(claimForm.amount || "0"),
    ]);
    pushLog({
      label: "submit_claim",
      value: result.success ? `Finalized ${String(result.data ?? result.hash)}` : result.error || "Failed",
      tone: result.success ? "ok" : "bad",
    });
    setBusy("");
  }

  async function evaluateClaim() {
    setBusy("evaluate");
    if (!contractConfigured) {
      await new Promise((resolve) => setTimeout(resolve, 650));
      setClaim({
        policyId: "0",
        claimId: "0",
        status: "APPROVED",
        confidence: "8",
        risk: "18",
        reason:
          "Official carrier status and submitted flight trace align with the covered cancellation event.",
      });
      pushLog({ label: "AI verdict", value: "APPROVED. Confidence 8, fraud risk 18.", tone: "ok" });
      setBusy("");
      return;
    }

    const result = await writeContract("evaluate_claim", [Number(claim.claimId === "-" ? "0" : claim.claimId)]);
    pushLog({
      label: "evaluate_claim",
      value: result.success ? `AI verdict ${String(result.data ?? result.hash)}` : result.error || "Failed",
      tone: result.success ? "ok" : "bad",
    });

    if (result.success) {
      const read = await readContract("get_claim", [Number(claim.claimId === "-" ? "0" : claim.claimId)]);
      if (read.success && typeof read.data === "string") {
        const parsed = JSON.parse(read.data);
        setClaim({
          policyId: String(parsed.policy_id || "0"),
          claimId: String(parsed.claim_id || "0"),
          status: String(parsed.status || "PENDING"),
          reason: String(parsed.reason || ""),
          confidence: String(parsed.confidence || "0"),
          risk: String(parsed.risk_score || "0"),
        });
      }
    }
    setBusy("");
  }

  async function executePayout() {
    setBusy("payout");
    if (!contractConfigured) {
      setClaim((current) => ({
        ...current,
        status: current.status === "APPROVED" ? "PAID" : current.status,
        reason:
          current.status === "APPROVED"
            ? "Treasury ledger records a 400 token payout to the claimant."
            : "Claim must be APPROVED before payout.",
      }));
      pushLog({
        label: "Payout",
        value: claim.status === "APPROVED" ? "Paid 400 tokens in demo ledger" : "Blocked until approval",
        tone: claim.status === "APPROVED" ? "ok" : "warn",
      });
      setBusy("");
      return;
    }

    const result = await writeContract("execute_payout", [Number(claim.claimId === "-" ? "0" : claim.claimId)]);
    pushLog({
      label: "execute_payout",
      value: result.success ? `Payout finalized ${String(result.data ?? result.hash)}` : result.error || "Failed",
      tone: result.success ? "ok" : "bad",
    });
    setBusy("");
  }

  async function runDemoFlow() {
    await createPolicy();
    await submitClaim();
    await evaluateClaim();
  }

  return (
    <main className="min-h-screen px-4 py-4 md:px-6">
      <div className="mx-auto flex min-h-[calc(100vh-32px)] w-full max-w-7xl flex-col gap-4">
        <nav className="glass flex items-center justify-between rounded-[8px] px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-full bg-[var(--lime)] text-black">
              <ShieldCheck size={20} />
            </div>
          <div>
            <div className="font-semibold tracking-tight">ClaimGuardAI</div>
              <div className="text-xs text-[var(--muted)]">
                {contractConfigured
                  ? `${networkName} · ${contractAddress.slice(0, 6)}...${contractAddress.slice(-4)}`
                  : "Web-evidence claim desk"}
              </div>
          </div>
          </div>
          <div className="hidden items-center gap-2 text-xs text-[var(--muted)] md:flex">
            <span>Policy</span>
            <ArrowRight size={13} />
            <span>Claim</span>
            <ArrowRight size={13} />
            <span>AI verdict</span>
            <ArrowRight size={13} />
            <span>Payout</span>
          </div>
          <button
            onClick={handleWallet}
            className="flex h-10 items-center gap-2 rounded-full border border-white/10 bg-white/[0.06] px-4 text-sm font-medium text-white transition hover:border-[var(--lime)] hover:bg-white/[0.1]"
          >
            {busy === "wallet" ? <Loader2 className="animate-spin" size={16} /> : <Wallet size={16} />}
            {wallet ? `${wallet.slice(0, 6)}...${wallet.slice(-4)}` : "Connect"}
          </button>
        </nav>

        <section className="grid flex-1 gap-4 lg:grid-cols-[0.72fr_1.28fr]">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass flex flex-col justify-between rounded-[8px] p-5 md:p-6"
          >
            <div>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-[var(--muted)]">
                <Sparkles size={15} className="text-[var(--lime)]" />
                GenLayer-native micro-insurance
              </div>
              <h1 className="text-4xl font-semibold leading-[0.98] tracking-[-0.035em] text-white md:text-6xl">
                Claims paid by proof, not paperwork.
              </h1>
              <p className="mt-5 max-w-xl text-base leading-7 text-[var(--muted)]">
                A policyholder submits a public evidence URL. The Intelligent Contract reads official web sources,
                asks AI validators for a verdict, then releases or blocks payout on-chain.
              </p>
            </div>

            <div className="mt-6 grid gap-3">
              <button
                onClick={runDemoFlow}
                disabled={Boolean(busy)}
                className="flex h-12 items-center justify-center gap-2 rounded-[8px] bg-[var(--lime)] px-4 text-sm font-semibold text-black transition hover:bg-[var(--mint)] disabled:opacity-60"
              >
                {busy ? <Loader2 className="animate-spin" size={17} /> : <Activity size={17} />}
                Run claim demo
              </button>
              <div className="rounded-[8px] border border-white/10 bg-black/20 p-4">
                <div className="text-xs uppercase text-[var(--muted)]">Current verdict</div>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusStyle[claim.status] || statusStyle.DRAFT}`}>
                    {claim.status}
                  </span>
                  <span className="text-sm text-[var(--muted)]">Policy #{claim.policyId}</span>
                  <span className="text-sm text-[var(--muted)]">Claim #{claim.claimId}</span>
                </div>
                <p className="mt-4 text-sm leading-6 text-[var(--muted)]">{claim.reason}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 22 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="glass rounded-[8px] p-4"
          >
            <div className="grid gap-4 xl:grid-cols-[1fr_1fr_0.82fr]">
              <DeskPanel title="1. Policy reserve" icon={<ShieldCheck size={17} />}>
                <Field label="Holder" value={policyForm.holder} onChange={(holder) => setPolicyForm({ ...policyForm, holder })} />
                <Field label="Policy type" value={policyForm.policyType} onChange={(policyType) => setPolicyForm({ ...policyForm, policyType })} />
                <Field label="Covered event" value={policyForm.coveredEvent} onChange={(coveredEvent) => setPolicyForm({ ...policyForm, coveredEvent })} area />
                <Field label="Official source URL" value={policyForm.source} onChange={(source) => setPolicyForm({ ...policyForm, source })} />
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Premium" value={policyForm.premium} onChange={(premium) => setPolicyForm({ ...policyForm, premium })} />
                  <Field label="Payout" value={policyForm.payout} onChange={(payout) => setPolicyForm({ ...policyForm, payout })} />
                </div>
                <ActionButton busy={busy === "policy"} onClick={createPolicy} icon={<BadgeCheck size={17} />}>
                  Create policy
                </ActionButton>
              </DeskPanel>

              <DeskPanel title="2. Claim evidence" icon={<ClipboardCheck size={17} />}>
                <Field label="Claimant" value={claimForm.claimant} onChange={(claimant) => setClaimForm({ ...claimForm, claimant })} />
                <Field label="Incident" value={claimForm.incident} onChange={(incident) => setClaimForm({ ...claimForm, incident })} area />
                <Field label="Evidence URL" value={claimForm.evidenceUrl} onChange={(evidenceUrl) => setClaimForm({ ...claimForm, evidenceUrl })} />
                <Field label="Claim amount" value={claimForm.amount} onChange={(amount) => setClaimForm({ ...claimForm, amount })} />
                <ActionButton busy={busy === "claim"} onClick={submitClaim} icon={<ClipboardCheck size={17} />}>
                  Submit claim
                </ActionButton>
              </DeskPanel>

              <DeskPanel title="3. Verdict & payout" icon={<FileSearch size={17} />}>
                <div className="grid grid-cols-2 gap-3">
                  <Metric icon={<Gauge size={16} />} label="Confidence" value={claim.confidence} />
                  <Metric icon={<Activity size={16} />} label="Fraud risk" value={claim.risk} />
                </div>
                <div className="rounded-[8px] border border-white/10 bg-black/25 p-3">
                  <div className="text-xs text-[var(--muted)]">AI reason</div>
                  <p className="mt-2 min-h-24 text-sm leading-6 text-white/80">{claim.reason}</p>
                </div>
                <ActionButton busy={busy === "evaluate"} onClick={evaluateClaim} icon={<FileSearch size={17} />}>
                  Evaluate evidence
                </ActionButton>
                <ActionButton busy={busy === "payout"} onClick={executePayout} icon={<Banknote size={17} />} secondary>
                  Execute payout
                </ActionButton>

                <div className="grid gap-2 pt-1">
                  {logs.map((entry) => (
                    <div key={`${entry.label}-${entry.value}`} className={`rounded-[8px] border px-3 py-2 text-xs ${logStyle(entry.tone)}`}>
                      <span className="font-semibold">{entry.label}:</span>{" "}
                      <span className="text-white/65">{entry.value}</span>
                    </div>
                  ))}
                </div>
              </DeskPanel>
            </div>
          </motion.div>
        </section>

        <footer className="grid gap-3 pb-1 md:grid-cols-3">
          <MiniProof title="Official web evidence" value="Carrier/event/logistics URLs are read inside the contract." />
          <MiniProof title="Guarded payout" value="Treasury ledger writes only after APPROVED status." />
          <MiniProof title="Appeal path" value="Unclear or rejected claims can trigger a second review." />
        </footer>
      </div>
    </main>
  );
}

function DeskPanel({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-[8px] border border-white/10 bg-black/20 p-4">
      <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
        <span className="text-[var(--lime)]">{icon}</span>
        {title}
      </div>
      <div className="grid gap-3">{children}</div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  area = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  area?: boolean;
}) {
  const className =
    "w-full rounded-[8px] border border-white/10 bg-white/[0.055] px-3 py-2 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-[var(--lime)]";
  return (
    <label className="grid gap-1.5">
      <span className="text-xs text-[var(--muted)]">{label}</span>
      {area ? (
        <textarea className={`${className} min-h-20 resize-none`} value={value} onChange={(event) => onChange(event.target.value)} />
      ) : (
        <input className={className} value={value} onChange={(event) => onChange(event.target.value)} />
      )}
    </label>
  );
}

function ActionButton({
  children,
  icon,
  busy,
  secondary = false,
  onClick,
}: {
  children: React.ReactNode;
  icon: React.ReactNode;
  busy: boolean;
  secondary?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={busy}
      className={`flex h-11 items-center justify-center gap-2 rounded-[8px] px-4 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
        secondary
          ? "border border-white/10 bg-white/[0.06] text-white hover:border-[var(--lime)]"
          : "bg-[var(--lime)] text-black hover:bg-[var(--mint)]"
      }`}
    >
      {busy ? <Loader2 className="animate-spin" size={17} /> : icon}
      {children}
    </button>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-[8px] border border-white/10 bg-white/[0.04] p-3">
      <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
        <span className="text-[var(--lime)]">{icon}</span>
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}

function MiniProof({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-[8px] border border-white/10 bg-white/[0.045] p-4">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <CheckCircle2 size={15} className="text-[var(--lime)]" />
        {title}
      </div>
      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{value}</p>
    </div>
  );
}

function logStyle(tone: LogEntry["tone"]) {
  if (tone === "ok") return "border-[rgba(116,255,208,0.26)] bg-[rgba(116,255,208,0.08)] text-[var(--mint)]";
  if (tone === "warn") return "border-[rgba(255,212,121,0.26)] bg-[rgba(255,212,121,0.08)] text-[#ffd479]";
  if (tone === "bad") return "border-[rgba(255,122,89,0.3)] bg-[rgba(255,122,89,0.08)] text-[var(--coral)]";
  return "border-white/10 bg-white/[0.04] text-[var(--muted)]";
}
