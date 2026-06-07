# Lung-cancer drug DBSCAN clustering (exploratory)

> **Status: exploratory first attempt — not a validated result.**
> The clustering as built is **dominated by MOA, not by drug response** (see
> [Findings](#findings)). Keep this as a record of *what was tried and why it
> didn't pan out*, not as something downstream should depend on.

## Intention

An unsupervised attempt to find groups of lung-cancer drugs that share **both** a
response profile and a mechanism of action:

- Source: `fnl_sprime_pooled_delta_sprime`, `tissue = 'LUNG'`, aggregated to
  **drug + MOA** combinations (~1,405 rows), with `avg_delta_s_prime` per combo.
- Features: `[avg_delta_s_prime]` + **one-hot encoded MOA (~521 categories)**,
  standardized, then DBSCAN.
- `eps` chosen via a k-distance elbow (landed on `eps = 4.0`); `min_samples`
  swept over 2 / 5 / 10 / 20 / 100; clusters visualized via PCA → 2D.

## Files

| File | Role |
|------|------|
| `lung_dbscan_eps_analysis.py` | k-distance elbow to pick `eps`. |
| `lung_dbscan_labeled_output.py` | Runs DBSCAN, labels the data, writes the CSV + legend plot. |
| `drug_clustering_by_moa_reference.py` | Reference / earlier clustering exploration. |
| `reference_ipython_clusteringalgos.txt` | Reference snippets. |
| `DBSCAN_EPS_ANALYSIS_DOCUMENTATION.md` | Detailed eps methodology (note: contains unfilled `~X.X` placeholders). |
| `lung_dbscan_*.png`, `lung_dbscan_labeled_results.csv` | Generated run outputs (reproducible from the scripts). |

## Findings

- **Feature design swamps the signal.** One numeric response column vs ~521
  one-hot MOA columns, all scaled to equal variance, makes distance ~521:1
  dominated by MOA. So clusters mostly re-derive "same MOA" groupings; ΔS′
  barely affects membership.
- **Results reflect that.** At `min_samples=10`, ~70% of rows (987/1,405) are
  noise, and the ~22 clusters track MOA (e.g. adrenergic-receptor-agonist drugs
  group together regardless of response magnitude).
- **High-dim sparse space is unreliable for DBSCAN.** Distance concentration in
  ~522 dimensions is why the noise fraction is large and why `min_samples` had
  to be swept to hunt for structure.
- **Not validated.** Silhouette / biological-purity checks were left as "next
  steps"; the eps doc still has placeholder statistics.

## If revisited

- Weight or drop MOA so the response metric isn't drowned out, or cluster on a
  richer response vector (per-gene ΔS′) instead of a single average.
- Consider methods better suited to mixed numeric/high-cardinality-categorical
  data, and validate with silhouette + biological sanity checks.
