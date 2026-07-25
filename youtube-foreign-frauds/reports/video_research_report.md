# Foreign Frauds — Video Research Report

**Prepared:** 2026-07-06 · **Data snapshot:** YouTube Data API v3 (public metadata) + web fact-checking
**Scope:** Establish what our inspiration channels do well, define the content target, and produce a
ranked, saturation-tested shortlist of *foreign* (non-EU/US) frauds we can turn into videos.

---

## 1. Executive summary

- **The format that works** (from analysing the two inspiration channels) is a **named protagonist +
  downfall arc + a concrete dollar figure**, told in a tight **12–20 min** long-form documentary,
  released while the story still has relevance. Timeliness is the single biggest performance lever.
- **Our lane** is *under-highlighted non-EU/US financial crime* — big scale, strong protagonist,
  evergreen (not hype). We already do the money-in-the-title hook well ($300M, $12.8B).
- **Where the open opportunity actually is:** **China, the Middle East (UAE/Turkey), and Africa.**
  These have huge, dramatic, genuinely *under-covered-in-English* cases. **India is saturated**
  (its domestic YouTube ecosystem has already done the big stories), and the famous global cases
  (1MDB, OneCoin) are taken.
- **Recommended first two videos:** **Ezubao** (China, $7.6B, essentially uncovered) and
  **Abraaj** (UAE, elite rise-and-fall story, only a WSJ mini-doc exists). One Asian, one Middle
  Eastern; both large, both open.

---

## 2. Method

1. **Inspiration baselining** — pulled the 50 most-recent long-form uploads for each reference
   channel via the Data API and computed an **age-adjusted** performance measure (`views/day` =
   total views ÷ days since publish) so recent and older videos compare fairly. Also measured
   length, cadence, engagement, and title patterns. (`channel_analysis.py`)
2. **Candidate discovery** — web search + fact-checking to assemble fraud candidates fitting the DNA.
3. **Saturation probe** — for each candidate, searched YouTube and pulled the view counts of the
   *biggest existing video* on the topic. A low ceiling = under-covered = opportunity. (`youtube_saturation.py`)
4. **Human correction** — the saturation score is coarse; foreign-language news clips and tangential
   videos are filtered out by hand in the verdicts below.

> **Tooling note:** all of the above runs from the cloud environment because it only touches
> `www.googleapis.com`. Transcript-level competitor analysis (scraping youtube.com) is blocked here
> and must run locally.

---

## 3. Inspiration-channel baselines

| Metric | Logically Answered | ColdFusion |
|---|--:|--:|
| Median views (recent 50) | **181K** | **714K** |
| Views/day (age-adjusted) | 1,965 | 3,339 |
| Typical length | ~15 min | ~20 min |
| Upload cadence | every ~3 days | every ~7 days |
| Median engagement (likes+comments/views) | 3.5% | 3.8% |
| Titles with a number / money / question | 10% / 6% / 8% | 19% / 6% / 4% |

**Two playbooks.** ColdFusion is the *prestige* model — ~4× the median views, longer, slower,
big evergreen swings. Logically Answered is the *velocity* model — half the length, 2×+ the cadence,
hits driven by this week's drama. **The velocity model is the realistic starting point for a young
channel** (cheaper per video, more at-bats), graduating toward ColdFusion length/production over time.

### What actually drives their top performers
1. **Downfall narratives** — schadenfreude is the engine: *collapse, disaster, prison, "getting what
   they deserve."* Fraud is a native fit (ColdFusion's *"Another Forbes 30u30 Facing Prison"* did 3.4× baseline).
2. **A named protagonist** — always a specific company/person, never an abstract theme.
3. **Timeliness** — the very top videos are days old (Logically's *"tokens are getting too expensive"*
   hit **92K views/day** at 3 days); the weakest are older, structural, evergreen-decline pieces.
4. **Curiosity-gap titles** — Logically reuses the franchise template *"X Is (Finally) Getting What
   They Deserve…"* + ellipses; ColdFusion uses clean declaratives. Short: 37–43 characters.
5. **Consistency** — tight length band + predictable cadence.

