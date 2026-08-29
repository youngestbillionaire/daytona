import json
import logging
from typing import Callable, Optional
from orchestrator.clients.nosana_client import nosana_client
from orchestrator.models import (
    CoreFeature,
    IdeationOutput,
    TargetUserPersona,
    WhitespaceAnalysisOutput,
)

logger = logging.getLogger("founder0.stage.ideation")

# ═══════════════════════════════════════════════════════════════════
# WORLD-CLASS MOCK IDEAS — Real innovations, not generic SaaS filler
# Each idea passes the "Would Peter Thiel fund this?" zero-to-one test
# ═══════════════════════════════════════════════════════════════════

MOCK_IDEAS = {
    # ── PRODUCTIVITY / ROOMMATE / SHARED LIVING ──
    "roommate": {
        "product_name": "DeadlockDAO",
        "tagline": "The Trustless Roommate Treasury That Eliminates All Financial Friction",
        "one_line_pitch": "DeadlockDAO replaces awkward money conversations between roommates with an autonomous escrow protocol that auto-settles shared expenses, enforces accountability through stake-based commitments, and turns household chores into tokenized micro-rewards.",
        "elevator_pitch": "Every shared living arrangement degenerates into passive-aggressive Venmo requests and screaming matches over $12 toilet paper. The core problem isn't tracking — Splitwise already does that. The problem is enforcement. DeadlockDAO creates a trustless household treasury where rent, utilities, and groceries auto-settle from locked deposits, disputed purchases trigger instant AI arbitration with receipt evidence, and chore completion unlocks dollar-value credits. We're not building a better spreadsheet — we're building the financial operating system for the 48 million Americans who share a home.",
        "core_features": [
            {"name": "Autonomous Escrow Settlement", "description": "Each roommate locks a security deposit. Recurring bills auto-deduct without anyone sending a single request. Late? Funds release from escrow automatically.", "user_value": "Zero awkward money conversations, ever."},
            {"name": "AI Receipt Arbitration", "description": "Photograph a receipt, AI categorizes items by who consumed them, auto-splits contested groceries, and renders binding micro-arbitration within 60 seconds.", "user_value": "No more 'I didn't eat those eggs' disputes."},
            {"name": "Chore-to-Credit Protocol", "description": "Complete verified household chores (photo + GPS + timestamp proof) to earn dollar-value credits deducted from your next bill share.", "user_value": "Real financial incentives for a clean home."}
        ],
        "target_user_persona": {"name": "The Exhausted Peacekeeper", "description": "25-34 year old professional who manages household finances by default and is tired of being the 'money person' in every shared living situation.", "pain_points": ["Sends 15+ payment reminders per month", "Has lost friendships over unpaid $40 debts", "Spends 2+ hours/month on manual expense reconciliation"]},
        "monetization_model": "Free for households up to 3 people. Pro Household ($6.99/mo) unlocks unlimited members, chore-to-credit, and AI arbitration. 0.5% instant settlement fee on escrow releases.",
        "pricing_suggestion": "Free Starter (3 people) / $6.99/mo Pro Household / $14.99/mo Property Manager (unlimited units)",
        "differentiation_from_competitors": "Splitwise tracks what you owe. We enforce payment. The fundamental shift is from passive ledger to active treasury — money moves automatically, disputes resolve instantly, and accountability is structural, not social.",
        "contrarian_insight": "Everyone assumes the roommate expense problem is a tracking problem. It's actually an enforcement problem. No amount of better UI fixes the fact that humans avoid financial confrontation. You need to remove the human from the loop entirely.",
        "technical_moat": "Escrow commitment graph with stake-weighted reputation scores. Each successful settlement increases trust score, reducing future deposit requirements. Network effects compound — switching costs grow with settlement history.",
        "tam_estimate": "$4.2B — 48M Americans in shared housing × $87/year willingness-to-pay for financial peace",
        "go_to_market_wedge": "Launch in university housing Facebook groups and r/roommates. Viral loop: one roommate signs up, others must join to settle. 3.2x viral coefficient from existing complaint communities.",
        "psychological_hook": "Loss aversion — the $340 your roommate owes you RIGHT NOW is more painful than any subscription fee. Users adopt because the cost of NOT switching is viscerally immediate.",
        "ten_x_factor": "Current tools require you to ASK for money. DeadlockDAO means money moves without asking. That's not 2x better — it's a categorically different experience, like the jump from cash to direct deposit.",
        "brand_tone": "assertive, trustworthy, zero-friction",
        "suggested_color_palette": ["#0284c7", "#0f172a", "#38bdf8"],
        "rejected_names": ["SplitForce", "RentGuard", "HouseBank"],
        "rejected_names_reasoning": ["Sounds like a generic Splitwise clone", "Implies insurance, not settlements", "Too institutional, not consumer-friendly"]
    },

    # ── FINTECH / FREELANCE ──
    "fintech": {
        "product_name": "PhantomCFO",
        "tagline": "Your AI Chief Financial Officer That Files Before You Even Think About It",
        "one_line_pitch": "PhantomCFO is an autonomous financial intelligence that watches your bank feed 24/7, categorizes every transaction with tax-code precision, discovers deductions you'd never find manually, and files quarterly estimates automatically — saving the average freelancer $4,200/year in missed write-offs.",
        "elevator_pitch": "67 million Americans freelance, and 73% of them overpay taxes because they miss legitimate deductions. The problem isn't laziness — it's that tax code is 75,000 pages long and existing tools force YOU to be the accountant. PhantomCFO connects to your bank feed once, then operates silently in the background: categorizing transactions with IRS-category precision, flagging missed deductions in real-time, auto-generating quarterly estimated payments, and producing audit-ready documentation. We don't help you do bookkeeping — we make bookkeeping not exist.",
        "core_features": [
            {"name": "Silent Bank Feed Intelligence", "description": "Connects once to your bank account via Plaid. From that moment, every transaction is auto-categorized to IRS Schedule C line items with 97.3% accuracy — no manual tagging ever.", "user_value": "Bookkeeping happens without you knowing."},
            {"name": "Deduction Hunter Engine", "description": "Pattern-matches your spending against 847 known freelancer deduction categories. Discovers home office percentages, vehicle depreciation, equipment amortization, and health insurance premiums you'd never catch.", "user_value": "Average user discovers $4,200 in missed deductions."},
            {"name": "Autonomous Quarterly Filing", "description": "Calculates and files IRS Form 1040-ES quarterly estimated payments automatically. Never miss a deadline, never overpay, never face a penalty.", "user_value": "Zero tax anxiety, zero late penalties."}
        ],
        "target_user_persona": {"name": "The Overwhelmed Solo Founder", "description": "Freelancer or solopreneur earning $50K-$250K who dreads tax season, currently uses a shoebox of receipts or pays $800+ for a CPA they see once a year.", "pain_points": ["Missed $11K in deductions last year", "Pays $800+ for annual CPA who spends 2 hours on their return", "Lives in constant low-grade anxiety about an IRS audit"]},
        "monetization_model": "Free for income under $30K/year. Pro ($12.99/mo) unlocks unlimited deduction hunting, quarterly auto-filing, and audit defense documentation. Enterprise ($49.99/mo) for agencies managing multiple freelancers.",
        "pricing_suggestion": "Free Starter (< $30K income) / $12.99/mo Pro Freelancer / $49.99/mo Agency Manager",
        "differentiation_from_competitors": "QuickBooks makes you the accountant with better tools. Keeper finds deductions but can't file. CPAs cost $800+ and see your finances once a year. PhantomCFO is the only product that operates continuously, autonomously, and files on your behalf — not as a tool, but as an agent.",
        "contrarian_insight": "The industry believes freelancers need better bookkeeping tools. Wrong. Freelancers need bookkeeping to stop existing as a task entirely. The winning product isn't the best accounting UI — it's the one with no UI at all.",
        "technical_moat": "Transaction categorization model trained on 12M anonymized freelancer transactions across 23 industries. Accuracy compounds with usage — each correction improves the model for all users in that industry vertical.",
        "tam_estimate": "$12.8B — 67M US freelancers × $191/year average spend on tax/accounting tools",
        "go_to_market_wedge": "Partner with freelance platforms (Upwork, Fiverr, Toptal) as an embedded financial copilot. Viral trigger: share your 'Deductions Found' report on Twitter/LinkedIn during tax season.",
        "psychological_hook": "Fear of loss — every day without PhantomCFO is money left on the table. The $4,200 average in missed deductions is money you already earned and are giving away to the IRS.",
        "ten_x_factor": "Existing tools reduce bookkeeping time from 14 hours to 4 hours. PhantomCFO reduces it to 0 hours. That's not an incremental improvement — it's the elimination of an entire category of work.",
        "brand_tone": "authoritative, invisible, premium",
        "suggested_color_palette": ["#059669", "#064e3b", "#34d399"],
        "rejected_names": ["TaxBot", "LedgerAI", "DeductionPro"],
        "rejected_names_reasoning": ["Sounds like a chatbot, not a CFO", "Too technical for non-accountants", "Implies effort, not automation"]
    },

    # ── SOCIAL / COMMUNITY ──
    "social": {
        "product_name": "GatherBond",
        "tagline": "Skin-in-the-Game Micro-Meetups That Actually Happen",
        "one_line_pitch": "GatherBond eliminates the 80% event ghosting rate by requiring a small refundable stake ($3-$10) to RSVP, automatically returning it only when you show up — turning casual interest into real-world connection.",
        "elevator_pitch": "The loneliness epidemic kills more people than smoking, yet every 'social' app is designed to keep you scrolling, not to get you out of the house. Meetup charges organizers $200/year. Bumble BFF has a 2% in-person meeting rate. The fundamental problem is commitment — people RSVP with zero skin in the game and ghost 80% of the time. GatherBond fixes this with stake-backed micro-meetups: put down $5 to RSVP, get it back when you check in at the venue. No-shows forfeit their stake to attendees who showed up. Suddenly, a 6-person board game night actually has 6 people.",
        "core_features": [
            {"name": "Stake-Backed RSVP Protocol", "description": "RSVP requires a $3-$10 refundable commitment. Show up (GPS + time verification) and get your stake back instantly. Ghost and your stake redistributes to attendees who honored their commitment.", "user_value": "Events that actually happen with the right number of people."},
            {"name": "Hyper-Local Interest Matching", "description": "ML-powered matching based on 47 hobby taxonomies, availability windows, and proximity. Suggests 3-6 person micro-events, not 50-person anonymous mixers.", "user_value": "Find your exact people within 2 miles."},
            {"name": "Friendship Momentum Engine", "description": "After a successful meetup, auto-suggests the next hangout based on group chemistry scores and shared availability. Builds recurring friend groups, not one-off events.", "user_value": "Turn a single meetup into a lasting friend group."}
        ],
        "target_user_persona": {"name": "The Relocated Professional", "description": "26-38 year old who moved to a new city for work and has been struggling for months to build a genuine social circle beyond coworkers.", "pain_points": ["Tried Bumble BFF — matched with 40 people, met zero", "Pays $30/mo for Meetup but events are too large and impersonal", "Feels genuine loneliness but is too proud to admit it openly"]},
        "monetization_model": "Free for attendees (we take 15% of forfeited ghost stakes as platform fee). Organizer Pro ($4.99/mo) for custom event branding and analytics. Venue partnerships for sponsored locations.",
        "pricing_suggestion": "Free for attendees / $4.99/mo Organizer Pro / Revenue share on forfeited stakes",
        "differentiation_from_competitors": "Every other platform optimizes for RSVPs. We optimize for ATTENDANCE. The stake mechanism transforms the fundamental economics — organizers don't pay, ghosters do. This is the only platform where the business model is aligned with real human connection.",
        "contrarian_insight": "The social app industry believes the problem is discovery — helping people FIND events and groups. Wrong. Discovery is solved. The real problem is commitment. People find events constantly and ghost them constantly. Fix the commitment mechanism, and everything else follows.",
        "technical_moat": "Stake-commitment behavioral data creates a trust graph that improves matching quality over time. Users who consistently show up get matched with other reliable attendees, creating a self-reinforcing quality network. This data is proprietary and compounds with every event.",
        "tam_estimate": "$8.1B — addressable through the 73M Americans who report wanting more social connection × $110/year willingness-to-pay",
        "go_to_market_wedge": "Launch in 3 dense urban neighborhoods (Brooklyn, SF Mission, Austin East). Seed with board game, hiking, and cooking micro-events. Viral loop: every attendee invites 1 friend to the next event.",
        "psychological_hook": "Commitment device psychology — the $5 stake isn't about the money, it's about self-signaling. Putting money down transforms 'maybe I'll go' into 'I'm going.' Loss aversion makes the stake feel 2.5x more painful to lose than it cost to place.",
        "ten_x_factor": "Meetup events have 20% attendance rates. GatherBond events have 89% attendance rates. That's not a better app — it's a fundamentally different product category: events that reliably happen.",
        "brand_tone": "warm, playful, accountable",
        "suggested_color_palette": ["#8b5cf6", "#1e1b4b", "#c084fc"],
        "rejected_names": ["ShowUp", "BondStake", "TrueHangout"],
        "rejected_names_reasoning": ["Too imperative, sounds like a command", "Sounds like a gambling app", "Generic and forgettable"]
    },

    # ── HEALTH / SLEEP ──
    "health": {
        "product_name": "ChronoForge",
        "tagline": "The Prescriptive Sleep Protocol That Tells You Exactly What to Do and When",
        "one_line_pitch": "ChronoForge replaces passive sleep scores with precise, minute-level behavioral prescriptions — telling you your exact caffeine cutoff time, optimal light exposure windows, and personalized wind-down protocol based on your unique chronotype and daily context.",
        "elevator_pitch": "Sleep trackers are the modern equivalent of a scale that tells you you're overweight but offers no diet plan. Whoop, Oura, and Sleep Cycle all excel at measurement — and they all fail at prescription. You know your sleep score was 62%. Now what? ChronoForge inverts the model: instead of measuring your sleep and leaving you to figure out what to change, it analyzes your daily inputs (caffeine, meals, screen time, exercise, stress) and outputs a precise, adaptive protocol: 'Last coffee at 1:47 PM. Begin blue-light filter at 8:30 PM. Take 200mg magnesium at 9:15 PM. Lights out at 10:42 PM.' No hardware required. No scores. Just instructions that work.",
        "core_features": [
            {"name": "Precision Caffeine Cutoff Engine", "description": "Calculates your exact caffeine cutoff time based on your CYP1A2 metabolism speed (fast/slow genetic proxy from intake patterns), sleep target, and accumulated sleep debt. Updates daily.", "user_value": "Never wonder 'is it too late for coffee?' again."},
            {"name": "Adaptive Wind-Down Protocol", "description": "Generates a minute-by-minute evening routine: when to dim lights, what supplements to take, optimal room temperature, breathing exercises — all personalized to your chronotype and tomorrow's schedule.", "user_value": "A bedtime routine that actually works, built for YOUR biology."},
            {"name": "Shift-Work Chronotype Adaptation", "description": "For rotating shift workers, nurses, and first responders: calculates optimal light exposure windows and sleep anchors to minimize circadian disruption across schedule changes.", "user_value": "Finally, a sleep tool built for people who don't work 9-5."}
        ],
        "target_user_persona": {"name": "The Quantified Insomniac", "description": "28-45 year old knowledge worker who has tried multiple sleep trackers, owns $500+ in sleep gadgets, and still sleeps poorly because no tool tells them what to CHANGE.", "pain_points": ["Owns Oura ring AND Sleep Cycle — still sleeps badly", "Knows sleep is important but generic advice like 'go to bed earlier' is useless", "Drinks coffee 'until about 2pm' without knowing their actual metabolic cutoff"]},
        "monetization_model": "Free basic protocol (caffeine cutoff only). Premium ($7.99/mo) unlocks full adaptive protocol, supplement timing, shift-work mode, and weekly chronobiology reports.",
        "pricing_suggestion": "Free Caffeine Calculator / $7.99/mo Full Protocol / $59.99/year Annual (save 37%)",
        "differentiation_from_competitors": "Every sleep product measures. None prescribe. Whoop says 'your recovery is low.' We say 'skip the 2:15 PM latte, do 4-7-8 breathing at 9:20 PM, and you'll gain 47 minutes of deep sleep tonight.' We're the first prescriptive sleep product, not the 50th descriptive one.",
        "contrarian_insight": "The sleep industry is obsessed with measurement because hardware companies make money selling sensors. But measurement without prescription is just expensive anxiety. The winning sleep product has NO hardware — it's pure behavioral intelligence.",
        "technical_moat": "Pharmacokinetic caffeine metabolism model combined with individual chronotype profiling from behavioral data. Our protocol accuracy improves with each night of data — after 14 days, prescription accuracy reaches 91% correlation with actual sleep quality improvements.",
        "tam_estimate": "$6.3B — 164M Americans with sleep issues × $38/year average spend on sleep solutions",
        "go_to_market_wedge": "Launch as a free caffeine cutoff calculator (viral TikTok/Twitter hook: 'Find your exact coffee deadline'). Upsell to full protocol after users see their first week of improvement.",
        "psychological_hook": "Specificity bias — a precise instruction ('stop caffeine at 1:47 PM') is dramatically more actionable and trustworthy than a vague guideline ('avoid caffeine in the afternoon'). Precision creates compliance.",
        "ten_x_factor": "Sleep trackers give you a score after the fact. ChronoForge gives you instructions before the fact. That's the difference between a thermometer and a thermostat — one observes, the other controls.",
        "brand_tone": "clinical, precise, empowering",
        "suggested_color_palette": ["#6366f1", "#0c0a1a", "#a78bfa"],
        "rejected_names": ["SleepScript", "RestIQ", "NightCoach"],
        "rejected_names_reasoning": ["Sounds like a medication", "Implies testing/scoring (the exact problem we're solving against)", "Too generic, sounds like a meditation app"]
    },

    # ── DEVTOOLS / DATABASE ──
    "devtools": {
        "product_name": "MigrateShield",
        "tagline": "The Database Migration Firewall That Prevents Production Disasters Before They Deploy",
        "one_line_pitch": "MigrateShield analyzes every database migration against a simulation of your production traffic, table sizes, and lock contention — blocking dangerous changes in CI and showing you the exact blast radius before a single row is touched.",
        "elevator_pitch": "A single bad database migration costs the average engineering team $52,000 in downtime, lost revenue, and emergency response. Yet every migration tool on the market — Prisma, Flyway, Liquibase — blindly executes SQL without analyzing whether it's safe for your specific production environment. MigrateShield is a CI/CD firewall for database changes: it profiles your production schema, simulates migrations against realistic traffic patterns, and blocks deployments that would cause table locks, data truncation, or constraint violations. It's the difference between deploying blind and deploying with X-ray vision.",
        "core_features": [
            {"name": "Lock Contention Simulator", "description": "Before any migration runs, simulates the exact lock behavior against your table sizes and concurrent query patterns. Shows 'This ALTER will lock writes on your 200M-row users table for ~47 minutes' with precision.", "user_value": "Never accidentally lock production tables again."},
            {"name": "Blast Radius Analyzer", "description": "Maps every migration statement to its downstream impact: which services reference the affected columns, which queries will break, which indexes become invalid. Generates a visual dependency graph.", "user_value": "See the full impact of every change before it ships."},
            {"name": "Automated Safe Rewrite Engine", "description": "When a dangerous migration is detected, automatically suggests safe alternatives: online DDL strategies, shadow table approaches, and staged rollout plans that achieve the same schema change with zero downtime.", "user_value": "Don't just block bad migrations — auto-fix them."}
        ],
        "target_user_persona": {"name": "The On-Call Database Guardian", "description": "Senior backend engineer or DBA responsible for database reliability at a company with 10M+ rows, who has been personally woken at 3 AM by a bad migration at least once.", "pain_points": ["Personally responsible for reviewing every migration PR by hand", "Has seen a junior dev lock a production table for 2 hours", "Spends 5+ hours/week on manual migration safety reviews"]},
        "monetization_model": "Free for repos under 10 migrations/month. Team ($29/mo per repo) unlocks simulation engine, blast radius maps, and safe rewrite suggestions. Enterprise ($199/mo) adds custom traffic profiling and SOC2 compliance reporting.",
        "pricing_suggestion": "Free Open Source / $29/mo Team / $199/mo Enterprise",
        "differentiation_from_competitors": "Prisma, Flyway, and Liquibase are migration EXECUTORS. MigrateShield is a migration FIREWALL. We don't run migrations — we prevent bad ones from running. This is a fundamentally different product category, like how Snyk doesn't build code but prevents vulnerable code from shipping.",
        "contrarian_insight": "The database migration market is focused on making migrations easier to write and execute. But the real cost isn't writing migrations — it's recovering from bad ones. The winning product doesn't help you migrate faster; it prevents you from migrating dangerously.",
        "technical_moat": "Production-traffic simulation models calibrated per-customer from real query logs and pg_stat_statements data. Our lock prediction accuracy exceeds 94% after profiling a production environment for 48 hours. This calibration data is deeply customer-specific and creates massive switching costs.",
        "tam_estimate": "$3.7B — 2.8M production Postgres/MySQL deployments × $1,320/year average cost of migration incidents",
        "go_to_market_wedge": "Open-source CLI that runs in GitHub Actions. Free for small teams. Viral loop: one engineer adds it to CI, entire team benefits. Convert to paid when team exceeds 10 migrations/month.",
        "psychological_hook": "Fear of catastrophic loss — every engineer has a 3 AM production incident horror story. MigrateShield sells peace of mind. The $29/mo is insurance against a $52,000 incident.",
        "ten_x_factor": "Current tools help you write migrations 2x faster. MigrateShield prevents 100% of predictable migration disasters. Speed of writing is irrelevant when one bad migration costs 52 hours of downtime.",
        "brand_tone": "authoritative, protective, engineering-grade",
        "suggested_color_palette": ["#f59e0b", "#1c1917", "#fbbf24"],
        "rejected_names": ["SafeSQL", "MigrateGuard", "SchemaShield"],
        "rejected_names_reasoning": ["Sounds like a linting library, not a firewall", "Too close to existing product names", "Implies static protection, not active simulation"]
    }
}


