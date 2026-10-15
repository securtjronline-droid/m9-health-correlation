# Verification — M9 Health Correlation Explorer

App values were read from the running app (Pearson, age 20–80). pandas values come from:

```python
import pandas as pd
df = pd.read_csv("nhanes_health.csv")
df["age"].corr(df["systolic_bp"]), len(df)                     # checks 1–3: swap columns
f = df[df["sex"] == "Female"]; f["age"].corr(f["systolic_bp"]), len(f)   # check 4
m = df[df["sex"] == "Male"];   m["age"].corr(m["systolic_bp"]), len(m)   # check 5
```

| # | Check | App shows | pandas gives | Match? |
|---|---|---|---|---|
| 1 | r for `age` vs `systolic_bp`, all participants | r = 0.463, n = 4,433 | 0.463, 4,433 | Yes |
| 2 | r for `bmi` vs `waist_cm`, all participants | r = 0.903, n = 4,433 | 0.903, 4,433 | Yes |
| 3 | r for `waist_cm` vs `hdl_chol`, all participants | r = −0.335, n = 4,433 | −0.335, 4,433 | Yes |
| 4 | r and n for `age` vs `systolic_bp`, **Female only** | r = 0.555, n = 2,263 | 0.555, 2,263 | Yes |
| 5 | r and n for `age` vs `systolic_bp`, **Male only** | r = 0.351, n = 2,170 | 0.351, 2,170 | Yes |
| 6 | With the filter set to Female, does the heatmap's `age`/`systolic_bp` square match row 4? | 0.56 (heatmap shows 2 decimals) | 0.555 | Yes |

Extra check: Spearman, Female, `age` vs `systolic_bp` — app 0.582, `f["age"].corr(f["systolic_bp"], method="spearman")` 0.582. Match.

## The M9 trap: r near zero ≠ no relationship

`sleep_hours` vs `systolic_bp` (all participants): Pearson r = 0.007, which looks like "no relationship".
But mean systolic BP by sleep hours is U-shaped:

| Sleep (h, rounded; ≤4 and ≥10 grouped) | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|
| Mean SBP (mmHg) | 126.8 | 131.0 | 126.5 | 125.7 | 125.7 | 127.4 | 128.4 |

Short and long sleepers both have higher BP than 7–8 hour sleepers. The ups and downs cancel out, so r stays near 0.
Correlation only measures *linear* (Pearson) or *monotonic* (Spearman) association.

## Code check

Reviewed `app.py` for these points:
- **`sex` is never correlated:** `NUMERIC_COLS = df.select_dtypes("number")`. All dropdowns and the heatmap multiselect use only this list.
- **Filters feed every view:** `filtered` is built once from the sex and age controls. The table, scatter plot, r, n and heatmap all read `filtered`, never `df`.
- **Missing values handled pairwise:** `pair_corr` drops rows only where x or y is missing. The heatmap uses `DataFrame.corr` (pairwise by default), with n per pair taken from `notna().T @ notna()`. Note: this CSV has no missing values, so n equals the filtered row count.
- **n next to every r:** the pairwise view shows n as a metric and in the plot title. The heatmap shows n in a caption, or in each cell if n ever differs between pairs.
- **Honest heatmap:** `sns.heatmap(vmin=-1, vmax=1, center=0, cmap="RdBu_r")`.
- **Method toggle:** one `method` variable is passed to both the pairwise `.corr` and the heatmap `.corr`.
- **CSV path:** loaded with the relative path `nhanes_health.csv`.