### Implications for us
- **The "foreign" angle is open space** — both inspirations skew US/Western tech & business.
- **A dollar figure in the title is an edge, not a cliché** — only 6% of either channel's titles cite
  a sum, yet fraud stories come with built-in numbers. Lean in (we already do).
- **Chase recency**, but pick stories with enough substance to stay evergreen (à la Luckin Coffee).

---

## 4. Target profile (channel DNA)

> **Under-highlighted, non-EU/US financial crime — big scale, strong protagonist/company, evergreen.**
> Weighted toward China/Korea and now broadened to any non-standard-EU/US region (Middle East,
> Africa, South Asia, Japan, Russia, SE Asia, Latin America). Avoid pure-hype/recency-only crypto
> stories that won't age well.

---

## 5. Master candidate table (saturation-tested)

"Best existing video" = the most-viewed YouTube treatment we found; low views (or only
regional-language / small-channel coverage) = an open lane. Verdicts are hand-corrected.

| Candidate | Region | Scale | Best existing (views · channel) | Read |
|:--|:--|:--|:--|:--|
| **Ezubao** | China | $7.6B | ~300 · small | 🟢 Wide open |
| **Abraaj** | UAE/Dubai | ~$1B | 116K · WSJ | 🟢 Open (only a mini-doc) |
| **Kingold** | China | $2.8B | 264K · *tangential* | 🟢 Open (no direct doc) |
| **NMC Health** | UAE | $4B | 28K · Malayalam | 🟢 English near-zero |
| **Thodex** | Turkey | ~$2B | 100K · German | 🟢 English lane open |
| **Steinhoff** | S. Africa | $7.4B | 191K · SA channel | 🟢 Under-covered intl. |
| **Truong My Lan** | Vietnam | $27B | 254K · news clip | 🟡 No long-form doc yet |
| **Mirror Trading Intl** | S. Africa | $588M | 75K · small | 🟡 Open but crypto |
| **Çiftlik Bank** | Turkey | $130M | 73K · Turkish | 🟡 Open but small scale |
| **Zhongzhi** | China | $64B | ~1K · small | 🟡 Open but diffuse (no protagonist) |
| **Oceanografía** | Mexico | $400M | <1K · Spanish | 🟡 Open but small/complex |
| **MMM / Mavrodi** | Russia | ~10M victims | 267K · "Scams" | 🟡 Room for a definitive telling |
| **Lai Xiaomin** | China | executed | 1.6M · China Uncensored | 🟠 Covered (political angle) |
| **Hin Leong** | Singapore | $3.5B | 604K · Bloomberg | 🟠 Moderately covered |
| **Olympus** | Japan | $1.7B | 796K · WS Millennial | 🟠 A strong version exists |
| **Daewoo** | S. Korea | $43B | 1.0M · Asianometry | 🟠 Strong version exists |
| **Satyam** | India | $1.5B | 2.9M · FinnovationZ | 🔴 Saturated |
| **OneCoin** | Bulgaria | $4B | 2.6M · BBC | 🔴 Saturated |
| **1MDB** | Malaysia | $4.5B | 4.3M · MagnatesMedia | 🔴 Saturated |
| **Nirav Modi** | India | $2B | 8.5M · Nitish Rajput | 🔴 Saturated |
| **Sahara** | India | $3–4B | 10.9M · small | 🔴 Saturated |
| **Harshad Mehta** | India | $1B (’92) | 23.6M · *Scam 1992* | 🔴 Saturated |

---

## 6. Recommended videos (deep detail)

### Tier 1 — make these first

**① Ezubao — China · $7.6B P2P Ponzi**
- **Story:** Ding Ning fabricated ~95% of investment projects and defrauded **900,000 people**.
  Lavish spending (a reported $20M+ villa gifted to an executive, cars, property). When it collapsed,
  staff **buried 1,200+ account books in 80 bags six metres underground** — police needed excavators.
  Ding got life.
- **Why:** biggest human scale on the board, a built-in $7.6B number, and **near-zero English
  coverage**. Evergreen morality tale.
