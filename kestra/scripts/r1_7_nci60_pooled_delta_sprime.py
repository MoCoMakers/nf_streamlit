#!/usr/bin/env python3
"""r1_7_nci60_pooled_delta_sprime.py — R1.7 independent drug-platform validation (NCI-60).

QUESTION (Reviewer 1, point 7): validate the top S' hits with INDEPENDENT evidence — the
reviewer explicitly asked for "independent PRISM/CTRP/GDSC drug-response datasets". NCI-60 is
exactly that: a fully independent drug-response platform (different cell lines, assay, era).

APPROACH (mirrors the lung-paper pooled ΔpS' and the R1.7 RNAi pillar
r1_7_dependency_analysis.py, but on NCI-60 drug response instead of RNAi):
  For each S'-flagged (genotype-gene, drug-target) pair, pool NCI-60 S' BY THE GENE'S DAMAGING
  ALLELE — i.e. split cell lines into 'mutant' (biallelic-damaging) vs 'wild-type' for that gene,
  pool the S' of the target's compounds within each line, and test whether the genotype-selective
  pattern S' detected in PRISM reproduces on this independent platform.

DATA (REAL reporting warehouse — NOT the local experimental mirror):
  im_nci_nci60_doseresp_sprime_list  NCI-60 fitted S' per (NSC compound, DTP cell line).
  raw_nci_nsc_chemical_names         NSC -> compound name (target compounds matched by name).
  im_cellosaurus_nci60_to_depmap_bridge   NCI-60 DTP cell_name -> DepMap ACH (exact-only bridge).
  im_dep_sprime_damaging_mutations   genotypes (ACH-keyed): 0=WT, 1=het(excluded), 2=biallelic mut.
  Cohort = PAN-TISSUE (NCI-60 lung-only is underpowered; lung is a subset, reported separately).

GENOTYPE SPLIT. A line is 'mutant' for a gene if biallelic-damaging (mutation_value=2) and
  'wild-type' if it carries none (=0); heterozygous (1) excluded. [Confirm rule vs Methods.]

STATISTIC. Per (genotype, target) pair: per-line pooled S' (mean over the target's compounds);
  ΔS' = mean(WT lines) − mean(mutant lines), matching the lung ΔpS' sign convention
  (negative ⇒ mutant MORE sensitive ⇒ synthetic-lethal direction; positive ⇒ mutant resistant).
  Significance by a PERMUTATION rank-sum test (Mann-Whitney U on average ranks, label-shuffle
  null; robust to small arms/ties), BH-FDR across the pair family, 95% bootstrap CI on ΔS'.
  Admissibility: ≥3 mutant and ≥3 wild-type lines.
  [CONVENTION CAVEAT: assumes higher NCI-60 S' = stronger sensitivity, as in the lung pS'.
   Confirm the NCI-60 S' polarity against the fit definition before quoting directions.]

Credentials come from PG* env vars (never hardcoded; this file is git-tracked). Read-only
account is sufficient. Usage:
  PGHOST=dmvpetridishdatastore.dev PGUSER=compbio_dw_readonly PGPASSWORD=... PGDATABASE=data_warehouse \
    python r1_7_nci60_pooled_delta_sprime.py --outdir /tmp/r1_7_nci60 [--nperm 20000] [--nboot 5000]
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

GENO_ID = {"RB1": 4890, "TP53": 7115, "CDKN2A": 17047, "PTEN": 2239}

# NCI-60 compound name patterns per drug target (case-insensitive substring match).
# CDK4 and CDK6 are merged: NCI-60 carries only dual CDK4/6 inhibitors, none CDK4- or
# CDK6-selective, so the RNAi pillar's separate CDK4 / CDK6 columns collapse to one here.
TARGET_PATTERNS = {
    "AURKB":  ["barasertib", "AZD1152"],
    "PLK1":   ["volasertib", "BI-2536", "rigosertib"],
    "CHEK1":  ["prexasertib", "LY2603618"],
    "CDK4/6": ["palbociclib", "ribociclib", "abemaciclib"],
    "KIF11":  ["ispinesib", "monastrol", "SB-743921", "litronesib"],
    "CENPE":  ["GSK923295"],
    "MDM2":   ["nutlin", "AMG-232", "RG7388", "idasanutlin"],
}

# (genotype gene, drug target, role) — same hypotheses as the RNAi pillar.
#   SL / MIRROR -> expect mutant MORE sensitive (ΔS' < 0);  NEG -> expect mutant resistant (ΔS' > 0)
PAIRS = [
    ("RB1",    "CDK4/6", "NEG"),
    ("RB1",    "AURKB",  "SL"),
    ("RB1",    "PLK1",   "SL"),
    ("RB1",    "CHEK1",  "SL"),
    ("TP53",   "MDM2",   "NEG"),
    ("TP53",   "KIF11",  "SL"),
    ("TP53",   "CENPE",  "SL"),
    ("CDKN2A", "CDK4/6", "MIRROR"),
    ("CDKN2A", "AURKB",  "SL"),
    ("CDKN2A", "PLK1",   "SL"),
    ("CDKN2A", "KIF11",  "SL"),
]
EXPECT_NEG = {"SL", "MIRROR"}   # roles expecting ΔS' < 0


def db_from_env():
    need = ("PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE")
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        sys.exit(f"ERROR: set env vars {missing} (read-only account is fine).")
    return dict(host=os.environ["PGHOST"], port=int(os.environ.get("PGPORT", "5432")),
                dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
                password=os.environ["PGPASSWORD"], connect_timeout=30)


def rankdata(x):
    x = np.asarray(x, float)
    order = x.argsort(kind="mergesort")
    ranks = np.empty(len(x), float)
    ranks[order] = np.arange(1, len(x) + 1)
    sx = x[order]; i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return ranks


def mwu_U(a, b):
    r = rankdata(np.concatenate([a, b]))
    return r[:len(a)].sum() - len(a) * (len(a) + 1) / 2.0


def perm_ranksum_p(mut, wt, nperm, rng):
    n1 = len(mut); comb = np.concatenate([mut, wt]); mu = n1 * len(wt) / 2.0
    obs = abs(mwu_U(mut, wt) - mu); hits = 0
    for _ in range(nperm):
        p = rng.permutation(comb)
        if abs(mwu_U(p[:n1], p[n1:]) - mu) >= obs - 1e-9:
            hits += 1
    return (hits + 1) / (nperm + 1)


def boot_ci(mut, wt, nboot, rng):
    deltas = np.empty(nboot)
    for i in range(nboot):
        bm = rng.choice(mut, len(mut), replace=True)
        bw = rng.choice(wt, len(wt), replace=True)
        deltas[i] = bw.mean() - bm.mean()
    return np.percentile(deltas, 2.5), np.percentile(deltas, 97.5)


def bh_fdr(p):
    p = np.asarray(p, float); n = len(p); order = p.argsort()
    ranked = p[order] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n); out[order] = np.clip(q, 0, 1)
    return out


def stars(q):
    return "***" if q < 0.001 else "**" if q < 0.01 else "*" if q < 0.05 else "·" if q < 0.10 else "ns"


def load_data(conn):
    # 1) genotypes via the exact-only bridge (pan-tissue)
    q_geno = """
      SELECT b.cell_name, m.gene_id, m.mutation_value::text AS mv
      FROM im_cellosaurus_nci60_to_depmap_bridge b
      JOIN im_dep_sprime_damaging_mutations m
        ON m.cell_line = ANY(string_to_array(b.depmap_ach, '|'))
      WHERE b.depmap_ach IS NOT NULL
        AND m.gene_id IN (4890, 7115, 17047, 2239)
        AND m.mutation_value::text IN ('0', '2')
    """
    geno = pd.read_sql(q_geno, conn).drop_duplicates()

    # 2) NSC -> name for the target compounds
    pats = sorted({p for v in TARGET_PATTERNS.values() for p in v})
    where = " OR ".join(["name ILIKE %s"] * len(pats))
    names = pd.read_sql(
        f"SELECT DISTINCT nsc, name FROM raw_nci_nsc_chemical_names WHERE {where}",
        conn, params=["%%%s%%" % p for p in pats])
    # map each NSC to a target (first pattern that matches its name)
    def classify(nm):
        low = nm.lower()
        for tgt, plist in TARGET_PATTERNS.items():
            if any(p.lower() in low for p in plist):
                return tgt
        return None
    names["target"] = names["name"].map(classify)
    names = names.dropna(subset=["target"]).drop_duplicates(subset=["nsc"])

    # 3) eligible finite S' for those NSCs
    nsc_list = names["nsc"].astype(str).tolist()
    q_sp = """
      SELECT l.nsc, l.cell_line, l.s_prime
      FROM im_nci_nci60_doseresp_sprime_list l
      WHERE l.load_eligible AND l.s_prime IS NOT NULL
        AND l.s_prime > '-infinity'::float8 AND l.s_prime < 'infinity'::float8
        AND l.s_prime = l.s_prime
        AND l.nsc = ANY(%s)
    """
    with conn.cursor() as cur:
        cur.execute(q_sp, (nsc_list,))
        sp = pd.DataFrame(cur.fetchall(), columns=["nsc", "cell_line", "s_prime"])
    sp["s_prime"] = sp["s_prime"].astype(float)
    sp = sp.merge(names[["nsc", "target"]], on="nsc", how="inner")

    # 4) all NCI-60 lines with >=1 eligible finite S' fit (for true per-gene coverage)
    with conn.cursor() as cur:
        cur.execute("""SELECT DISTINCT cell_line FROM im_nci_nci60_doseresp_sprime_list
                       WHERE load_eligible AND s_prime IS NOT NULL
                         AND s_prime > '-infinity'::float8 AND s_prime < 'infinity'::float8
                         AND s_prime = s_prime""")
        fitted = {r[0] for r in cur.fetchall()}

    # 5) lung-only cohort: NCI-60 cell_names whose DepMap line is a lung line
    #    (matches the manuscript / RNAi-pillar cohort, ccle_name LIKE '%_LUNG')
    with conn.cursor() as cur:
        cur.execute("""SELECT DISTINCT b.cell_name
                       FROM im_cellosaurus_nci60_to_depmap_bridge b
                       JOIN im_sprime_solved_s_prime s
                         ON s.depmap_id = ANY(string_to_array(b.depmap_ach, '|'))
                       WHERE b.depmap_ach IS NOT NULL AND s.ccle_name LIKE '%_LUNG'""")
        lung_cellnames = {r[0] for r in cur.fetchall()}
    return geno, names, sp, fitted, lung_cellnames


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--nperm", type=int, default=20000)
    ap.add_argument("--nboot", type=int, default=5000)
    a = ap.parse_args(argv)
    figs = a.outdir / "figures"; tabs = a.outdir / "tables"
    figs.mkdir(parents=True, exist_ok=True); tabs.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260615)

    with psycopg.connect(**db_from_env()) as conn:
        geno, names, sp, fitted, lung_cellnames = load_data(conn)

    # per-line pooled S' within each target (mean over that target's compounds, per line)
    pooled_all = (sp.groupby(["target", "cell_line"])["s_prime"].mean()
                  .reset_index().rename(columns={"s_prime": "sp"}))
    pooled_all.to_csv(tabs / "r1_7_nci60_per_line.csv", index=False)

    def run_cohort(label, allowed, min_arm=3):
        """Compute coverage + pooled ΔS' for a cohort (allowed=None → pan-tissue; else lung-only).
        min_arm: minimum lines per arm to test a pair (3 = standard; 2 = relaxed 'rare-case' peek)."""
        gn = geno if allowed is None else geno[geno.cell_name.isin(allowed)]
        ft = fitted if allowed is None else (fitted & allowed)
        pl = pooled_all if allowed is None else pooled_all[pooled_all.cell_line.isin(allowed)]
        gby = {gid: gn[gn.gene_id == gid].set_index("cell_name")["mv"].to_dict() for gid in GENO_ID.values()}
        gcov_rows = []
        for gname, gid in GENO_ID.items():
            gg = gn[(gn.gene_id == gid) & (gn.cell_name.isin(ft))]
            gcov_rows.append(dict(gene=gname,
                                  mutant=int(gg.loc[gg.mv == "2", "cell_name"].nunique()),
                                  wild_type=int(gg.loc[gg.mv == "0", "cell_name"].nunique())))
        gcov = pd.DataFrame(gcov_rows).set_index("gene").reindex(["TP53", "PTEN", "RB1", "CDKN2A"])
        gcov.to_csv(tabs / f"r1_7_nci60_genotype_coverage_{label}.csv")
        rows, perline, cover = [], {}, []
        for gtype, target, role in PAIRS:
            gid = GENO_ID[gtype]
            sub = pl[pl.target == target].copy(); sub["mv"] = sub["cell_line"].map(gby[gid])
            mut = sub.loc[sub.mv == "2", "sp"].to_numpy(float)
            wt = sub.loc[sub.mv == "0", "sp"].to_numpy(float)
            cover.append(dict(genotype=gtype, target=target, role=role,
                              n_compounds=names[names.target == target].shape[0], n_mut=len(mut), n_wt=len(wt)))
            if len(mut) < min_arm or len(wt) < min_arm:
                continue
            delta = wt.mean() - mut.mean()
            p = perm_ranksum_p(mut, wt, a.nperm, rng)
            lo, hi = boot_ci(mut, wt, a.nboot, rng)
            match = (delta < 0) if role in EXPECT_NEG else (delta > 0)
            rows.append(dict(genotype=gtype, target=target, role=role, n_mut=len(mut), n_wt=len(wt),
                             sp_mut=round(float(mut.mean()), 3), sp_wt=round(float(wt.mean()), 3),
                             delta=round(float(delta), 3), ci_lo=round(float(lo), 3), ci_hi=round(float(hi), 3),
                             expected="mutant more sensitive" if role in EXPECT_NEG else "mutant resistant",
                             concordant=bool(match), p_perm=p))
            perline[(gtype, target)] = (mut, wt)
        pd.DataFrame(cover).to_csv(tabs / f"r1_7_nci60_coverage_{label}.csv", index=False)
        res = pd.DataFrame(rows)
        if not res.empty:
            res["q_bh"] = bh_fdr(res["p_perm"].to_numpy()); res["sig"] = res["q_bh"].map(stars)
            res = res.sort_values(["genotype", "role", "target"]).reset_index(drop=True)
        res.to_csv(tabs / f"r1_7_nci60_pooled_delta_{label}.csv", index=False)
        print(f"\n=== cohort={label} (admissible >=3/arm pairs: {len(res)}) ===")
        print(gcov.fillna(0).astype(int).to_string())
        if not res.empty:
            print(res.to_string(index=False))
        return res, perline, gcov, pd.DataFrame(cover)

    # PAN-TISSUE (powered supplement; min 3/arm) and LUNG-ONLY rare-case peek (relaxed min 2/arm)
    res, perline, gcov, cover_df = run_cohort("pan", None, min_arm=3)
    res_lung, perline_lung, gcov_lung, cover_lung = run_cohort("lung", lung_cellnames, min_arm=2)
    # canonical (pan) filenames retained for the docx builder inputs
    gcov.to_csv(tabs / "r1_7_nci60_genotype_coverage.csv")
    cover_df.to_csv(tabs / "r1_7_nci60_coverage.csv", index=False)
    if not res.empty:
        res.to_csv(tabs / "r1_7_nci60_pooled_delta.csv", index=False)

    # ---- LUNG-ONLY peek figure (n=2 rare case; explicitly NOT interpretable) ----
    lung_heads = [h for h in [("TP53", "MDM2"), ("TP53", "KIF11"), ("TP53", "CENPE")] if h in perline_lung]
    if lung_heads:
        figL, axes = plt.subplots(1, len(lung_heads), figsize=(3.0 * len(lung_heads), 4.0))
        if len(lung_heads) == 1:
            axes = [axes]
        for ax, (gt, tgt) in zip(axes, lung_heads):
            mut, wt = perline_lung[(gt, tgt)]
            for xi, (vals, col) in enumerate([(wt, "0.5"), (mut, "#2c7fb8")]):
                jj = (rng.random(len(vals)) - 0.5) * 0.18
                ax.scatter(np.full(len(vals), xi) + jj, vals, s=44, color=col, alpha=0.85, edgecolors="none")
                if len(vals):
                    ax.hlines(vals.mean(), xi - 0.2, xi + 0.2, color="black", lw=2)
            ax.set_xticks([0, 1]); ax.set_xticklabels([f"{gt}-WT (n={len(wt)})", f"{gt}-mut (n={len(mut)})"], fontsize=8)
            ax.set_title(tgt, fontsize=9)
            if ax is axes[0]:
                ax.set_ylabel("NCI-60 pooled S′ (↑ more sensitive)")
        figL.suptitle("LUNG-ONLY peek — n=2 mutant lines; NOT interpretable, shown only for transparency", fontsize=9)
        figL.tight_layout(); figL.savefig(figs / "fig_nci60_lung_beeswarm.png", dpi=150, bbox_inches="tight"); plt.close(figL)

    if res.empty:
        print("pan cohort: no admissible pairs"); return

    # ---- Figure 1: diverging ΔS' bars ----
    d = res.sort_values("delta")
    colors = ["#d7301f" if r == "NEG" else "#2c7fb8" for r in d["role"]]
    fig, ax = plt.subplots(figsize=(7.8, 4.8)); y = np.arange(len(d))
    ax.barh(y, d["delta"], xerr=[d["delta"]-d["ci_lo"], d["ci_hi"]-d["delta"]],
            color=colors, edgecolor="0.3", linewidth=0.4, error_kw=dict(ecolor="0.5", lw=0.8))
    ax.axvline(0, color="0.3", lw=1); ax.set_yticks(y)
    ax.set_yticklabels([f"{g} · {t}" for g, t in zip(d.genotype, d.target)], fontsize=8.5)
    for yi, (val, s, m) in enumerate(zip(d["delta"], d["sig"], d["concordant"])):
        ax.annotate((s if s != "ns" else "") + ("  ✓" if m else "  ✗"),
                    (val, yi), xytext=(6 if val >= 0 else -6, 0), textcoords="offset points",
                    va="center", ha="left" if val >= 0 else "right", fontsize=7.5, color="0.25")
    ax.set_xlabel("ΔS′  (wild-type − mutant)  ·  ← mutant MORE sensitive   |   mutant resistant →")
    ax.set_title("NCI-60 drug response vs S′ genotype calls\n(pooled ΔS′, pan-tissue)", fontsize=11)
    ax.scatter([], [], marker="s", color="#2c7fb8", label="S′ synthetic-lethal positive (expect ←)")
    ax.scatter([], [], marker="s", color="#d7301f", label="negative control (expect →)")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    fig.tight_layout(); fig.savefig(figs / "fig_nci60_diverging.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---- Figure 2: per-line beeswarm for headline pairs ----
    heads = [h for h in [("TP53", "MDM2"), ("TP53", "KIF11"), ("RB1", "CDK4/6")] if h in perline]
    if heads:
        fig, axes = plt.subplots(1, len(heads), figsize=(3.2 * len(heads), 4.2))
        if len(heads) == 1:
            axes = [axes]
        for ax, (gt, tgt) in zip(axes, heads):
            mut, wt = perline[(gt, tgt)]
            for xi, (vals, col) in enumerate([(wt, "0.5"), (mut, "#2c7fb8")]):
                j = (rng.random(len(vals)) - 0.5) * 0.28
                ax.scatter(np.full(len(vals), xi) + j, vals, s=26, color=col, alpha=0.8, edgecolors="none")
                ax.hlines(vals.mean(), xi - 0.2, xi + 0.2, color="black", lw=2)
            ax.set_xticks([0, 1]); ax.set_xticklabels([f"{gt}-WT", f"{gt}-mut"], fontsize=8)
            rr = res[(res.genotype == gt) & (res.target == tgt)].iloc[0]
            ax.set_title(f"{tgt}\nΔS′={rr.delta:+.2f}  {rr.sig}", fontsize=9)
            if ax is axes[0]:
                ax.set_ylabel("NCI-60 pooled S′ (↑ more sensitive)")
        fig.suptitle("Per-line pooled S′ by genotype (headline pairs)", fontsize=10)
        fig.tight_layout(); fig.savefig(figs / "fig_nci60_beeswarm.png", dpi=150); plt.close(fig)

    # ---- Figure 3: true per-gene genotype coverage (the audit) ----
    yy = np.arange(len(gcov))
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.barh(yy - 0.2, gcov["mutant"].fillna(0), 0.38, color="#2c7fb8", label="mutant")
    ax.barh(yy + 0.2, gcov["wild_type"].fillna(0), 0.38, color="0.6", label="wild-type")
    for i, (m, w) in enumerate(zip(gcov["mutant"].fillna(0), gcov["wild_type"].fillna(0))):
        ax.annotate(f"{int(m)}", (m, i - 0.2), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7.5)
        ax.annotate(f"{int(w)}", (w, i + 0.2), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7.5)
    ax.set_yticks(yy); ax.set_yticklabels(gcov.index)
    ax.axvline(3, color="#d7301f", ls="--", lw=1); ax.annotate("≥3/arm", (3.3, len(gcov) - 0.5), color="#d7301f", fontsize=8)
    ax.set_xlabel("NCI-60 lines with an eligible S′ fit and a genotype call")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.set_title("NCI-60 genotype coverage via the bridge (pan-tissue, any compound)", fontsize=10)
    fig.tight_layout(); fig.savefig(figs / "fig_nci60_coverage.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    print("\nwrote tables/{coverage,pooled_delta,per_line}.csv and figures/fig_nci60_{diverging,beeswarm,coverage}.png")


if __name__ == "__main__":
    main()
