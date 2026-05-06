# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: PropertyPilot

AI automation platform for Australian real estate agencies. Done-for-you automation systems that layer on top of agencies' existing CRMs — no CRM migration required.

**Status:** Pre-revenue. Brisbane-only for first 90 days. Target: boutique independent agencies (3–8 agents), principal is the decision-maker.

---

## Product Architecture

**52 automations across 8 categories:**
- Lead Capture (7), Lead Nurturing (8), Vendor & Seller (8), Property Management (10), Settlements (5), Reviews & Referrals (5), Marketing (5), Internal Operations (4)

**Two core packages:**
- **AI Lead Capture** — missed call text-back, after-hours responder, portal speed-to-lead (REA/Domain), WhatsApp/WeChat/Telegram, new lead assignment. Core promise: every portal lead responded to inside 5 minutes, 24/7.
- **AI Lead Nurture** — follow-up sequences, dormant lead reactivation, appraisal follow-up, OFI check-in/follow-up, buyer match alerts, 12-month long-term nurture.

**Nick's AI Lead Qualifier** — standalone AI qualifier that filters inbound leads before they reach an agent. A built component of the Lead Capture package, not a separate product.

---

## Business Rules (Enforce in All Code/Copy/UI)

- **No published prices** — ever. Named packages exist internally; no price lists anywhere client-facing.
- **Single CTA everywhere:** "Book Your Free Lead Health Check →"
- **No fabricated statistics** — only use verified sources (Rex Software, AgentZap, Realty-AI, Stepps, MRI Software, ListingHub, TransUnion/Forrester)
- **No expansion** outside Brisbane until 2+ agencies are proven live
- **No paid ads** before Phase 2 (Day 31+)

---

## The Grand Slam Guarantee

> "PropertyPilot responds to every portal lead inside 5 minutes for 90 days. Miss one — you don't pay at all."

Applies to the AI Lead Capture package only. Do not extend to the full 52-automation suite.

---

## Technical Constraints

- **First CRM:** AgentBox (Reapit Sales) — all automations built and stress-tested here first
- **CRM expansion order:** AgentBox → Rex → Vault RE → MRI Box+Dice → LockedOn
- No builds outside AgentBox until first agency is live
- AgentBox API access must be confirmed before committing to installs

---

## Financial Model

- Setup fee: 30% on signing / 70% at go-live
- Monthly retainer: $497–$1,397/month per agency
- Nick's per-install fee: **TBD — must be locked in writing before first paid client**

---

## Open Blockers (Pre-First-Sale Requirements)

1. Nick's fee — written agreement, per-install price, turnaround SLA, scope
2. AgentBox API access — developer access confirmed
3. Stripe / payment processing — set up before closing first client
4. Legal agreement template — scope, guarantee terms, cancellation clauses
5. Founding agency spot count — confirm before publishing site (currently: 3 spots / 2 remaining)

---

## Key Statistics (Verified Sources Only)

| Stat | Source |
|------|--------|
| 48% of real estate enquiries go unanswered | Rex Software |
| Average response time: ~4 business hours | Rex Software |
| Agents responding within 5 min are 21x more likely to qualify a lead vs 30 min | AgentZap |
| Average agent response time to new lead: 917 minutes | Realty-AI |
| 78% of buyers commit to the first agent who responds | Realty-AI |
| Appraisal requests responded to within 24h: 80% conversion; next day: 20% | Stepps |
| 29% of property managers intend to leave the profession | MRI Software / PMVA |
| 48% of agents use 4+ disconnected tools | TransUnion/Forrester 2025 |
| 65% of seller leads are referrals or repeat clients | ListingHub |
| 46% of sellers go back to the same agent who helped them buy | ListingHub |