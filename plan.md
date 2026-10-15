# Plan: Health Correlation Explorer (`app.py`)

## Context
M9 assignment: a single-file Streamlit app that explores correlations in `nhanes_health.csv` and covers five required features: a data preview, a pairwise view, a heatmap, sex and age filters, and a Pearson/Spearman toggle. The user checks every r and n against pandas, so the numbers have to come from the **filtered** data and match `Series.corr` exactly. Allowed packages: streamlit, pandas, seaborn, and scipy if needed. Nothing else without asking.

### What the data showed (checked, not assumed)
- 4,433 rows, 11 columns: `age, sex, bmi, waist_cm, systolic_bp, diastolic_bp, hba1c, total_chol, hdl_chol, sleep_hours, sedentary_minutes`.
- `sex` is the only text column (`Female` 2,263 / `Male` 2,170).
- **There are no blank or non-numeric cells right now.** Pairwise NaN handling is still built in, but in this file n = number of filtered rows for every pair.
- `age` runs from 20 to 80, and 80 is top-coded ("80 or older").

## Design: one filtered DataFrame feeds everything
```
load_data() [st.cache_data] ──► df (raw)
sidebar: sex, age range, method ──► filtered = df[sex mask & age.between(lo, hi)]
                                       │
     ┌───────────────┬─────────────────┼──────────────────┐
  Data preview    Pairwise view     Heatmap         (all use the same `method`)
  (filtered rows) r, n from         pairwise r and n
                  filtered[[x,y]]   from filtered[cols]
```
- `NUMERIC_COLS` is built with `select_dtypes("number")`, so `sex` is excluded by construction. Every dropdown and multiselect draws its options from that list only.
- The script reruns from top to bottom on every widget change. All three views read `filtered` and `method`, and none reads `df`, so no view can go stale.

## Build order (test each step before moving to the next)
1. **Load + numeric columns**: `load_data()` reads the relative path `nhanes_health.csv` and is cached. Define `NUMERIC_COLS`. Add the title and a short description of the dataset, using the data dictionary, the note that age 80 means 80+, and the caveat that NHANES oversamples some groups.
2. **Sidebar filters + method**:
   - Sex radio: All / Female / Male.
   - Age range slider: 20–80, default is the full range.
   - Method radio: Pearson / Spearman.
   - Build `filtered`. Show "n = X participants after filters". If fewer than 3 rows remain, show a warning and `st.stop()`.
3. **Data preview**: `st.dataframe(filtered)` plus a row count.
4. **Correlation helper**: `pair_corr(data, x, y, method)` drops NaNs on just those two columns, then returns `(r, n)` using pandas `.corr(method=...)` so it matches the verification code exactly. If n < 3 or either column is constant, it returns NaN.
5. **Pairwise view**:
   - X and Y selectboxes (defaults `age` / `systolic_bp`). Warn if X equals Y.
   - Show r and n as `st.metric`s, labelled with the method.
   - Scatter: seaborn `regplot` (linear trend line, semi-transparent points) on the pairwise-dropped data, rendered with `st.pyplot`.
   - An optional "Color by health threshold" checkbox and a threshold choice:
     - SBP ≥ 130
     - DBP ≥ 80
     - BMI ≥ 30
     - HbA1c ≥ 6.5
     - Total cholesterol ≥ 240
   - When the option is on, use `scatterplot(hue=...)` with an overall `regplot` line on top. The coloring is visual only. r is still computed on all points.
   - Caption: "r near 0 ≠ no relationship (e.g. U-shaped sleep)".
6. **Heatmap**:
   - A multiselect of `NUMERIC_COLS` (default all, at least 2 required).
   - Pairwise matrix: `filtered[cols].corr(method=method)` gives r, because pandas drops NaNs pairwise by default. The n matrix comes from `notna().T @ notna()`.
   - `sns.heatmap(vmin=-1, vmax=1, center=0, cmap="RdBu_r", annot=...)`. Each cell is annotated as `"r\nn=…"`.
   - When n is the same everywhere (as in the current data), annotate r only and show the single n in a caption. This keeps cells readable at 10×10.
7. **requirements.txt** and the run check (Part 5 of the assignment). Created only after you approve this plan.

## Packages
`streamlit`, `pandas`, `seaborn`. **Note:** rendering seaborn plots in Streamlit needs `import matplotlib.pyplot as plt` (for `st.pyplot` and figure handling). matplotlib ships as a seaborn dependency, but `app.py` would import it directly and `requirements.txt` should list it. **I need your OK on that.** scipy is not needed, because pandas computes both Pearson and Spearman.

## Run command
```bash
uv run --with streamlit,pandas,seaborn,scipy streamlit run app.py
```
`uv` is installed. Your system python3 has none of these packages, so use the uv command above.

## Open questions / unclear points
1. **matplotlib import**: is it OK, as described above? The alternative is plotly, which the assignment allows but is a new package.
2. **Trend line under Spearman**: a linear OLS line doesn't represent a rank correlation. Options:
   - keep the linear line for both methods and add a caption (recommended, simplest)
   - switch to a LOWESS line, which needs statsmodels, a new package
   - use binned means, which needs only pandas
3. **n in the heatmap**: is it OK to show one n caption when all cells share the same n, and print n per cell only when the cells differ?
4. **Sex filter widget**: is a radio with All / Female / Male OK, or do you prefer a multiselect?
5. **Thresholds**: is the list above OK? Low HDL is sex-specific (<40 M, <50 F), so it is left out unless you want it.
6. **Files**: `plan.md`, `prompts.md` and `verification.md` exist but are empty. I assume you will fill them yourself, and I won't touch them.

## Verification
- Run the app with the uv command and click through every widget.
- In a separate uv Python session (`uv run --with pandas python`), reproduce the assignment's checks:
  - `age`/`systolic_bp`, `bmi`/`waist_cm` and `waist_cm`/`hdl_chol` on all rows
  - Female only and Male only
- Confirm that the app's r and n match. With Female selected, confirm that the heatmap cell for age/SBP equals the pairwise r.
- Switch to Spearman and confirm the values match `.corr(method="spearman")`.
- Confirm that `sex` never appears in any dropdown or on the heatmap axes.