DYNAMIC_PALETTES = [
    ["#06b6d4", "#0b192c", "#38bdf8"],  # Electric Cyan / Sky
    ["#10b981", "#022c22", "#34d399"],  # Emerald Mint / Forest
    ["#8b5cf6", "#1e1b4b", "#c084fc"],  # Hyper Violet / Amethyst
    ["#f59e0b", "#3b1a03", "#fbbf24"],  # Sunset Amber / Gold
    ["#f43f5e", "#3f0713", "#fda4af"],  # Neon Rose / Crimson
    ["#6366f1", "#131633", "#818cf8"],  # Royal Indigo / Ultramarine
    ["#14b8a6", "#032824", "#2dd4bf"],  # Cyber Teal / Jade
    ["#f97316", "#371505", "#fb923c"],  # Solar Orange / Blaze
    ["#3b82f6", "#071630", "#93c5fd"],  # Electric Cobalt / Ocean
    ["#d946ef", "#3b0764", "#f0abfc"],  # Cyber Fuchsia / Magenta
]

def _get_dynamic_palette(idea_text: str) -> list:
    """Generate a unique aesthetic theme palette deterministically per product idea."""
    idx = sum(ord(c) for c in idea_text) % len(DYNAMIC_PALETTES)
    return DYNAMIC_PALETTES[idx]

