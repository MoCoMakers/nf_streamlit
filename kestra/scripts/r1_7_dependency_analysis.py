#!/usr/bin/env python3
"""r1_7_dependency_analysis.py — R1.7 orthogonal genetic-dependency validation.

QUESTION (Reviewer 1, point 7): validate the top S' hits with INDEPENDENT evidence.
APPROACH: for each S'-flagged drug target, test whether RNAi knockdown of that target gene
reproduces the genotype-selective vulnerability S' detected from PRISM drug response — a
different assay (genetic perturbation, not drug) on the same lung-cancer genotype framework.

FULL METHODOLOGY (suitable for Methods):
  Data. DepMap RNAi dependencies, DEMETER2 v6 "combined" model (McFarland et al.,
    Nat Commun 2018), warehouse table raw_depm_demeter_combined_gene_dep_scores
    (gene x cell line; more-negative score = stronger dependency). Genotypes from
    im_dep_sprime_damaging_mutations; cell-line bridge (CCLE name <-> DepMap ACH id) from
    im_sprime_solved_s_prime. Cohort = lung cell lines (ccle_name LIKE '%_LUNG').
  Genotype split. For each tumour-suppressor gene a line is 'mutant' if it carries a
    biallelic damaging alteration (mutation_value=2) and 'wild-type' if it carries none
    (mutation_value=0); heterozygous (1) lines are excluded. [Genotype rule per manuscript
    Methods — confirm against Methods before submission.]
  Target genes. The mechanism-of-action targets of the curated S' gold hits: RB1 ->
    AURKB/PLK1/CHEK1 (synthetic-lethal positives) and CDK4/CDK6 (negative controls);
    TP53 -> KIF11/CENPE (positives) and MDM2 (negative control); CDKN2A -> AURKB/PLK1/KIF11
    (positives) and CDK6 (the cross-genotype 'mirror' — expected selective in CDKN2A where it
    is resistant in RB1). PTEN is omitted (only n=2 mutant lung lines with RNAi).
  Statistic. Per (genotype, target) pair: DeltaRNAi = mean(mutant) - mean(wild-type).
    Significance by a PERMUTATION rank-sum test — the Mann-Whitney U computed on average ranks,
    with a two-sided null built from N label permutations (robust to the small mutant arms and
    to ties; no normal approximation). p-values are FDR-controlled (Benjamini-Hochberg) across
    the panel. A pair is 'concordant' if sign(DeltaRNAi) matches the S' prediction (positives:
    mutant MORE dependent, Delta<0; negative controls: mutant NOT dependent, Delta>0).

Credentials come from PG* env vars (never hardcoded; this file is git-tracked). Read-only
account is sufficient. Usage:
  PGHOST=... PGUSER=... PGPASSWORD=... PGDATABASE=... \
    python r1_7_dependency_analysis.py --outdir /tmp/r1_7 [--nperm 20000]
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
import numpy as np
import pandas as pd
import psycopg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GENO_ID = {"RB1": 4890, "TP53": 7115, "CDKN2A": 17047}
# (genotype, target symbol, DEMETER gene label, role)
#   role SL/MIRROR -> expect mutant MORE dependent (Delta<0); NEG -> expect NOT dependent (Delta>0)
PAIRS = [
    ("RB1",    "AURKB", "AURKB (9212)", "SL"),
    ("RB1",    "PLK1",  "PLK1 (5347)",  "SL"),
    ("RB1",    "CHEK1", "CHEK1 (1111)", "SL"),
    ("RB1",    "CDK4",  "CDK4 (1019)",  "NEG"),
    ("RB1",    "CDK6",  "CDK6 (1021)",  "NEG"),
    ("TP53",   "KIF11", "KIF11 (3832)", "SL"),
    ("TP53",   "CENPE", "CENPE (1062)", "SL"),
    ("TP53",   "MDM2",  "MDM2 (4193)",  "NEG"),
    ("CDKN2A", "AURKB", "AURKB (9212)", "SL"),
    ("CDKN2A", "PLK1",  "PLK1 (5347)",  "SL"),
    ("CDKN2A", "KIF11", "KIF11 (3832)", "SL"),
    ("CDKN2A", "CDK6",  "CDK6 (1021)",  "MIRROR"),
]
EXPECT_NEG = {"SL", "MIRROR"}   # roles expecting Delta < 0

QUERY = """
WITH bridge AS (
  SELECT DISTINCT depmap_id, ccle_name FROM im_sprime_solved_s_prime WHERE ccle_name LIKE '%%\\_LUNG'
),
geno AS (
  SELECT b.ccle_name, g.gene_id, g.mutation_value
  FROM im_dep_sprime_damaging_mutations g JOIN bridge b ON b.depmap_id = g.cell_line
  WHERE g.gene_id IN (4890,7115,17047) AND g.mutation_value IN (0,2)
),
dep AS (
  SELECT ccle_id, gene, dep_score FROM raw_depm_demeter_combined_gene_dep_scores
  WHERE gene IN ('AURKB (9212)','PLK1 (5347)','CHEK1 (1111)','CDK4 (1019)','CDK6 (1021)',
                 'KIF11 (3832)','CENPE (1062)','MDM2 (4193)')
)
SELECT geno.gene_id, dep.gene AS target, geno.ccle_name, geno.mutation_value, dep.dep_score
FROM geno JOIN dep ON dep.ccle_id = geno.ccle_name
"""


def db_from_env():
    need = ("PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE")
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        sys.exit(f"ERROR: set env vars {missing} (read-only account is fine).")
    return dict(host=os.environ["PGHOST"], port=int(os.environ.get("PGPORT", "5432")),
                dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
                password=os.environ["PGPASSWORD"], connect_timeout=30)


def rankdata(x):
    """Average ranks (ties shared) — numpy only."""
    x = np.asarray(x, float)
    order = x.argsort(kind="mergesort")
    ranks = np.empty(len(x), float)
    ranks[order] = np.arange(1, len(x) + 1)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return ranks


def mwu_U(a, b):
    comb = np.concatenate([a, b])
    r = rankdata(comb)
    R1 = r[:len(a)].sum()
    return R1 - len(a) * (len(a) + 1) / 2.0


def perm_ranksum_p(mut, wt, nperm, rng):
    """Two-sided permutation p for the Mann-Whitney U (label-shuffle null)."""
    n1 = len(mut)
    comb = np.concatenate([mut, wt])
    mu = n1 * len(wt) / 2.0
    obs_dev = abs(mwu_U(mut, wt) - mu)
    hits = 0
    for _ in range(nperm):
        p = rng.permutation(comb)
        if abs(mwu_U(p[:n1], p[n1:]) - mu) >= obs_dev - 1e-9:
            hits += 1
    return (hits + 1) / (nperm + 1)


def bh_fdr(p):
    p = np.asarray(p, float); n = len(p)
    order = p.argsort()
    ranked = p[order] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n); out[order] = np.clip(q, 0, 1)
    return out


def stars(q):
    return "***" if q < 0.001 else "**" if q < 0.01 else "*" if q < 0.05 else "·" if q < 0.10 else "ns"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--nperm", type=int, default=20000)
    a = ap.parse_args(argv)
    figs = a.outdir / "figures"; tabs = a.outdir / "tables"
    figs.mkdir(parents=True, exist_ok=True); tabs.mkdir(parents=True, exist_ok=True)

    with psycopg.connect(**db_from_env()) as conn:
        raw = pd.read_sql(QUERY, conn)
    raw.to_csv(tabs / "r1_7_rnai_per_line.csv", index=False)   # per-line input (for reproducibility/beeswarm)

    id2name = {v: k for k, v in GENO_ID.items()}
    rng = np.random.default_rng(20260613)
    rows, perline = [], {}
    for gtype, sym, demeter, role in PAIRS:
        gid = GENO_ID[gtype]
        sub = raw[(raw.gene_id == gid) & (raw.target == demeter)]
        mut = sub.loc[sub.mutation_value == 2, "dep_score"].to_numpy(float)
        wt = sub.loc[sub.mutation_value == 0, "dep_score"].to_numpy(float)
        if len(mut) < 2 or len(wt) < 2:
            continue
        delta = mut.mean() - wt.mean()
        p = perm_ranksum_p(mut, wt, a.nperm, rng)
        expect = "mutant more dependent" if role in EXPECT_NEG else "mutant NOT dependent"
        match = (delta < 0) if role in EXPECT_NEG else (delta > 0)
        rows.append(dict(genotype=gtype, target=sym, role=role, n_mut=len(mut), n_wt=len(wt),
                         dep_mut=round(mut.mean(), 3), dep_wt=round(wt.mean(), 3),
                         delta=round(delta, 3), expected=expect, concordant=bool(match), p_perm=p))
        perline[(gtype, sym)] = (mut, wt)

    res = pd.DataFrame(rows)
    res["q_bh"] = bh_fdr(res["p_perm"].to_numpy())
    res["sig"] = res["q_bh"].map(stars)
    res = res.sort_values(["genotype", "role", "target"]).reset_index(drop=True)
    res.to_csv(tabs / "r1_7_rnai_concordance.csv", index=False)
    print(res.to_string(index=False))
    print(f"\nConcordant: {res.concordant.sum()}/{len(res)} pairs; "
          f"q<0.05: {(res.q_bh < 0.05).sum()}")

    # ---- Figure 1: diverging Delta bars (the two-sided story) ----
    d = res.copy()
    d["signed"] = d["delta"]
    d = d.sort_values("signed")
    colors = ["#d7301f" if r == "NEG" else "#2c7fb8" for r in d["role"]]
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    y = np.arange(len(d))
    ax.barh(y, d["signed"], color=colors, edgecolor="0.3", linewidth=0.4)
    ax.axvline(0, color="0.3", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{g} · {t}" for g, t in zip(d.genotype, d.target)], fontsize=8.5)
    for yi, (val, s, m) in enumerate(zip(d["signed"], d["sig"], d["concordant"])):
        ax.annotate((s if s != "ns" else "") + ("  ✓" if m else "  ✗"),
                    (val, yi), xytext=(6 if val >= 0 else -6, 0), textcoords="offset points",
                    va="center", ha="left" if val >= 0 else "right", fontsize=7.5, color="0.25")
    ax.set_xlabel("ΔRNAi dependency  (mutant − wild-type) ·  ← mutant MORE dependent   |   mutant resistant →")
    ax.set_title("RNAi knockdown reproduces S′'s genotype-selective calls (DEMETER2, lung)")
    ax.scatter([], [], marker="s", color="#2c7fb8", label="S′ synthetic-lethal positive (expect ←)")
    ax.scatter([], [], marker="s", color="#d7301f", label="negative control (expect →)")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    fig.tight_layout(); fig.savefig(figs / "fig_r1_7_diverging.png", dpi=150); plt.close(fig)

    # ---- Figure 2: per-line beeswarm for the headline pairs ----
    heads = [("TP53", "KIF11"), ("RB1", "CDK6"), ("TP53", "MDM2")]
    heads = [h for h in heads if h in perline]
    fig, axes = plt.subplots(1, len(heads), figsize=(3.2 * len(heads), 4.2), sharey=False)
    if len(heads) == 1:
        axes = [axes]
    for ax, (gt, sym) in zip(axes, heads):
        mut, wt = perline[(gt, sym)]
        for xi, (vals, lab, col) in enumerate([(wt, "WT", "0.5"), (mut, "mut", "#2c7fb8")]):
            jitter = (rng.random(len(vals)) - 0.5) * 0.28
            ax.scatter(np.full(len(vals), xi) + jitter, vals, s=26, color=col, alpha=0.8, edgecolors="none")
            ax.hlines(vals.mean(), xi - 0.2, xi + 0.2, color="black", lw=2)
        ax.axhline(0, color="0.8", ls="--", lw=1)
        ax.set_xticks([0, 1]); ax.set_xticklabels([f"{gt}-WT", f"{gt}-mut"], fontsize=8)
        rrow = res[(res.genotype == gt) & (res.target == sym)].iloc[0]
        ax.set_title(f"{sym}\nΔ={rrow.delta:+.2f}  {rrow.sig}", fontsize=9)
        ax.set_ylabel("RNAi dependency (↓ stronger)") if ax is axes[0] else None
    fig.suptitle("Per-line target dependency by genotype (headline pairs)", fontsize=10)
    fig.tight_layout(); fig.savefig(figs / "fig_r1_7_beeswarm.png", dpi=150); plt.close(fig)

    print("\nwrote: r1_7_rnai_concordance.csv, r1_7_rnai_per_line.csv, "
          "fig_r1_7_diverging.png, fig_r1_7_beeswarm.png")


if __name__ == "__main__":
    main()
