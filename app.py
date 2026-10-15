"""Health Correlation Explorer — M9 exercise.

Explores correlations between health measures in nhanes_health.csv.
Every view (table, scatter, r, n, heatmap) is computed from the same
filtered DataFrame, so the sidebar filters affect everything.
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

DATA_PATH = "nhanes_health.csv"

# Health thresholds for optional scatter-plot coloring: label -> (column, cutoff)
THRESHOLDS = {
    "High systolic BP (SBP ≥ 130)": ("systolic_bp", 130),
    "High diastolic BP (DBP ≥ 80)": ("diastolic_bp", 80),
    "Obesity (BMI ≥ 30)": ("bmi", 30),
    "Diabetes (HbA1c ≥ 6.5)": ("hba1c", 6.5),
    "High cholesterol (total ≥ 240)": ("total_chol", 240),
}


@st.cache_data
def load_data(path):
    return pd.read_csv(path)


def pair_corr(data, x, y, method):
    """Return (r, n) for x vs y, dropping missing values pairwise."""
    mask = data[x].notna() & data[y].notna()
    n = int(mask.sum())
    if n < 3:
        return float("nan"), n
    r = data.loc[mask, x].corr(data.loc[mask, y], method=method)
    return r, n


def fmt_r(r):
    return "—" if pd.isna(r) else f"{r:.3f}"


st.set_page_config(page_title="Health Correlation Explorer", layout="wide")

df = load_data(DATA_PATH)
# Numeric columns only — `sex` is text, so it can never enter a correlation.
NUMERIC_COLS = df.select_dtypes("number").columns.tolist()

# ---------------------------------------------------------------- Sidebar
st.sidebar.header("Filters")
sex = st.sidebar.radio("Sex", ["All", "Female", "Male"])
age_min, age_max = int(df["age"].min()), int(df["age"].max())
age_lo, age_hi = st.sidebar.slider(
    "Age range (80 = 80 or older)", age_min, age_max, (age_min, age_max)
)
st.sidebar.header("Correlation method")
method_label = st.sidebar.radio("Method", ["Pearson", "Spearman"])
method = method_label.lower()

mask = df["age"].between(age_lo, age_hi)
if sex != "All":
    mask &= df["sex"] == sex
filtered = df[mask]

st.sidebar.markdown(f"**n = {len(filtered):,} participants** after filters")

# ---------------------------------------------------------------- 1. Data preview
st.title("Health Correlation Explorer")
st.markdown(
    """
**Data:** 4,433 adults aged 20+ from the CDC's 2017–2018 National Health and
Nutrition Examination Survey (NHANES). Each row is one participant. Measures
include body size (`bmi`, `waist_cm`), blood pressure (`systolic_bp`,
`diastolic_bp`), blood sugar (`hba1c`), cholesterol (`total_chol`, `hdl_chol`),
and self-reported `sleep_hours` and `sedentary_minutes`. Age is top-coded at 80.

NHANES oversamples some groups, so these correlations describe *this sample*,
not the US population.
"""
)

if len(filtered) < 3:
    st.warning("Fewer than 3 participants match these filters. Widen the filters.")
    st.stop()

st.subheader("Data preview")
st.caption(f"Showing {len(filtered):,} filtered rows (sex: {sex}, age {age_lo}–{age_hi}).")
st.dataframe(filtered, hide_index=True)

# ---------------------------------------------------------------- 2. Pairwise view
st.subheader(f"Pairwise view ({method_label})")
c1, c2 = st.columns(2)
x = c1.selectbox("X variable", NUMERIC_COLS, index=NUMERIC_COLS.index("age"))
y = c2.selectbox("Y variable", NUMERIC_COLS, index=NUMERIC_COLS.index("systolic_bp"))

if x == y:
    st.warning("Pick two different variables.")
else:
    r, n = pair_corr(filtered, x, y, method)
    m1, m2 = st.columns(2)
    m1.metric(f"{method_label} r", fmt_r(r))
    m2.metric("n (participants)", f"{n:,}")

    color_on = st.checkbox("Color points by a health threshold")
    plot_df = filtered[[x, y]].dropna()

    fig, ax = plt.subplots(figsize=(8, 5))
    if color_on:
        label = st.selectbox("Threshold", list(THRESHOLDS))
        col, cutoff = THRESHOLDS[label]
        flag = filtered.loc[plot_df.index, col]
        plot_df = plot_df.assign(
            Group=flag.ge(cutoff).map({True: f"{col} ≥ {cutoff}", False: f"{col} < {cutoff}"})
            .where(flag.notna(), "missing")
        )
        sns.scatterplot(data=plot_df, x=x, y=y, hue="Group", alpha=0.4, s=15, ax=ax)
        sns.regplot(data=plot_df, x=x, y=y, scatter=False, color="black", ax=ax)
    else:
        sns.regplot(
            data=plot_df, x=x, y=y, ax=ax,
            scatter_kws={"alpha": 0.3, "s": 12}, line_kws={"color": "crimson"},
        )
    ax.set_title(f"{y} vs {x}   ({method_label} r = {fmt_r(r)}, n = {n:,})")
    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        "Trend line is a linear (least-squares) fit and is shown for both methods. "
        "Threshold coloring is visual only; r uses all plotted points. "
        "An r near 0 does not mean no relationship. A U-shaped pattern "
        "(like sleep hours) can have r ≈ 0."
    )

# ---------------------------------------------------------------- 3. Heatmap
st.subheader(f"Correlation heatmap ({method_label})")
cols = st.multiselect("Variables to include", NUMERIC_COLS, default=NUMERIC_COLS)

if len(cols) < 2:
    st.info("Select at least two variables.")
else:
    # pandas .corr drops missing values pairwise by default
    corr = filtered[cols].corr(method=method)
    present = filtered[cols].notna().astype(int)
    n_matrix = present.T @ present  # pairwise complete-case counts

    same_n = n_matrix.to_numpy().min() == n_matrix.to_numpy().max()
    if same_n:
        annot, fmt = True, ".2f"
    else:
        annot = corr.round(2).astype(str) + "\nn=" + n_matrix.astype(str)
        fmt = ""

    size = max(6, 0.8 * len(cols))
    fig, ax = plt.subplots(figsize=(size + 1, size))
    sns.heatmap(
        corr, vmin=-1, vmax=1, center=0, cmap="RdBu_r",
        annot=annot, fmt=fmt, square=True, linewidths=0.5,
        cbar_kws={"label": f"{method_label} r"}, ax=ax,
    )
    st.pyplot(fig)
    plt.close(fig)

    if same_n:
        st.caption(f"Every square uses n = {int(n_matrix.iloc[0, 0]):,} participants (no missing values in this selection).")
    else:
        st.caption("Each square shows r and its pairwise n (missing values dropped per pair).")
    st.caption("Color scale is fixed from −1 to 1 so colors are comparable across filters.")