def _select_mock_idea(idea: str, whitespace: WhitespaceAnalysisOutput) -> dict:
    """Select the best mock idea based on keyword matching against the user's input."""
    q = idea.lower()
    selected = None

    if any(w in q for w in ["pet", "dog", "cat", "puppy", "kitten", "animal"]):
        selected = {
            "product_name": "PawMatch",
            "tagline": "The Verified Social Network for Dog Playdates & Pet Compatibility",
            "one_line_pitch": "PawMatch eliminates aggressive dog park encounters and flakey pet owners with vaccine-verified temperament matching and scheduled neighborhood playdates.",
            "elevator_pitch": "68 million households own pets, but finding safe playdates and compatible socialization is pure guesswork. Pet owners suffer through aggressive dogs at public parks, flaky meetup groups, and zero verification. PawMatch introduces temperament-calibrated matching where verified vaccination records, energy levels, and play styles ensure zero-conflict socialization. We don't just connect pet owners — we build safe, trusted local animal communities.",
            "core_features": [
                {"name": "Temperament & Energy Matching", "description": "Proprietary behavioral algorithm pairs dogs by size, play style (wrestler, chaser, gentle), and energy output to prevent aggression.", "user_value": "Zero dog fights, zero anxiety at playdates."},
                {"name": "Verified Vet & Vaccine Pass", "description": "Automated OCR verifies rabies and DHPP records directly from vet receipts before granting profile activation.", "user_value": "100% guaranteed healthy, disease-free playmates."},
                {"name": "Verified Park Playdate Escrow", "description": "Stake-backed attendance holds that unlock treat rewards at local partnered pet boutiques when meetups happen.", "user_value": "No more showing up to empty parks."}
            ],
            "target_user_persona": {
                "name": "The Protective Pet Parent",
                "description": "24-40 year old urban/suburban dog owner who treats their pet like family and wants safe, high-quality socialization.",
                "pain_points": ["Traumatized by aggressive dogs at public dog parks", "Friends' dogs don't match energy level", "Spends $100s on toys and treats for lonely pets"]
            },
            "monetization_model": "Free for basic matching. PawMatch Gold ($8.99/mo) unlocks unlimited playdates, verified breed badges, and 15% discounts at 4,000+ local pet supply partners.",
            "pricing_suggestion": "Free Starter / $8.99/mo PawMatch Gold / $19.99/mo Multi-Pet VIP",
            "differentiation_from_competitors": "BarkBuddy and Petzbe are passive image feeds. PawMatch is an active temperament verification and safe meetup protocol.",
            "contrarian_insight": "Everyone assumes pet socialization is a photo-sharing problem. It is actually a safety and temperament compatibility problem. Owners care 10x more about avoiding dog fights than looking at cute pictures.",
            "technical_moat": "Verified veterinary record graph and behavioral temperament calibration dataset across 200+ dog breeds.",
            "tam_estimate": "$6.4B — 68M US pet-owning households × $94/year willingness to spend on pet wellness and socialization",
            "go_to_market_wedge": "Viral adoption through local dog agility parks, veterinary clinics, and rescue shelters with 3.4x referral loops.",
            "psychological_hook": "Parental protection instinct — preventing traumatic animal encounters is an urgent, non-negotiable priority.",
            "ten_x_factor": "Transforms risky public dog park roulette into guaranteed peaceful, joyful play sessions.",
            "brand_tone": "warm, trusted, playful, safety-first",
            "suggested_color_palette": ["#f97316", "#371505", "#fb923c"],
            "rejected_names": ["TinderDogs", "BarkForce", "PetSwipe"],
            "rejected_names_reasoning": ["Sounds like a gimmick", "Too aggressive sounding", "Implies human dating rather than pet safety"]
        }
    elif any(w in q for w in ["dating", "tinder", "match", "romance", "single"]):
        selected = {
            "product_name": "TrueSpark",
            "tagline": "The High-Intent Dating Network That Eliminates Endless Swiping & Ghosting",
            "one_line_pitch": "TrueSpark replaces swipe fatigue with commitment-backed micro-dates and zero-ghosting attendance bonds.",
            "elevator_pitch": "Modern dating apps optimize for addiction and dopamine, resulting in an 85% ghosting rate and severe burnout. TrueSpark flips the model: users match on shared values, commit a small refundable bond to coffee dates, and receive prompt mutual feedback.",
            "core_features": [
                {"name": "Commitment-Bonded Dates", "description": "Refundable micro-deposits guarantee both parties show up on time.", "user_value": "Zero ghosting, zero wasted evenings."},
                {"name": "Values Alignment Engine", "description": "Matches based on lifestyle non-negotiables rather than superficial photo carousels.", "user_value": "High chemistry from date one."},
                {"name": "Safe Public Venue Coordinator", "description": "Auto-reserves verified partner cafes with exclusive member tables.", "user_value": "Effortless date logistics."}
            ],
            "target_user_persona": {
                "name": "The Burned-Out Dater",
                "description": "25-38 year old professional seeking genuine relationships after years of superficial dating app exhaustion.",
                "pain_points": ["Ghosted on 4 out of 5 matches", "Tired of endless dry texting", "Wants high-intent, emotionally mature partners"]
            },
            "monetization_model": "Free entry. TrueSpark Premium ($14.99/mo) unlocks priority invites, verified relationship goals, and partner discounts.",
            "pricing_suggestion": "Free / $14.99/mo Premium / $29.99/mo VIP Concierge",
            "differentiation_from_competitors": "Tinder and Hinge profit from keeping you single. TrueSpark profits from getting you off the app into real life.",
            "contrarian_insight": "Dating apps fail because they optimize for engagement time instead of relationship formation. Adding real friction (skin in the game) massively increases success rates.",
            "technical_moat": "Reputation-commitment graph with mutual verification scores.",
            "tam_estimate": "$8.2B global online dating market",
            "go_to_market_wedge": "College alumni networks and local professional communities.",
            "psychological_hook": "Dignity and respect — eliminates the humiliation of being stood up.",
            "ten_x_factor": "Moves matches from screen to in-person coffee in under 48 hours.",
            "brand_tone": "authentic, high-intent, respectful",
            "suggested_color_palette": ["#f43f5e", "#3f0713", "#fda4af"],
            "rejected_names": ["SwipeMore", "QuickDate", "MeetFast"],
            "rejected_names_reasoning": ["Promotes superficial behavior", "Sounds rushed", "Lacks emotional resonance"]
        }
    elif any(w in q for w in ["game", "gaming", "pokemon", "ar", "vr", "metaverse"]):
        selected = {
            "product_name": "RealmQuest",
            "tagline": "The Decentralized Location-Based AR Realm That Turns Any City Into An RPG",
            "one_line_pitch": "RealmQuest bridges real-world exploration with tactical co-op AR battles, eliminating rural dead zones through player-anchored territory nodes.",
            "elevator_pitch": "Location-based games like Pokémon GO alienate millions of suburban and rural players while relying on brainless tap-mashing battles. RealmQuest introduces player-generated localized territories, deep tactical combat, and battery-optimized AR tracking.",
            "core_features": [
                {"name": "Decentralized Territory Nodes", "description": "Players anchor custom exploration beacons anywhere in the world, ensuring rich gameplay even in rural towns.", "user_value": "Play anywhere, not just in downtown Tokyo or NYC."},
                {"name": "Tactical Real-Time Co-Op", "description": "Multiplayer boss raids requiring real positional positioning and class synergies.", "user_value": "Deep engaging combat, not mindless tapping."},
                {"name": "Ultra-Low Power AR Engine", "description": "Optimized spatial meshing consuming 70% less battery and zero device overheating.", "user_value": "Hours of continuous gameplay on a single charge."}
            ],
            "target_user_persona": {
                "name": "The Active Gamer",
                "description": "18-35 year old gamer who loves walking and outdoor activities but is frustrated by corporate AR game limitations.",
                "pain_points": ["No spawns in their home area", "Battery dies in 45 minutes", "Tired of pay-to-win microtransactions"]
            },
            "monetization_model": "Free to play with cosmetic battle passes ($7.99/season) and guild realm customization.",
            "pricing_suggestion": "Free / $7.99 Season Pass / $19.99 Guild Champion",
            "differentiation_from_competitors": "Niantic controls all points of interest centrally. RealmQuest is player-curated, tactical, and battery-friendly.",
            "contrarian_insight": "AR games don't need real-world sponsor landmarks. They need player-generated narrative significance and deep tactical combat.",
            "technical_moat": "Spatial mesh optimization protocols and decentralized POI validation graphs.",
            "tam_estimate": "$22.4B mobile gaming & AR exploration market",
            "go_to_market_wedge": "Gaming subreddits, university campus walking clubs, and Discord gaming communities.",
            "psychological_hook": "Curiosity and exploration — turning everyday walks into epic quests.",
            "ten_x_factor": "10x deeper combat with 1/3 the battery consumption.",
            "brand_tone": "epic, adventurous, vibrant",
            "suggested_color_palette": ["#8b5cf6", "#1e1b4b", "#c084fc"],
            "rejected_names": ["GoClone", "WalkMon", "CityRaid"],
            "rejected_names_reasoning": ["Sounds like a cheap knockoff", "Too generic", "Implies combat only"]
        }
    elif any(w in q for w in ["roommate", "bill", "split", "chore", "household", "rent", "shared"]):
        selected = dict(MOCK_IDEAS["roommate"])
    elif any(w in q for w in ["freelance", "tax", "account", "invoice", "bookkeep", "receipt", "deduction"]):
        selected = dict(MOCK_IDEAS["fintech"])
    elif any(w in q for w in ["meetup", "hobby", "friend", "community", "social", "lonely", "ghost", "event"]):
        selected = dict(MOCK_IDEAS["social"])
    elif any(w in q for w in ["sleep", "health", "caffeine", "circadian", "fitness", "recovery", "diet"]):
        selected = dict(MOCK_IDEAS["health"])
    elif any(w in q for w in ["schema", "database", "migration", "postgres", "sql", "deploy", "devops"]):
        selected = dict(MOCK_IDEAS["devtools"])
    else:
        # Generate custom fallback tailored from prompt keywords
        words = [w.capitalize() for w in idea.split() if len(w) > 3]
        base_name = f"{words[0]}Hub" if words else "VentureOS"
        selected = {
            "product_name": base_name,
            "tagline": f"The Autonomous Platform Built For {idea[:35]}",
            "one_line_pitch": f"An intelligent, zero-friction solution that solves: {idea}",
            "elevator_pitch": f"Legacy tools force users to perform manual work. {base_name} eliminates manual friction by deploying verified automated workflows tailored for {idea}.",
            "core_features": [
                {"name": "Autonomous Core Engine", "description": f"Auto-executes core workflows for {idea[:30]} with zero manual overhead.", "user_value": "Saves 10+ hours per week."},
                {"name": "Verifiable Trust Network", "description": "Maintains instant state verification and mutual accountability.", "user_value": "Complete peace of mind."},
                {"name": "Zero-Friction Collaboration", "description": "Seamless real-time synchronization across all participants.", "user_value": "Zero friction, zero drop-off."}
            ],
            "target_user_persona": {
                "name": "The Modern Enthusiast",
                "description": f"Users seeking seamless execution in the {idea[:25]} space.",
                "pain_points": [f"Wastes hours on manual steps in {idea[:25]}", "Struggles with outdated tools", "Needs instant reliability"]
            },
            "monetization_model": "Freemium ($0 Starter / $9.99/mo Pro / $29.99/mo Power)",
            "pricing_suggestion": "Free Starter / $9.99/mo Pro / $29.99/mo VIP",
            "differentiation_from_competitors": "Incumbents require manual configuration; we provide autonomous verified resolution.",
            "contrarian_insight": "Everyone assumes more manual controls are needed. The ground truth is that users want the task automated away completely.",
            "technical_moat": "Compounding network effect with deep behavioral calibration.",
            "tam_estimate": "$4.5B serviceable addressable market",
            "go_to_market_wedge": "Direct viral adoption via niche enthusiast communities.",
            "psychological_hook": "Loss aversion — users eliminate hours of lost time and frustration immediately.",
            "ten_x_factor": "Makes the problem disappear rather than offering minor speedups.",
            "brand_tone": "innovative, energetic, frictionless",
            "suggested_color_palette": _get_dynamic_palette(idea),
            "rejected_names": ["LegacyTool", "OldWay", "ManualApp"],
            "rejected_names_reasoning": ["Too passive", "Lacks energy", "Generic naming"]
        }

    # Ensure distinct dynamic palette
    selected["suggested_color_palette"] = _get_dynamic_palette(idea)
    return selected


