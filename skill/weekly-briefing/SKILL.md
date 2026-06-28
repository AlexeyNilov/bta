---
name: weekly-briefing
description: Produce an analytical weekly briefing on international affairs, Valencia and Spain, economics, business, markets, technology, AI, opportunities, and risks. Use when Codex is asked to create, refresh, or save a past-7-days global affairs briefing, especially a magazine-style report written for entrepreneurial generalists and saved as input/weekly_report.md.
---

# Weekly Briefing

## Goal

Write a concise, analytical weekly briefing that explains what mattered in the past 7 days, why it mattered, where opportunities or risks may be forming, and what to watch next. The default output path is `input/weekly_report.md` unless the user names another file.

Do not add links, the goal is to create text easily convertable to speech.

## Workflow

1. Define the reporting window.
   - Use the current date and cover the previous 7 calendar days.
   - State the exact date range in the briefing.
   - If the user specifies a different range, use that range.

2. Gather current evidence.
   - Browse or otherwise verify current events; do not rely on model memory for time-sensitive claims.
   - Prefer primary sources, official releases, central banks, regulators, election authorities, company filings, and reputable news wires or international outlets.
   - Cross-check major claims when possible, especially casualty figures, election results, market-moving policy decisions, sanctions, and earnings.

3. Select for lasting significance.
   - Prioritize developments likely to affect geopolitics, security, macro policy, capital allocation, technology strategy, supply chains, regulation, or institutional trust.
   - Look for entrepreneurial signals: new constraints, regulatory shifts, bottlenecks, unmet demand, adoption curves, capital misallocation, local advantages, and incumbents under pressure.
   - Include contrarian angles when evidence supports them, especially where consensus narratives may be too optimistic, too pessimistic, or missing second-order effects.
   - Avoid filling space with daily market moves, routine political theater, or single-company noise unless it signals a broader structural shift.
   - Include fewer, better-explained stories rather than comprehensive headline coverage.

4. Draft into `input/weekly_report.md`.
   - Use Markdown headings exactly as listed in "Required Structure".
   - Target roughly 2,000-3,000 words unless the user requests otherwise.
   - Keep prose analytical, concise, objective, and intellectually curious.

5. Review before finalizing.
   - Confirm each section has enough substance and no obvious stale claims.
   - Separate facts from analysis with phrasing such as "The immediate effect is..." and "The risk is...".
   - Define technical terms briefly on first use.
   - Remove clickbait, partisan framing, sensational language, and unsupported predictions.

6. Convert to mp3

```bash
BTA_VOICE=charles bta convert input/weekly_report.md
bash scripts/merge_wavs.sh ./output
mv output/output.mp3 output/weekly_report.mp3
rm output/*.wav
```

## Required Structure

Use this section order:

```markdown
# Weekly Briefing: YYYY-MM-DD to YYYY-MM-DD

## Executive Summary

## World Affairs

## Valencia & Spain

## Business & Markets

## Economics

## Technology & AI

## The Bigger Picture

## Opportunities & Risks

## Looking Ahead
```

## Section Guidance

### Executive Summary

Write 5-10 bullets highlighting the week's most important developments. Each bullet should combine event plus significance; avoid headline-only bullets. Include at least one bullet that frames a notable opportunity and at least one that frames a notable risk.

### World Affairs

Cover major geopolitical events, diplomacy, conflicts, elections, international organizations, and policy changes. For each selected story, explain:

- What happened
- Why it matters
- What could happen next

### Valencia & Spain

Cover the most consequential local and national developments affecting Valencia, the Valencian Community, and Spain.

Include local stories when they have civic, economic, social, environmental, infrastructure, housing, tourism, technology, business, cultural, or policy significance. Connect local developments to wider Spanish, European, or global trends when useful, but do not force a global angle.

For each selected story, explain:

- What happened locally or nationally
- Why it matters for people or institutions in Valencia and Spain
- What could happen next

If the week is genuinely quiet in Valencia, say so briefly and focus the section on the most relevant Spain-wide developments instead.

### Business & Markets

Discuss the biggest developments in companies, industries, markets, trade, and finance. Emphasize structural trends: capital spending, supply chains, regulation, competition, credit conditions, energy markets, trade realignment, and sector strategy.

### Economics

Explain major macroeconomic developments, including inflation, interest rates, central banks, employment, trade, fiscal policy, energy, and commodities when relevant. Emphasize implications rather than statistics; use statistics only when they clarify the point.

### Technology & AI

Cover important developments in AI/LLM, semiconductors, cybersecurity, software, major technology companies, and scientific breakthroughs. Prioritize developments likely to shape the next several months.

### The Bigger Picture

Identify 3-5 themes connecting events across politics, economics, business, and technology. Explain how these trends reinforce or contradict one another.

### Opportunities & Risks

Identify 4-8 practical opportunities and risks suggested by the week's events. Write for an entrepreneurial reader who wants to notice where conditions are changing before they become obvious.

For each item:

- Name the opportunity or risk plainly
- Explain the causal mechanism, not just the trend label
- Distinguish what is known from what is a hypothesis
- State what evidence would confirm or weaken the thesis

Good items may involve business formation, market positioning, career bets, local Valencia or Spain opportunities, regulatory arbitrage, AI adoption, supply-chain changes, energy and infrastructure constraints, tourism and housing pressures, or capital-market risks.

Use a mildly contrarian lens, but do not force contrarianism. A useful contrarian point should challenge a lazy consensus and explain why the common reading may be incomplete.

### Looking Ahead

Identify the most important events, decisions, earnings, policy announcements, elections, product launches, or meetings expected in the coming week. For each, explain why it deserves attention.

## Style Rules

- Write like the editor of a weekly international affairs and economics magazine.
- Assume an educated generalist reader.
- Prefer depth over breadth.
- Maintain an entrepreneurial lens: ask who gains leverage, who loses pricing power, what bottlenecks appear, and where incentives are changing.
- Surface opportunities and risks without giving personalized financial, legal, or investment advice.
- Be willing to be mildly contrarian, but only when the argument is evidence-based and falsifiable.
- Explain trade-offs and second-order consequences.
- Avoid false precision; name uncertainty where evidence is incomplete.
- Do not use partisan labels as analysis.
- Do not overfit the report to the loudest news cycle.

## Prepare for naration

Shape prepared Markdown for narration by adding inline pause tags. Preserve prose exactly except for trailing pause tags.

Supported syntax is `[1s]`, `[1.5s]`, or `[0.25s]`. Unsupported pause text will be spoken, so validate tags after editing.

### Default Timing

- Chapter-level headings: `[2s]`
- Section-level headings: `[2s]`
- Ordinary paragraphs: `[1.5s]`
