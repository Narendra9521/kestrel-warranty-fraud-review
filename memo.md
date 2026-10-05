# Memo to Ritu: warranty fraud flag

**Decision.** Act first on the simple rules below, which need no model, and use the model only as a ranking aid for the investigation desk (40 claims a month). Do not make accuracy the board's KPI.

**Why not "above 97%".** About 97 in 100 claims are genuine, so a model that flags nothing already scores about 97% and stops no fraud. The board number should be: *fraud rupees stopped, minus Rs 380 goodwill for each genuine customer we hold, per 40 claims checked.*

**The number, tested strictly.** I replayed June 2026 week by week, letting the model use only what Kestrel would have known at the time (investigation outcomes arrive about 30 days after a claim; this is an assumption, the export has no decision dates). Result: 9 of the 22 June frauds were in the top 40. That stops Rs 13,100 of fraud and holds 31 genuine customers (Rs 11,800), **net about Rs 1,400, with a plausible range of -Rs 7,500 to +Rs 12,800**. If the Rs 260 cost of each investigation is also counted, it is a loss. So the model alone is not yet proven to pay for itself. It was weak because the 1 May rule change created new fraud and the model needs a few weeks of labelled examples to learn it. The final model is trained on all data to June, so it should do better, but I cannot prove that.

**What worked better.** A plain rule (small uninspected claim at an outlet under a year old, plus the customer's earlier claims) found 16 of the 22 frauds in the same test, net about Rs 8,000-13,500. That is why the actions below come first.

**Your hunch about new partners: half right.** Since 1 May, when claims under Rs 2,000 stopped needing inspection, fraud at new partners is about 16% (34 of 211 claims), against about 0.2% at older ones (2 of 1,211). But it is five outlets, not all new ones: SP3160 (Pune), SP3232 (Jaipur), SP3318 (Hubballi), SP3129 (Chennai) and SP3319 (Warangal) account for 29 of the 36 confirmed frauds (Rs 42,000 claimed). Most new partners are clean, as Meenal said. Fraud also bunches just under the limit, at Rs 1,900-1,999 (about 9% fraud, against about 3% for other small claims). 

**Next week.**
1. Put those five outlets back on mandatory inspection.
2. Require inspection for claims of Rs 1,900-1,999.
3. Run the model's top 40 and the rule's list side by side for one month, record every outcome, and keep whichever pays better.
4. Ask Tanmay to export open cases as blank, not 0.

**Be aware.** Only 36 frauds exist since the May change, so the model is a ranking aid, not proof against any outlet or customer. Retrain monthly, as outcomes arrive. Outlets may adapt by moving amounts below Rs 1,900.