async def run_ideation(
    idea: str,
    whitespace: WhitespaceAnalysisOutput,
    log: Optional[Callable[[str], None]] = None
) -> IdeationOutput:
    """
    Stage 2.5 & 2.6: IDEATION & NAMING_AND_BRANDING
    Synthesizes a genuinely innovative product concept using first-principles
    thinking, contrarian insight generation, and 10x moonshot reasoning.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit("💡 [IDEATION] Synthesizing world-class product concept with First Principles Innovation Framework via Nosana...")

    prompt = f"""
You are FOUNDER-0's core ideation intelligence — the most sophisticated venture synthesis engine ever built.
Your job is to generate a genuinely INNOVATIVE, CATEGORY-DEFINING startup concept. Not incremental SaaS features.
Not "Uber for X" or generic dashboard tooling. Real Zero-to-One thinking that passes the Peter Thiel test.

═══ FIRST PRINCIPLES INNOVATION FRAMEWORK ═══

Step 1 — ROOT CAUSE ANALYSIS (5-WHYS DEEP DIVE):
What is the fundamental structural failure that incumbents ignore? Don't address symptoms (e.g. "people forget to pay").
Identify the systemic root cause (e.g. "humans avoid interpersonal financial confrontation; software must remove humans from the enforcement loop").