- **Working title:** *"$7 Billion Buried in 80 Bags — China's Biggest Ponzi."*

**② Abraaj — UAE/Dubai · ~$1B**
- **Story:** Arif Naqvi built the emerging-markets private-equity darling (Gates Foundation money in
  his health fund), then misused fund cash; collapsed 2018. Arrested in London 2019, still fighting
  US extradition. "The Key Man." An elite rise-and-fall protagonist.
- **Why:** arguably the best *story* we found; only a WSJ mini-doc (~116K) exists. Wide open.
- **Working title:** *"The $1 Billion Man Who Fooled Bill Gates."* (verify framing before use)

### Tier 2 — strong follow-ups

**③ Kingold — China · $2.8B fake gold.** 83 tonnes of **gilded copper** pledged as gold collateral;
chairman Jia Zhihong. Unbeatable visuals; no direct documentary exists. On-brand fake-X title.

**④ Steinhoff — S. Africa · $7.4B.** "Enron of South Africa"; CEO **Markus Jooste died by suicide in
2024** as prosecution loomed. Huge number, tragic recent ending, global retailer most viewers
unknowingly touched. Under-covered internationally.

**⑤ Thodex — Turkey · ~$2B.** Founder fled with users' crypto, caught in Albania, **sentenced to
11,196 years** — the absurd sentence is an instant title/thumbnail. English lane open.

**⑥ NMC Health — UAE · $4B hidden debt.** Migrant-pharmacist BR Shetty built a FTSE-100 hospital
empire that hid billions; collapsed 2020. Rags-to-riches-to-ruin arc; English coverage near-zero.

### Notable, with caveats
- **Truong My Lan (Vietnam, $27B)** — largest bank fraud in history; richest-woman arc. **Fact check:**
  her death sentence is being **commuted to life** (Vietnam abolished the death penalty for embezzlement
  in June 2025); she must still repay ~$11B. Frame as "the $27B queen," not "facing execution." Region
  is SE Asia, not China/Korea — include only if widening past our core.
- **Lai Xiaomin (China, executed)** — 3 tonnes of cash in an apartment he called "the supermarket,"
  executed 2021. Elite hook, but China Uncensored's version (~1.6M) means we'd need a distinct angle.
- **Zhongzhi (China, $64B)** — biggest number, but diffuse and protagonist-light; harder to make gripping.

---

## 7. Strategic insights

- **Middle East & Africa are the sweet spot** — large, dramatic, and genuinely under-covered in English.
- **India is a trap** despite great stories — its domestic YouTube is enormous, so Nirav Modi (8.5M),
  Sahara (10.9M), *Scam 1992*/Harshad Mehta (23.6M), Satyam (2.9M) are already saturated. Skip unless
  we have a sharply differentiated angle.
- **Competitor to add to our watch-list:** **MagnatesMedia** — did 1MDB at 4.3M and works this exact
  genre. Worth baselining alongside Logically Answered & ColdFusion.
- **The Korea gap** — we specifically want Korean stories, but the best-scale one (**Daewoo**, $43B) is
  already well covered (Asianometry, ~1M), while the under-covered Korean cases (Optimus, Wakon) carry
  Korean-language research friction or hype-risk. **Korea likely needs its own dedicated research pass.**

---

## 8. Next steps

1. **Green-light 1–2 titles** (recommended: Ezubao + Abraaj).
2. For each, build a **deep-research dossier**: timeline, key players, the "how the scam worked"
   mechanics, primary sources, and the strongest visual beats.
3. Produce a **title/thumbnail set (3–5 variants)** and a **video outline** in the proven
   named-protagonist + downfall + dollar-figure format.
4. **Optional:** fold **MagnatesMedia** into the channel-analysis baseline; run a **dedicated Korea pass**.

*Supporting data: `reports/synthesis.md` (inspiration analysis), `reports/shortlist.md` (ranked picks
+ appendix), `reports/saturation.md` / `reports/saturation_global.md` (coverage probes). Pipeline:
`channel_analysis.py`, `youtube_saturation.py`, `candidates.json`, `candidates_global.json`.*
