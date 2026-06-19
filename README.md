# ClaimGuardAI

AI-native micro-insurance claims on GenLayer.

One-line pitch: ClaimGuardAI dies without GenLayer because the product's core action is an on-chain subjective payout judgment based on live web evidence.

## Why GenLayer

ClaimGuardAI handles low-value insurance claims where manual review costs more than the payout. A normal smart contract cannot read airline, event, logistics, booking, or public status pages and decide whether the evidence satisfies a policy. ClaimGuardAI puts that judgment inside a GenLayer Intelligent Contract.

The contract:

- Creates micro-insurance policies with a reserved payout amount.
- Accepts claim submissions with public evidence URLs.
- Reads official sources and claim evidence through `gl.nondet.web.get`.
- Runs `gl.nondet.exec_prompt` inside a local function wrapped by `gl.eq_principle.strict_eq`.
- Stores a deterministic verdict and guarded status transition.
- Releases payout only after the claim is `APPROVED`.
- Supports challenged claims through a second semantic appeal review.

## Project Structure

```text
ClaimGuardAI/
  contracts/ClaimGuardAI.py
  frontend/
  scripts/deploy/deploy.ps1
  tests/test_contract_static.py
```

## Builder Program Score Path

| Axis | Target | Evidence |
|---|---:|---|
| GenLayer fit | 5 | The claim verdict depends on on-chain web evidence plus LLM reasoning; without it the product becomes a normal claims form. |
| Contract quality | 4-5 | Explicit state machine, budget safety, deterministic JSON storage, guarded payout, appeal path, and strict validation. |
| Engineering | 4 | Separate contract, frontend, tests, deploy script, and documented setup. |
| Frontend / UX | 4 | Next.js app calls the deployed contract through `genlayer-js` and covers policy -> claim -> verdict -> payout. |

## Contract Flow

1. `create_policy(holder, policy_type, covered_event, evidence_source, premium_amount, payout_amount)`
2. `submit_claim(policy_id, claimant, incident_summary, evidence_url, claimed_amount)`
3. `add_evidence(claim_id, evidence_url)` when more proof is needed
4. `evaluate_claim(claim_id)` reads web evidence and stores `APPROVED`, `REJECTED`, or `NEED_MORE_EVIDENCE`
5. `execute_payout(claim_id)` writes a treasury ledger entry only for approved claims
6. `challenge_claim(claim_id, reason)` and `resolve_challenge(claim_id)` provide an appeal path

## Pre-Deploy Verification

From `D:\Genlayer\ClaimGuardAI`:

```powershell
python -m unittest discover -s tests
python -c "import ast; ast.parse(open('contracts/ClaimGuardAI.py', encoding='utf-8').read())"
genlayer lint contracts/ClaimGuardAI.py
```

## Deploy

```powershell
genlayer deploy contracts/ClaimGuardAI.py --name ClaimGuardAI
```

After deployment, copy the address into `frontend/.env.local`:

```text
NEXT_PUBLIC_CONTRACT_ADDRESS=0xeF87cECaeB3375785AD9A5FfA99a77B607283bD6
NEXT_PUBLIC_NETWORK=testnetAsimov
NEXT_PUBLIC_GENLAYER_RPC=
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL, connect a GenLayer-compatible wallet, then run the full flow from the first screen.

The app includes a visible demo fallback when `NEXT_PUBLIC_CONTRACT_ADDRESS` is empty, but the submission path is the real `genlayer-js` path. Set the contract address before recording the final demo video.

## Demo Video Script

1. Show the deployed contract address in `.env.local`.
2. Connect wallet.
3. Create a flight micro-insurance policy.
4. Submit a claim with an official status/evidence URL.
5. Run `evaluate_claim` and wait for finality.
6. Show the AI verdict reason, confidence, and risk score.
7. Execute payout and show the treasury ledger/status change.

## Live App

Add the deployed frontend URL here before submission:

```text
https://your-claimguard-ai-app.vercel.app
```