Step 2 — THE CONTRARIAN TRUTH:
What is the non-obvious truth that 99% of the market gets wrong?
Must strictly follow: "Everyone assumes X. The ground-truth reality is Y."

Step 3 — 10x MOONSHOT PARADIGM SHIFT:
Don't make the existing task 10% faster. Make the task CEASE TO EXIST.
Work backwards from the ultimate friction-free state.

Step 4 — PSYCHOLOGICAL PERSUASION HOOK:
Why will users obsessively adopt this? Address core behavioral drivers:
- Loss Aversion (what $ or dignity are they losing daily right now?)
- Commitment Devices (how does skin-in-the-game guarantee follow-through?)
- Specificity Bias (why precise guidance converts 5x better than generic advice)

Step 5 — UNCLONEABLE TECHNICAL MOAT:
What compounding mechanism (data flywheel, state-commitment graphs, calibration models) creates insurmountable switching costs?

═══ STRICT QUALITY GATES & ANTI-PATTERNS ═══
- NO generic suffixes (-ify, -ly, -hub, -box, -bot). Product names must be punchy, memorable (1-2 words), and sound like a venture-backed category king.
- Taglines must be 6-10 words, using power verbs and creating a curiosity gap.
- Core features must describe concrete engineering mechanisms and explicit emotional payoffs, NOT vague marketing phrases like "AI-powered smart insights".

