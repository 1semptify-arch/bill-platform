"""Canonical content and seed records for the Minnesota Rent Assurance & Deposit Protection Act."""

BILL_META = {
    "short_title": "Minnesota Rent Assurance & Deposit Protection Act",
    "working_name": "Turnbuchalla Model — Working Statutory Draft",
    "jurisdiction": "State of Minnesota",
    "amends": "Minn. Stat. § 504B.178",
    "stage": "Working Draft — Pre-Introduction",
    "updated": "2026-11-14",
    "thesis": (
        "Move every residential security deposit into bonded custodial escrow, "
        "replace unilateral deposit deductions with independent adjudication, "
        "and back verified tenant hardship with a three-source rent assurance pool — "
        "with zero subrogation debt."
    ),
    "summary_points": [
        {
            "id": "pillar-escrow",
            "label": "Title I · Deposit Escrow",
            "headline": "Landlords never hold deposits; neutral adjudicators decide claims.",
            "detail": "Deposits sit in bonded custodial escrow for the tenancy. Tenants earn statutory 1% interest plus clean-year surplus dividends; pooled net float (~3%, ~$23.4M/yr at scale) funds administration and independent adjudication.",
            "clause_ref": "I-1",
        },
        {
            "id": "pillar-assurance",
            "label": "Title II · Rent Assurance",
            "headline": "Verified hardship rent is paid from a three-source pool — never clawed back.",
            "detail": "During verified job loss or medical crisis, the pool pays covered rent directly to the housing provider. Funded by ~3% deposit float (~$3.25/mo), monthly M1PR tax-credit advance (~$6/mo), and matched landlord share (~$6/mo).",
            "clause_ref": "II-3",
        },
        {
            "id": "pillar-fairness",
            "label": "Fairness & Anti-Capture",
            "headline": "Symmetric fraud penalties, public claims registry, and a 5-year sunset.",
            "detail": "Paid claims end the matter (no subrogation). Fabricated landlord claims and false fraud referrals carry symmetric penalties; tenant abuse is bounded by verified triggers, per-lease caps, and renewal pricing.",
            "clause_ref": "I-4",
        },
    ],
}

JOURNEY_STAGES = [
    {"step": 1, "name": "Concept & Audit", "state": "done", "note": "Three-source braid + UK custodial & APTC precedents audited Oct 2026"},
    {"step": 2, "name": "Working Draft", "state": "current", "note": "Titles I–IV structured in public; open questions flagged for actuarial & statutory review"},
    {"step": 3, "name": "Statutory & Actuarial Check", "state": "next", "note": "504B practitioner read + FHF / MHFA pilot actuarial validation"},
    {"step": 4, "name": "Legislative Sponsors", "state": "upcoming", "note": "Post-certification House & Senate Housing committee chairs (2027–28 session)"},
    {"step": 5, "name": "Committee & Pilot", "state": "upcoming", "note": "Public testimony, Revisor engrossment, MHFA LIHTC pilot fiscal note"},
    {"step": 6, "name": "Floor & Enactment", "state": "upcoming", "note": "5-year statutory sunset with mandatory Year-3 committee report"},
]

TITLES = [
    {
        "num": 0,
        "code": "PREAMBLE",
        "name": "Preamble & Definitions",
        "subtitle": "Legislative findings and statutory scope across Minnesota residential tenancies.",
    },
    {
        "num": 1,
        "code": "TITLE I",
        "name": "Deposit Protection",
        "subtitle": "The self-funding custodial core. Amends Minn. Stat. § 504B.178. Modeled on UK Tenancy Deposit Protection (operating nationally since 2007).",
    },
    {
        "num": 2,
        "code": "TITLE II",
        "name": "Rent Assurance",
        "subtitle": "State-chartered guarantee pool administered on an unemployment-insurance precedent, beginning with an MHFA pilot on publicly subsidized stock.",
    },
    {
        "num": 3,
        "code": "TITLE III",
        "name": "Renter's Belongings Coverage",
        "subtitle": "Integrated contents line (fire, water, theft) riding the same pool; final cap and opt-in mechanics deferred to actuarial review.",
    },
    {
        "num": 4,
        "code": "TITLE IV",
        "name": "Governance, Home Agency & Review",
        "subtitle": "Anti-capture board composition, MHFA home agency, administrative appeal standard, and mandatory 5-year sunset.",
    },
]

CLAUSES = [
    {
        "id": "P-1",
        "title_num": 0,
        "heading": "Legislative findings",
        "status": "modeled",
        "statute_text": (
            "Deposit disputes and serial nonpayment filings consume a third to a half of Minnesota's "
            "23,282 to 25,847 annual eviction filings. Private 'deposit insurance' surety products pay "
            "the landlord and pursue the tenant through collection — creating new debt rather than protection. "
            "Custodial deposit protection with free independent adjudication has operated nationally in the "
            "United Kingdom since 2007, funded off pooled escrow float."
        ),
        "plain_text": (
            "Roughly a third to half of Minnesota eviction filings trace back to deposit conflicts or short-term "
            "income shocks. Commercial 'deposit replacement' bonds still bill the renter afterward. Putting deposits "
            "in neutral custody and funding dispute resolution from interest float is already proven at national scale."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Explains why fee-based 'deposit alternatives' leave renters owing money at move-out.",
        "provider_note": "Recognizes the $5,600–$7,400 provider loss per eviction that fast assurance prevents.",
        "lawmaker_note": "Grounds single-subject jurisdiction ('residential rental risk') in MN Judicial Branch filing data.",
        "refs": ["C-02", "C-04", "C-05"],
    },
    {
        "id": "D-1",
        "title_num": 0,
        "heading": "Core definitions & scope",
        "status": "modeled",
        "statute_text": (
            "'Residential landlord' attaches directly to the residential rental agreement rather than a municipal "
            "rental license, ensuring uniform statewide coverage across jurisdictions without local licensing. "
            "Defines 'Pool,' 'Fund,' 'Administrator,' 'Independent Adjudicator,' 'Covered Hardship,' "
            "'Manufactured Claim,' and 'Clean Year.'"
        ),
        "plain_text": (
            "Applies to any residential lease in Minnesota whether or not the city has a rental licensing ordinance, "
            "so rural and suburban rentals follow the exact same rules as metro units."
        ),
        "audiences": ["provider", "lawmaker"],
        "renter_note": "Covers your lease anywhere in Minnesota, regardless of city licensing rules.",
        "provider_note": "One uniform statewide definition — no patchwork municipal compliance.",
        "lawmaker_note": "Avoids Minnesota's municipal-licensing gap by attaching to the lease relationship under Ch. 504B.",
        "refs": ["C-01"],
    },
    {
        "id": "I-1",
        "title_num": 1,
        "heading": "Custodial escrow",
        "status": "locked",
        "statute_text": (
            "Every residential security deposit is paid into bonded program escrow at lease signing and held there "
            "for the duration of the tenancy. The residential landlord never holds, commingles, itemizes, or "
            "unilaterally retains the deposit. Statutory one percent (1%) simple annual interest under Minn. Stat. "
            "§ 504B.178, subd. 2 continues to accrue to the tenant."
        ),
        "plain_text": (
            "At move-in, your security deposit goes into a state-bonded neutral account instead of the landlord's bank "
            "account. It stays safe there until move-out and still earns your guaranteed 1% annual interest."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Your deposit cannot be spent, lost in a property sale, or held hostage at move-out.",
        "provider_note": "Eliminates separate trust-account bookkeeping and 21-day statutory penalty traps.",
        "lawmaker_note": "Directly amends Minn. Stat. § 504B.178 custodial mechanics; preserves the 1% tenant floor.",
        "refs": ["C-01", "C-10"],
    },
    {
        "id": "I-2",
        "title_num": 1,
        "heading": "Independent claims adjudication",
        "status": "locked",
        "statute_text": (
            "Deposit and unit-damage claims at termination of tenancy are decided by an independent adjudication "
            "body operating on an administrative-law model. Neither the residential landlord nor the administering "
            "insurance carrier decides claims."
        ),
        "plain_text": (
            "At move-out, if there is a disagreement over damage, a neutral referee — not the landlord and not the "
            "insurance administrator — reviews photos and records from both sides and decides who gets paid."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Ends unilateral deduction letters; deductions require neutral review before money moves.",
        "provider_note": "Valid documented damage is paid cleanly on a fixed administrative timetable without conciliation court.",
        "lawmaker_note": "Separates carrier administration from claim adjudication to prevent insurer capture.",
        "refs": ["C-10"],
    },
    {
        "id": "I-3",
        "title_num": 1,
        "heading": "Tenant counter-claim lane",
        "status": "locked",
        "statute_text": (
            "Tenants may initiate deposit return and statutory-remedy claims directly through the same independent "
            "adjudication body without filing fees; the administrator answers to claimants on equal footing."
        ),
        "plain_text": (
            "Renters do not have to pay court filing fees or take a day off work for conciliation court to get "
            "their deposit returned — they use the exact same online or mail claim lane."
        ),
        "audiences": ["renter", "lawmaker"],
        "renter_note": "Zero filing fee to request your deposit return if a landlord fails to sign off at move-out.",
        "provider_note": "Resolves move-out disputes in days without courtroom legal fees.",
        "lawmaker_note": "Diverts high-volume § 504B.178 deposit disputes out of district and conciliation court dockets.",
        "refs": ["C-02"],
    },
    {
        "id": "I-4",
        "title_num": 1,
        "heading": "No subrogation",
        "status": "locked",
        "statute_text": (
            "A claim paid from the pool or escrow is final and is not recoverable from the tenant by the fund, "
            "the administering carrier, the landlord, or any assignee or collection agency."
        ),
        "plain_text": (
            "When the insurance pool pays a covered claim, the matter is over. Nobody can turn around and send "
            "collectors after the renter for what the pool paid."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Locked non-negotiable: true insurance protection, never a disguised surety loan.",
        "provider_note": "You get paid promptly without chasing former tenants through collection agencies.",
        "lawmaker_note": "The core statutory distinction between pooled insurance and commercial surety-bond products.",
        "refs": ["C-04", "C-06"],
    },
    {
        "id": "I-5",
        "title_num": 1,
        "heading": "Claims-free dividend (renter)",
        "status": "locked",
        "statute_text": (
            "Tenancies completing a clean lease year with zero paid claims earn the renter an annual dividend "
            "declared from pool surplus above reserve targets, in addition to the statutory 1% deposit interest "
            "(mutual insurance model; declared from actual surplus, not a guaranteed fixed payout)."
        ),
        "plain_text": (
            "Every year a lease runs cleanly with no claims, renters earn a bonus dividend when the pool has surplus "
            "on top of their guaranteed 1% interest."
        ),
        "audiences": ["renter", "provider"],
        "renter_note": "Rewards taking care of your home with an annual cash or credit dividend in surplus years.",
        "provider_note": "Aligns tenant financial incentives directly with unit care and lease compliance.",
        "lawmaker_note": "Mutual-pool surplus mechanics (SFM precedent) avoid state general-fund liability.",
        "refs": ["C-01", "C-09"],
    },
    {
        "id": "I-6",
        "title_num": 1,
        "heading": "Public claims registry",
        "status": "locked",
        "statute_text": (
            "Aggregate per-owner and per-property-portfolio claims frequency and manufactured-claim findings are "
            "published in an open public registry, governed by Fair Credit Reporting Act (FCRA)-modeled accuracy, "
            "notice, and dispute-correction rules. No individual tenant identities appear in the public registry."
        ),
        "plain_text": (
            "Renters and cities can look up a building owner's aggregate track record on deposit claims before signing "
            "a lease — with strict accuracy and correction rights for owners and zero tenant names published."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "See whether a building routinely files inflated move-out claims before you rent there.",
        "provider_note": "Clean operators can prove their fair track record publicly; FCRA dispute rules protect against errors.",
        "lawmaker_note": "Replaces opaque anecdotes with auditable portfolio-level data while keeping zero tenant PII.",
        "refs": ["C-03"],
    },
    {
        "id": "I-7",
        "title_num": 1,
        "heading": "Manufactured-claim & false-referral penalties",
        "status": "locked",
        "statute_text": (
            "A damage or hardship claim proven fabricated carries an experience-rating surcharge plus statutory "
            "penalty and referral. Symmetric penalties apply to any knowingly false fraud referral made against a "
            "tenant, with mandatory tenant notice, evidentiary threshold, and a defense window before any external "
            "referral transmits."
        ),
        "plain_text": (
            "Staging fake damage claims or making false fraud accusations carries matching financial penalties for "
            "both sides, and a renter always gets notice and a chance to respond before any fraud referral leaves the agency."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Blocks retaliatory 'fraud' threats by requiring real proof, prior notice, and symmetric penalties.",
        "provider_note": "Deters fraudulent tenant hardship filings alongside bad-actor landlord claims.",
        "lawmaker_note": "Symmetric deterrence satisfies due-process and bipartisan fairness scrutiny.",
        "refs": ["C-08"],
    },
    {
        "id": "I-8",
        "title_num": 1,
        "heading": "Self-funding of Title I via escrow float",
        "status": "modeled",
        "statute_text": (
            "Net investment yield on pooled custodial deposits above the 1% statutory tenant interest (~3% net yield "
            "on Treasury-grade instruments, modeled at ~$23.4M/year statewide) funds escrow custody and independent "
            "adjudication, with adjudication carrying its own dedicated statutory budget line."
        ),
        "plain_text": (
            "Investing pooled deposits safely in U.S. Treasuries earns roughly 4%. After paying tenants their 1%, "
            "the remaining ~3% (~$23.4M/year statewide) pays for the escrow system and neutral referees without new taxes."
        ),
        "audiences": ["provider", "lawmaker"],
        "renter_note": "No fee is deducted from your deposit principal to run the escrow or dispute system.",
        "provider_note": "No per-unit escrow administrative fee.",
        "lawmaker_note": "Dedicated adjudication budget line prevents administrative starving of neutral review.",
        "refs": ["C-01", "C-10"],
    },
    {
        "id": "I-9",
        "title_num": 1,
        "heading": "Regulation of private deposit-alternative products",
        "status": "locked",
        "statute_text": (
            "Commercial security-deposit replacement products may be offered in Minnesota only if they include "
            "statutory no-subrogation, refundable principal or capped mutual cost, and mandatory reporting through "
            "the public claims registry."
        ),
        "plain_text": (
            "Private 'zero-deposit' companies can only operate in Minnesota if they follow the same rules: no "
            "chasing tenants for paid claims and full public reporting."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Closes the loophole where monthly 'deposit fee' apps charge non-refundable fees and still sue you.",
        "provider_note": "Levels the playing field so compliant coverage isn't undercut by predatory surety bonds.",
        "lawmaker_note": "Prevents regulatory arbitrage around Minn. Stat. § 504B.178.",
        "refs": ["C-06"],
    },
    {
        "id": "II-1",
        "title_num": 2,
        "heading": "Covered hardship rent assurance",
        "status": "modeled",
        "statute_text": (
            "The Rent Assurance Fund pays covered monthly rent directly to the residential landlord during verified "
            "tenant income hardship arising from a defined statutory trigger list (involuntary job loss, severe "
            "medical crisis, or habitability displacement, verified under unemployment-insurance documentation "
            "standards) for a bounded coverage term (2 to 6 months, subject to actuarial schedule)."
        ),
        "plain_text": (
            "If a renter loses their job or faces a documented medical emergency, the pool pays rent straight to "
            "the landlord for a set bridge period (2–6 months) while the household stabilizes — preventing eviction."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Keeps your family housed and keeps an eviction filing off your court record during a real crisis.",
        "provider_note": "Rent arrives on time during tenant emergencies instead of months of unpaid rent and court costs.",
        "lawmaker_note": "Uses proven UI verification triggers; coverage term (2–6 mo) flagged for actuarial calibration.",
        "refs": ["C-02", "C-05", "C-07"],
    },
    {
        "id": "II-2",
        "title_num": 2,
        "heading": "Forward-rent stability plan; zero backward debt",
        "status": "locked",
        "statute_text": (
            "Covered rent paid by the Fund during a hardship window is not recoverable from the tenant. Any "
            "post-hardship payment plan applies solely to forward rent accruing after the coverage period ends "
            "and operates as a condition of continued ongoing coverage, never as back-debt collection."
        ),
        "plain_text": (
            "Rent paid by the pool during your covered emergency is forgiven, not turned into a mountain of back "
            "rent. Once coverage ends, any payment plan only covers future months going forward."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Prevents the 'cliff' where emergency help ends and you still owe thousands in back arrears.",
        "provider_note": "Delivers a clean ledger transition after the hardship window with clear forward expectations.",
        "lawmaker_note": "Contrasts deliberately with France's Visale surety clawback model.",
        "refs": ["C-04"],
    },
    {
        "id": "II-3",
        "title_num": 2,
        "heading": "Three-source funding braid & mutual dividends",
        "status": "modeled",
        "statute_text": (
            "Participation is mandatory statewide upon rollout and funded by three braided legs (~$15.33/unit/month "
            "base case at $1,300 rent, ~1.18% of rent): (a) Escrowed deposit net float (~$3.25/unit/mo); "
            "(b) Renter-side share (~$6/unit/mo) paid as a monthly advance from the Minnesota Renter's Credit "
            "(M1PR) reconciled on the annual return via CRP e-file rails (federal APTC / Form 8962 model; over-cap "
            "renters pay ~$6/mo directly, disclosed); and (c) Landlord matched share (~$6/unit/mo) priced on a "
            "community-rated base plus bounded experience band, earning a no-claim dividend in surplus years."
        ),
        "plain_text": (
            "Roughly $15.33/month per unit comes from three small shares: ~$3.25 from deposit interest float, "
            "~$6 advanced from the existing MN Renter's Credit (or paid directly by high-income renters), and "
            "~$6 matched by the landlord (who gets a rebate dividend in clean years)."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "For M1PR-eligible renters (up to $77,570 income), your ~$6/mo share comes from your existing credit — $0 new out-of-pocket.",
        "provider_note": "~$6/mo (~$72/yr) replaces $5,600–$7,400 eviction losses, with mutual rebates for clean buildings.",
        "lawmaker_note": "Rides existing DOR M1PR ($2,720 max) + mandatory CRP e-file rails; split ratio awaits actuarial sign-off.",
        "refs": ["C-07", "C-08", "C-09", "C-10", "C-11"],
    },
    {
        "id": "II-4",
        "title_num": 2,
        "heading": "Year-one reserve ramp & trust-fund backstop",
        "status": "open",
        "statute_text": (
            "Title II claim payouts phase in as custodial escrow crosses statutory reserve thresholds over the "
            "12-month lease-migration ramp, or via a repayable state startup advance amortized against future "
            "premiums on the unemployment-insurance trust-fund precedent."
        ),
        "plain_text": (
            "Because deposits move into escrow gradually as leases renew over year one, reserve build is bridged "
            "either by a phased coverage start or a repayable state startup loan paid back by future pool premiums."
        ),
        "audiences": ["lawmaker"],
        "renter_note": "Ensures the pool cannot run dry in its first year.",
        "provider_note": "Guarantees claim solvency from day one of active coverage.",
        "lawmaker_note": "OPEN DRAFTING CALL: choose reserve-threshold phase-in vs. repayable UI-style startup advance.",
        "refs": ["C-09", "C-12"],
    },
    {
        "id": "II-5",
        "title_num": 2,
        "heading": "Tenant-side actuarial & anti-abuse controls",
        "status": "locked",
        "statute_text": (
            "Solvency and fairness are enforced on the tenant side through UI-verified hardship triggers, "
            "per-lease coverage caps, claims-history pricing tiers at lease renewal, and mandatory cooperation "
            "with forward-rent stabilization plans."
        ),
        "plain_text": (
            "Protects the pool against gaming: hardship must be documented like unemployment insurance, each lease "
            "has a clear cap, repeat claims affect renewal tiering, and forward rent plans require cooperation."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Keeps premiums tiny (~1.18% of rent) by stopping repeat abuse before it drains the mutual pool.",
        "provider_note": "Ensures Rent Assurance is a verified hardship bridge, not an open-ended rent holiday.",
        "lawmaker_note": "Enacts the Fairness Axiom: symmetric guardrails on both sides of the lease.",
        "refs": ["C-07", "C-08"],
    },
    {
        "id": "II-6",
        "title_num": 2,
        "heading": "MHFA subsidized-housing pilot authority",
        "status": "modeled",
        "statute_text": (
            "Minnesota Housing (MHFA) is authorized to operate Title II first as a bounded pilot across Low-Income "
            "Housing Tax Credit (LIHTC) and agency-financed properties; audited pilot loss ratios and administrative "
            "data constitute the empirical fiscal note for statewide rollout."
        ),
        "plain_text": (
            "Minnesota Housing can test Rent Assurance first on affordable housing properties it already oversees, "
            "producing real Minnesota loss numbers before expanding statewide."
        ),
        "audiences": ["provider", "lawmaker"],
        "renter_note": "Starts protection fastest in affordable properties where eviction risk is sharpest.",
        "provider_note": "Proves claim turnarounds and loss math on real Minnesota buildings before statewide mandate.",
        "lawmaker_note": "De-risks the legislative fiscal note by generating real in-state actuarial data first.",
        "refs": ["C-07"],
    },
    {
        "id": "III-1",
        "title_num": 3,
        "heading": "Renter's personal belongings line (deferred parameters)",
        "status": "open",
        "statute_text": (
            "Personal-contents coverage for fire, water, and theft rides the same pool infrastructure as a third "
            "coverage line, coordinating habitability displacement with Title II as a single integrated claim. "
            "Mandatory vs. opt-in election, coverage cap, and deductible remain OPEN pending actuarial pricing."
        ),
        "plain_text": (
            "Adds basic protection for a renter's furniture, clothes, and essentials in a fire, flood, or theft — "
            "handled in one claim if a building emergency forces a move. Final price/opt-in waits for actuarial math."
        ),
        "audiences": ["renter", "lawmaker"],
        "renter_note": "One claim covers both emergency housing stability and replacing essentials after a fire or flood.",
        "provider_note": "Reduces uninsured tenant displacement friction after building water or fire losses.",
        "lawmaker_note": "OPEN: ~$10–$15/mo modeled contents load makes opt-in vs. mandatory the main actuarial swing variable.",
        "refs": ["C-07"],
    },
    {
        "id": "IV-1",
        "title_num": 4,
        "heading": "Anti-capture governing board",
        "status": "locked",
        "statute_text": (
            "The Pool Governing Board includes statutory voting seats reserved for residential tenants and "
            "independent consumer advocates alongside housing-provider, actuarial, and agency representatives."
        ),
        "plain_text": (
            "Renters and consumer advocates hold guaranteed voting seats on the board that oversees the pool, "
            "alongside property owners and insurance experts."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Renters sit at the table setting rules and reviewing dividends — never locked out.",
        "provider_note": "Balanced board representation with housing providers and actuaries.",
        "lawmaker_note": "Structural safeguard against agency or industry capture.",
        "refs": [],
    },
    {
        "id": "IV-2",
        "title_num": 4,
        "heading": "Home agency & contracted carrier administration",
        "status": "open",
        "statute_text": (
            "The Fund is housed at Minnesota Housing (MHFA), claims adjudication sits in an independent administrative "
            "body, and day-to-day pool servicing is contracted to a licensed insurer (State Fund Mutual workers'-comp "
            "precedent)."
        ),
        "plain_text": (
            "Minnesota Housing oversees the public fund, an experienced licensed insurer runs day-to-day claims "
            "operations, and a separate neutral body decides disputes."
        ),
        "audiences": ["provider", "lawmaker"],
        "renter_note": "Professional insurance servicing speed backed by public oversight.",
        "provider_note": "Claims processed on commercial insurance rails rather than slow agency paperwork.",
        "lawmaker_note": "OPEN: final confirmation of MHFA vs. Commerce permanent home post-pilot (SFM precedent).",
        "refs": [],
    },
    {
        "id": "IV-3",
        "title_num": 4,
        "heading": "Administrative review & appeal standard",
        "status": "open",
        "statute_text": (
            "Adjudication determinations are subject to expedited administrative reconsideration followed by "
            "judicial review in Minnesota district court; the statutory standard of review (substantial-evidence "
            "record review vs. de novo) is flagged OPEN for legislative counsel."
        ),
        "plain_text": (
            "Either side can appeal a referee's decision — first through fast internal review, and then to "
            "district court if needed."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Preserves your constitutional right to court review if an adjudicator errs.",
        "provider_note": "Clear appeal path for high-value or contested property damage determinations.",
        "lawmaker_note": "OPEN: select Chapter 14 substantial-evidence review vs. de novo district court standard.",
        "refs": [],
    },
    {
        "id": "IV-4",
        "title_num": 4,
        "heading": "Five-year sunset & mandatory Year-3 report",
        "status": "locked",
        "statute_text": (
            "The Act carries a five-year statutory sunset from statewide effective date, paired with a mandatory "
            "Year-3 actuarial, eviction-diversion, and claims-registry audit delivered to the House and Senate "
            "housing committees."
        ),
        "plain_text": (
            "The law automatically expires after 5 years unless the Legislature votes to renew it after reviewing "
            "a full Year-3 audit of real costs, claims, and eviction reductions."
        ),
        "audiences": ["renter", "provider", "lawmaker"],
        "renter_note": "Public Year-3 report proves whether renters are getting deposits back faster and keeping homes.",
        "provider_note": "Guarantees the Legislature must fix or end the program if loss ratios miss targets.",
        "lawmaker_note": "Checkable legislative promise — lowers enactment risk by requiring affirmative renewal.",
        "refs": [],
    },
    {
        "id": "IV-5",
        "title_num": 4,
        "heading": "Single-subject conforming clause",
        "status": "locked",
        "statute_text": (
            "All M1PR advance-reconciliation and escrow-float provisions are enacted strictly as funding machinery "
            "dedicated to residential rental risk inside this Act, conforming to Minn. Const. art. IV, § 17."
        ),
        "plain_text": (
            "Keeps every piece of the bill focused on one constitutional subject — residential rental risk — "
            "so the credit-advance mechanics cannot be challenged as a separate tax bill."
        ),
        "audiences": ["lawmaker"],
        "renter_note": "Protects the law against technical constitutional challenges after passage.",
        "provider_note": "Ensures deposit and assurance funds cannot be raided for unrelated state budgets.",
        "lawmaker_note": "Drafted explicitly for Minnesota's strict Art. IV, § 17 single-subject jurisprudence.",
        "refs": ["C-11"],
    },
]

CLAIMS_LEDGER = [
    {
        "id": "C-01",
        "figure": "1% annual",
        "claim": "Statutory simple interest floor on residential security deposits in Minnesota.",
        "source": "Minn. Stat. § 504B.178, subd. 2",
        "status": "verified",
        "checked": "2026-11-02",
        "derivation": "Direct statutory text verified against MN Office of the Revisor of Statutes.",
    },
    {
        "id": "C-02",
        "figure": "23,282 – 25,847",
        "claim": "Annual residential eviction filings across Minnesota district courts (25,847 in 2023; 23,282 in 2024).",
        "source": "Minnesota Judicial Branch Annual Eviction Dashboards (2023–2024)",
        "status": "verified",
        "checked": "2026-10-23",
        "derivation": "Statewide court-record totals published by MN Judicial Branch.",
    },
    {
        "id": "C-03",
        "figure": "44.6%",
        "claim": "Share of eviction filings concentrated in serial/repeat filings (~30% of filing households).",
        "source": "Princeton Eviction Lab — Serial Eviction Filings Study",
        "status": "verified",
        "checked": "2026-10-23",
        "derivation": "Peer-reviewed multi-state court-record analysis demonstrating repeat-filing concentration.",
    },
    {
        "id": "C-04",
        "figure": "$9 Billion",
        "claim": "Estimated U.S. tenant rental and surety collection debt burden highlighted in federal enforcement.",
        "source": "Consumer Financial Protection Bureau (CFPB) Rental Debt Report",
        "status": "verified",
        "checked": "2026-10-23",
        "derivation": "CFPB market snapshot on rental debt collection and deposit-alternative clawbacks.",
    },
    {
        "id": "C-05",
        "figure": "$5,600 – $7,400",
        "claim": "Average direct financial cost to a housing provider per completed eviction (turnover, legal, vacancy, arrears).",
        "source": "Harris County / Innovation for Justice (i4J) Eviction Cost Model",
        "status": "verified",
        "checked": "2026-10-23",
        "derivation": "Provider-side cost accounting benchmark (~$72/yr landlord match vs. $5.6K–$7.4K eviction loss).",
    },
    {
        "id": "C-06",
        "figure": "3% – 7% of rent",
        "claim": "Typical annual price charged by commercial rent-default / surety carriers for narrower coverage.",
        "source": "Internal market survey (whitepaper L48)",
        "status": "estimate",
        "checked": "2026-10-23",
        "derivation": "Modeled benchmark from private carrier rate filings; awaits formal actuarial comparison.",
    },
    {
        "id": "C-07",
        "figure": "$15.33/mo (1.18%)",
        "claim": "Base-case three-source pooled cost per unit at $1,300 monthly rent (~$106M claims vs. ~$110M net funding).",
        "source": "Turnbuchalla Math Audit 2026-10-23 (whitepaper L99)",
        "status": "estimate",
        "checked": "2026-10-23",
        "derivation": "~$3.25 net deposit float + ~$6.04 M1PR advance + ~$6.04 landlord match = $15.33/mo (~1.18% of $1,300 rent).",
    },
    {
        "id": "C-08",
        "figure": "$21.23/mo (1.63%)",
        "claim": "Fraud/moral-hazard stress scenario (+30% claims shock above base case).",
        "source": "Turnbuchalla Stress Model (whitepaper L100)",
        "status": "estimate",
        "checked": "2026-10-23",
        "derivation": "$138M stressed claims × 1.25 admin/reserve load less $23.4M float = $21.23/unit/mo (~1.63% of $1,300 rent).",
    },
    {
        "id": "C-09",
        "figure": "$30.00/mo (2.31%)",
        "claim": "Severe recession shock scenario (6% statewide lease default rate); ~$4M/yr reserve build in normal years.",
        "source": "Turnbuchalla Stress Model (whitepaper L101–L104)",
        "status": "estimate",
        "checked": "2026-10-23",
        "derivation": "$185M recession claims load = $30.00/unit/mo (~2.31% of $1,300 rent), buffered by multi-year surplus reserves.",
    },
    {
        "id": "C-10",
        "figure": "~$23.4M/yr (3% net)",
        "claim": "Net annual custodial deposit float on ~$780M escrowed statewide deposits (4% Treasury yield minus 1% tenant floor).",
        "source": "Turnbuchalla Float Restatement 2026-10-23 (whitepaper L114)",
        "status": "estimate",
        "checked": "2026-10-23",
        "derivation": "Corrected 10/23 to subtract tenant's 1% statutory interest: 3% × ~$780M = ~$23.4M/yr (~$39/unit/yr ≈ $3.25/mo).",
    },
    {
        "id": "C-11",
        "figure": "$2,720 max / $77,570 cap",
        "claim": "Minnesota Renter's Credit (M1PR) maximum annual credit and household income eligibility cap.",
        "source": "Minnesota Department of Revenue — TY2025 M1PR Schedule",
        "status": "verified",
        "checked": "2026-10-23",
        "derivation": "Published MN DOR tax-year 2025 parameters (~$72/yr renter share uses <3% of max credit).",
    },
    {
        "id": "C-12",
        "figure": "12-month ramp",
        "claim": "Year-1 custodial deposit migration averages ~50% steady-state float as leases turn over across 12 months.",
        "source": "Turnbuchalla Migration Schedule 2026-10-23",
        "status": "estimate",
        "checked": "2026-10-23",
        "derivation": "Uniform monthly lease-renewal assumption; motivates Clause II-4 startup advance or reserve threshold.",
    },
]

LOCKED_DECISIONS = [
    {"num": 1, "clause": "I-4", "title": "No subrogation — paid claim ends the matter", "why": "Separates true pooled insurance from surety-bond debt collection."},
    {"num": 2, "clause": "II-3", "title": "Mandatory three-source braid + experience band", "why": "Prevents adverse selection while rewarding clean buildings with no-claim dividends."},
    {"num": 3, "clause": "I-2", "title": "Independent adjudication + tenant counter-claim lane", "why": "Neither the landlord nor the carrier decides deposit or damage claims."},
    {"num": 4, "clause": "IV-1", "title": "Statutory tenant & consumer seats on governing board", "why": "Structural anti-capture governance."},
    {"num": 5, "clause": "I-7", "title": "Symmetric manufactured-claim & false-referral penalties", "why": "Equal deterrence against staged claims and retaliatory fraud accusations."},
    {"num": 6, "clause": "I-6", "title": "Public aggregate claims registry (FCRA dispute rules)", "why": "Market transparency per portfolio with zero tenant PII."},
    {"num": 7, "clause": "IV-4", "title": "Five-year sunset + mandatory Year-3 committee audit", "why": "Checkable promise that requires empirical results to renew."},
    {"num": 8, "clause": "III-1", "title": "Integrated belongings line (parameters post-actuarial)", "why": "Coordinates habitability displacement and contents loss without guessing price early."},
]

SEED_MARKS = [
    {
        "id": "M-0001",
        "clause_id": "II-3",
        "kind": "question",
        "quote_text": "over-cap renters pay ~$6/mo directly, disclosed",
        "proposed_text": "",
        "body": "How does a renter above the $77,570 M1PR income cap pay the ~$6/month share in practice — on the lease ledger or on state tax filing?",
        "author_label": "St. Paul Renter",
        "reply_to": "",
        "status": "published",
        "response_body": "Collected as an explicitly itemized ~$6/month statutory pool line or reconciled cleanly on the MN return via the CRP e-file rail — never buried inside base rent or marked up with landlord admin fees. Final collection rail is flagged for DOR technical review.",
        "responder_role": "Drafting Table",
        "created_at": "2026-11-12T14:20:00Z",
    },
    {
        "id": "M-0002",
        "clause_id": "I-4",
        "kind": "question",
        "quote_text": "A claim paid from the pool or escrow is final and is not recoverable from the tenant",
        "proposed_text": "",
        "body": "If there is zero subrogation, what stops a bad-faith tenant from trashing a unit or skipping rent intentionally and walking away clean?",
        "author_label": "Small Duplex Owner (4 units, Duluth)",
        "reply_to": "",
        "status": "published",
        "response_body": "Three statutory controls in Clauses I-7 and II-5: (1) intentional/criminal destruction is excluded from hardship coverage; (2) hardship triggers require UI-grade verification (involuntary job loss or documented medical crisis); and (3) paid-claim history prices future renewal tiers and caps per-lease payouts.",
        "responder_role": "Drafting Table",
        "created_at": "2026-11-13T09:45:00Z",
    },
    {
        "id": "M-0003",
        "clause_id": "I-2",
        "kind": "edit",
        "quote_text": "decided by an independent adjudication body operating on an administrative-law model",
        "proposed_text": "Specify a 14-calendar-day decision clock from close of evidence and allow smartphone photo/video uploads without notarization.",
        "body": "In UK custodial schemes, clear timelines keep units turning over without holding up either party. Adding an explicit 14-day adjudication clock in I-2 would help both small landlords and moving renters.",
        "author_label": "Housing Policy Researcher",
        "reply_to": "",
        "status": "published",
        "response_body": "Strong operational point — logged for Title I statutory text integration alongside Minn. Stat. § 504B.178's existing 21-day baseline.",
        "responder_role": "Statutory Review Lane",
        "created_at": "2026-11-13T16:10:00Z",
    },
    {
        "id": "M-0004",
        "clause_id": "II-6",
        "kind": "comment",
        "quote_text": "",
        "proposed_text": "",
        "body": "Starting Title II as an MHFA pilot on LIHTC properties is the right sequence — those properties already submit standardized compliance reporting, so loss-ratio data will be clean for committee fiscal staff.",
        "author_label": "Nonprofit Housing Developer",
        "reply_to": "M-0001",
        "status": "published",
        "response_body": "",
        "responder_role": "",
        "created_at": "2026-11-14T08:30:00Z",
    },
    {
        "id": "M-0005",
        "clause_id": "IV-3",
        "kind": "question",
        "quote_text": "substantial-evidence record review vs. de novo",
        "proposed_text": "",
        "body": "Would de novo review in district court recreate the exact court congestion Title I is meant to relieve, unless filing requires posting the disputed amount?",
        "author_label": "Appellate Practitioner (queued sample)",
        "reply_to": "",
        "status": "queued",
        "response_body": "",
        "responder_role": "",
        "created_at": "2026-11-14T11:15:00Z",
    },
]

SEED_REQUESTS = [
    {
        "id": "R-0001",
        "req_type": "briefing",
        "clause_id": "II-3",
        "org_or_role": "Legislative Fiscal Staff — Housing Division",
        "contact_info": "staff-briefing-demo@house.mn.example (steward-only field)",
        "summary": "20-minute walkthrough on the M1PR monthly advance reconciliation mechanics and Year-1 LIHTC pilot sizing.",
        "details": "Interested in how CRP e-file enrollment handles mid-year tenant moves between buildings.",
        "stance": "neutral",
        "status": "scheduled",
        "steward_note": "Prepared 1-page APTC/CRP reconciliation diagram; holding formal pitch wave until committee org session.",
        "is_public": 1,
        "created_at": "2026-11-12T15:00:00Z",
    },
    {
        "id": "R-0002",
        "req_type": "amendment",
        "clause_id": "I-1",
        "org_or_role": "Rural Property Manager (18 units, Mankato)",
        "contact_info": "",
        "summary": "Allow electronic ACH/check deposit transmittal within 5 business days of lease signing for rural banks.",
        "details": "Instant point-of-signing wire can be slow for smaller regional credit unions; a 5-business-day transmittal window matches escrow norms.",
        "stance": "conditional",
        "status": "reviewing",
        "steward_note": "Checking UK custodial 14-day deposit protection window precedent — very reasonable operational buffer.",
        "is_public": 1,
        "created_at": "2026-11-13T12:40:00Z",
    },
    {
        "id": "R-0003",
        "req_type": "position",
        "clause_id": "",
        "org_or_role": "Minnesota Tenant-Landlord Mediation Coalition (Demo Record)",
        "contact_info": "",
        "summary": "Supports Title I custodial escrow and independent adjudication; monitoring Title II actuarial split.",
        "details": "Neutral custodial holding removes hostility at lease end while preserving 100% of documented damage recovery.",
        "stance": "support",
        "status": "incorporated",
        "steward_note": "Recorded on the public positions ledger.",
        "is_public": 1,
        "created_at": "2026-11-14T09:05:00Z",
    },
]