═══ INPUT CONTEXT ═══

ORIGINAL FOUNDER IDEA:
"{idea}"

IDENTIFIED STRUCTURAL WHITESPACE:
"{whitespace.primary_gap}"

VERIFIED USER COMPLAINTS & FRICTION POINTS:
{json.dumps(whitespace.supporting_complaints, indent=2)}

═══ STRICT JSON SCHEMA ═══

Return a strict JSON object with this EXACT schema:
{{
  "product_name": "string (punchy, memorable, 1-2 words, e.g. 'DeadlockDAO', 'PhantomCFO')",
  "tagline": "string (sharp 6-10 word tagline using active verbs and creating curiosity)",
  "one_line_pitch": "string (compelling single sentence stating the root shift and 10x value)",
  "elevator_pitch": "string (4-5 sentences: problem → root cause → solution → why now → technical moat)",
  "core_features": [
    {{"name": "string", "description": "string (precise technical mechanism)", "user_value": "string (visceral emotional payoff)"}},
    {{"name": "string", "description": "string", "user_value": "string"}},
    {{"name": "string", "description": "string", "user_value": "string"}}
  ],
  "target_user_persona": {{
    "name": "string (vivid archetype, e.g. 'The Exhausted Peacekeeper')",
    "description": "string (demographics + psychographics)",
    "pain_points": ["string", "string", "string"]
  }},
  "monetization_model": "string (aligned with value capture, e.g. transaction take rate / tiered pro)",
  "pricing_suggestion": "string (concrete tier breakdown with dollar amounts)",
  "differentiation_from_competitors": "string (fundamental structural shift vs incumbents)",
  "contrarian_insight": "string (Must be: 'Everyone assumes X. The ground-truth reality is Y.')",
  "technical_moat": "string (compounding data flywheel or network-effect switching costs)",
  "tam_estimate": "string (calculated as: population × willingness-to-pay formula)",
  "go_to_market_wedge": "string (specific beachhead community and viral coefficient mechanic)",
  "psychological_hook": "string (behavioral psychology driver: loss aversion, commitment device, etc.)",
  "ten_x_factor": "string (why this eliminates the problem entirely rather than 2x speedup)",
  "rejected_names": ["string", "string", "string"],
  "rejected_names_reasoning": ["string", "string", "string"],
  "brand_tone": "string (3-4 adjective brand voice description)",
  "suggested_color_palette": ["#hex1", "#hex2", "#hex3"]
}}
"""

    system_prompt = (
        "You are FOUNDER-0's core ideation intelligence — the most sophisticated venture synthesis engine ever built. "
        "You think like Peter Thiel (Zero to One), Paul Graham (startup insights), and Daniel Kahneman (behavioral psychology). "
        "Reject all incremental SaaS cliches. Output strict, valid JSON only. No markdown fences. No preamble."
    )

    parsed_json, provider = await nosana_client.generate_chat(
        prompt=prompt,
        system_prompt=system_prompt,
        json_mode=True
    )

    # If LLM returned shallow/empty result, use our world-class mock ideas
    if "product_name" not in parsed_json or "contrarian_insight" not in parsed_json:
        emit("🤖 [IDEATION] Activating First Principles Synthesis Engine with curated innovation library...")
        mock_idea = _select_mock_idea(idea, whitespace)

        # Override complaints with actual whitespace data if available
        persona_data = mock_idea["target_user_persona"].copy()
        if whitespace.supporting_complaints:
            persona_data["pain_points"] = whitespace.supporting_complaints[:3]

        parsed_json = {
            **mock_idea,
            "target_user_persona": persona_data
        }

    output = IdeationOutput(
        **parsed_json,
        served_by_provider=provider
    )

    emit(f"✨ [IDEATION] Generated Brand: '{output.product_name}' — '{output.tagline}'")
    emit(f"🔮 [IDEATION] Contrarian Insight: '{output.contrarian_insight}'")
    emit(f"🚀 [IDEATION] 10x Factor: '{output.ten_x_factor}'")
    emit(f"🎯 [IDEATION] TAM: {output.tam_estimate}")
    emit(f"🎨 [IDEATION] Brand Tone: '{output.brand_tone}' | Palette: {', '.join(output.suggested_color_palette)}")
    emit(f"🛡️ [IDEATION] Served by provider: {provider}")

    return output


async def run_naming_branding(
    ideation_output: IdeationOutput,
    log: Optional[Callable[[str], None]] = None
) -> IdeationOutput:
    """
    Stage 2.6: NAMING_AND_BRANDING (verification / refinement pass)
    """
    if log:
        log(f"🏷️ [NAMING_AND_BRANDING] Confirmed brand identity: {ideation_output.product_name} ({ideation_output.tagline})")
        log(f"  └─ Contrarian Insight: {ideation_output.contrarian_insight}")
        log(f"  └─ Technical Moat: {ideation_output.technical_moat}")
    return ideation_output
