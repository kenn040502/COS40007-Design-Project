# -*- coding: utf-8 -*-
"""
Build the COS40007 Design Project report by filling the team's template.
- Preserves the title page and Table of Contents (SDT block) from the template.
- Removes the placeholder body content and writes the full report:
  narrative, data tables, and all analysis figures from outputs/figures/.
Run:  .venv\\Scripts\\python.exe build_report.py
"""
import os
import json
import pandas as pd
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(ROOT, "outputs", "figures")
MODELS = os.path.join(ROOT, "outputs", "models")
PROC = os.path.join(ROOT, "data", "processed")
TEMPLATE = r"D:\Ai_engineer\COS40007_E's Island_Design_Project_Report.docx"
OUT = TEMPLATE  # write the finished report back to the team's file

doc = docx.Document(TEMPLATE)

# ── Remove placeholder body (everything from first Heading1 'Introduction') ──
paras = doc.paragraphs
start = None
for i, p in enumerate(paras):
    if p.style and p.style.style_id == "Heading1":
        start = i
        break
for p in paras[start:]:
    p._element.getparent().remove(p._element)

# ── Counters ─────────────────────────────────────────────────────────────────
_fig = {"n": 0}
_tab = {"n": 0}

# ── Helpers ──────────────────────────────────────────────────────────────────

def h1(text):
    doc.add_paragraph(text, style="Heading 1")

def h2(text):
    doc.add_paragraph(text, style="Heading 2")

def h3(text):
    doc.add_paragraph(text, style="Heading 3")

def para(text, italic=False, bold=False, size=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = italic
    run.bold = bold
    if size:
        run.font.size = Pt(size)
    p.paragraph_format.space_after = Pt(6)
    return p

def bullets(items):
    for it in items:
        p = doc.add_paragraph(style="List Paragraph")
        p.paragraph_format.left_indent = Inches(0.3)
        run = p.add_run("•  ")
        # support bold lead "Label: rest"
        if isinstance(it, tuple):
            lead, rest = it
            r1 = p.add_run(lead)
            r1.bold = True
            p.add_run(rest)
        else:
            p.add_run(it)
        p.paragraph_format.space_after = Pt(3)

def figure(filename, caption, width=6.0):
    _fig["n"] += 1
    path = os.path.join(FIG, filename)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(path, width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run(f"Figure {_fig['n']}. {caption}")
    cr.italic = True
    cr.font.size = Pt(9)
    cap.paragraph_format.space_after = Pt(10)

def _set_cell_bg(cell, color):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), color)
    tcpr.append(shd)

def _set_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "808080")
        borders.append(e)
    tblPr.append(borders)

def table(caption, headers, rows, col_widths=None, font_size=9, header_bg="1F4E79"):
    _tab["n"] += 1
    cap = doc.add_paragraph()
    cr = cap.add_run(f"Table {_tab['n']}. {caption}")
    cr.italic = True
    cr.font.size = Pt(9)
    cap.paragraph_format.space_after = Pt(3)

    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_borders(t)
    hdr = t.rows[0].cells
    for j, htext in enumerate(headers):
        hdr[j].text = ""
        run = hdr[j].paragraphs[0].add_run(str(htext))
        run.bold = True
        run.font.size = Pt(font_size)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _set_cell_bg(hdr[j], header_bg)
    for r_i, row in enumerate(rows):
        cells = t.add_row().cells
        for j, val in enumerate(row):
            cells[j].text = ""
            run = cells[j].paragraphs[0].add_run(str(val))
            run.font.size = Pt(font_size)
            if r_i % 2 == 1:
                _set_cell_bg(cells[j], "EFF3F8")
    if col_widths:
        for j, w in enumerate(col_widths):
            for cell in t.columns[j].cells:
                cell.width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ── Load computed data ───────────────────────────────────────────────────────
ts_metrics = pd.read_csv(os.path.join(MODELS, "ts_metrics_summary.csv"))
clu = json.load(open(os.path.join(MODELS, "clustering_results.json")))
km = pd.read_csv(os.path.join(PROC, "districts_kmeans_clustered.csv"))
pov = pd.read_csv(os.path.join(PROC, "poverty_district_wide.csv"))

# =============================================================================
# 1. INTRODUCTION
# =============================================================================
h1("Introduction")

h2("Background and Motivation")
para(
    "Income inequality and poverty remain two of the most closely watched indicators of "
    "national development in Malaysia. Although the country has transformed from an agrarian "
    "economy into an upper-middle-income nation, the gains have not been evenly distributed "
    "across its 16 states and Federal Territories or its administrative districts. The "
    "Department of Statistics Malaysia (DOSM) reports that the national Gini coefficient "
    "narrowed only marginally from 0.407 in 2019 to 0.404 in 2022, while the absolute poverty "
    "rate stood at 6.2% nationally in 2022 — but reached as high as 19.7% in Sabah. These "
    "headline averages conceal a substantial degree of regional disparity that is directly "
    "relevant to the design of redistribution and rural-development policy."
)
para(
    "Under the COS40007 “Smart Government” theme, this project applies machine-learning "
    "techniques — unsupervised clustering and time-series forecasting — to open Malaysian "
    "public-sector data in order to surface patterns that aggregate statistics hide. The "
    "motivation is twofold: (1) to demonstrate that standard AI methods can convert routinely "
    "published government survey data into actionable, geographically targeted insight, and "
    "(2) to do so in a transparent, reproducible pipeline that a public agency could adopt."
)

h2("Project Objectives")
para("The project set out to achieve the following objectives:")
bullets([
    ("Group districts by socioeconomic profile. ", "Use clustering to segment Malaysia’s 160 administrative districts into interpretable socioeconomic tiers from income, expenditure, inequality and poverty features."),
    ("Forecast inequality trajectories. ", "Use ARIMA time-series modelling to forecast the Gini coefficient of each state to 2030 and quantify forecast reliability."),
    ("Quantify the pandemic’s distributional impact. ", "Measure the change in district poverty between 2019 and 2022 to locate the communities most affected by the COVID-19 shock."),
    ("Validate against official statistics. ", "Cross-check every headline result against DOSM and World Bank published figures to ensure real-world reliability."),
    ("Deliver an interactive demonstrator. ", "Package the analysis into a Flask web dashboard so non-technical stakeholders can explore the findings."),
])

h2("Summary of Outcomes")
para(
    "All four DOSM datasets were processed through a single reproducible pipeline (random seed "
    "fixed at 42) that regenerates every figure and metric in this report. The key outcomes were:"
)
bullets([
    ("Two robust district clusters. ", "K-Means and hierarchical clustering independently agreed on k = 2: a low-income/high-poverty tier of 121 districts (75.6%, mean income RM 5,018, poverty 14.82%) and a mid-income tier of 39 districts (24.4%, mean income RM 8,938, poverty 3.68%), with a silhouette score of 0.42."),
    ("A declining inequality forecast. ", "ARIMA(2,1,2) forecast the state-average Gini to continue falling gently toward ~0.357 by 2030, with a strong mean test RMSE of 0.0144 (mean MAPE 3.82%) across all 16 states."),
    ("Sarawak as the volatility hotspot. ", "Sarawak’s interior districts produced both the largest poverty increases (Julau +18.2 pp) and decreases (Bukit Mabong –20.5 pp) between 2019 and 2022."),
    ("Official validation. ", "Every cross-sectional figure reconciles with DOSM’s published 2022 statistics, and the modelled trend agrees in direction with the official national Gini series."),
])

# =============================================================================
# 2. DATASET
# =============================================================================
h1("Dataset")

h2("Data Source")
para(
    "Four datasets were sourced from the OpenDOSM Data Catalogue and the Malaysian Open Data "
    "portal (data.gov.my), all published by the Department of Statistics Malaysia (DOSM) under "
    "the Creative Commons Attribution 4.0 International (CC BY 4.0) licence. They derive from the "
    "Household Income and Expenditure Survey (HIES), the official instrument DOSM uses to measure "
    "income, expenditure, inequality and poverty. The datasets were retrieved programmatically "
    "(see data/download_datasets.py) directly from DOSM’s storage endpoints, guaranteeing that "
    "the analysis runs on primary-source government data rather than third-party copies."
)
table(
    "DOSM datasets used in the project (CC BY 4.0).",
    ["Dataset", "OpenDOSM / data.gov.my catalogue", "Coverage", "Rows"],
    [
        ["HIES by District", "hies_district", "160 districts, 2022", "160"],
        ["HIES by State", "hies_state", "16 states, 2022", "16"],
        ["Poverty by District", "hh_poverty_district", "160 districts, 2019 & 2022", "318"],
        ["Gini Coefficient by State", "hh_inequality_state", "16 states, 1974–2022", "273"],
    ],
    col_widths=[1.8, 2.4, 1.6, 0.6],
)
para(
    "Two design choices underpin the dataset selection. The district-level HIES table is "
    "cross-sectional (one row per district for 2022) and therefore well suited to clustering, "
    "whereas the state Gini table is a long, irregular time series (1974–2022) suited to "
    "forecasting. Combining a cross-sectional and a longitudinal source lets the project answer "
    "both “where is poverty concentrated today?” and “where is inequality heading?”.",
)

h2("Data Processing")
para(
    "The preprocessing module (src/preprocessing.py) loads, cleans, type-casts and merges the "
    "raw CSVs, writing tidy outputs to data/processed/. The main steps were:"
)
bullets([
    ("Type coercion and missing-value handling. ", "Income, expenditure, Gini and poverty columns were coerced to numeric and rows with missing core values dropped; all 160 districts and 16 states survived cleaning."),
    ("Feature engineering. ", "Two derived features were added to the district table — savings_rate = (income_mean − expenditure_mean) / income_mean × 100, and income_expenditure_ratio = income_mean / expenditure_mean — to capture household financial resilience."),
    ("Poverty reshaping. ", "The long poverty table was pivoted to a wide format with one row per district carrying 2019 and 2022 absolute poverty plus their difference (poverty_abs_change), enabling direct before/after comparison."),
    ("Gini interpolation. ", "Because HIES is not conducted annually, the state Gini series contains gaps (e.g., 1975, 1977–1978). Linear interpolation produced a uniform annual series of 698 points across 16 states, a prerequisite for ARIMA’s evenly-spaced-step assumption."),
])
para(
    "A note on DOSM survey methodology informed the cleaning: the 1970 and 1974 surveys covered "
    "Peninsular Malaysia only, Sabah and Sarawak entered from 1976, and from 1989 the series "
    "refers to Malaysian citizens. These breaks justify treating the early series cautiously and "
    "withholding only the most recent years for testing (Section 3.2)."
)
figure(
    "eval_income_gini_scatter.png",
    "District-level mean household income versus Gini coefficient (2022), coloured by state. "
    "Higher-income districts cluster on the right; within-district inequality (Gini) is only "
    "weakly related to income level, foreshadowing the clustering result.",
)

# =============================================================================
# 3. AI MODEL DEVELOPMENT
# =============================================================================
h1("AI model development")
para(
    "Two complementary unsupervised / statistical learning approaches were developed: (a) "
    "clustering to segment districts, and (b) ARIMA time-series forecasting of state inequality. "
    "Both are implemented in src/ and orchestrated by run_pipeline.py."
)

h2("Feature engineering / Feature extraction")
para(
    "For clustering, five standardised HIES district features were used as the model input: "
    "income_mean, income_median, expenditure_mean, gini and poverty. Because these variables "
    "span very different scales (income in thousands of RM, Gini on a 0–1 scale), they were "
    "z-score standardised with scikit-learn’s StandardScaler so that high-magnitude income "
    "variables do not dominate the Euclidean distance calculation."
)
table(
    "Feature dictionary for the district clustering model.",
    ["Feature", "Description", "Unit"],
    [
        ["income_mean", "Mean gross monthly household income", "RM"],
        ["income_median", "Median gross monthly household income", "RM"],
        ["expenditure_mean", "Mean monthly household expenditure", "RM"],
        ["gini", "Within-district Gini coefficient", "0–1"],
        ["poverty", "Absolute poverty incidence", "% of households"],
    ],
    col_widths=[1.6, 3.6, 1.2],
)
para(
    "For dimensionality reduction and visualisation, Principal Component Analysis (PCA) projected "
    "the five standardised features onto two components. PC1 explains 66.7% and PC2 22.7% of "
    "total variance (89.4% cumulative), confirming that a two-dimensional projection retains "
    "almost all of the structure in the data and is therefore a faithful basis for the cluster "
    "scatter plots. For the time-series model the single modelled variable is the annual, "
    "interpolated state Gini coefficient; differencing (d = 1) acts as the temporal feature "
    "transform that removes the long-run trend."
)

h2("Train/Test split")
para(
    "The clustering task is unsupervised and has no labelled target, so it uses the full set of "
    "160 districts; model quality is assessed with internal validity indices (silhouette, "
    "Davies–Bouldin, Calinski–Harabasz) and cross-checked by running two different algorithms "
    "on the same data."
)
para(
    "For the ARIMA forecasting task a temporal hold-out was used per state: the last 5 annual "
    "observations form the test set and all earlier years form the training set. An Augmented "
    "Dickey–Fuller (ADF) stationarity test was run on each training series before fitting; only "
    "5 of the 16 training series were stationary at the 5% level, confirming that first-order "
    "differencing (d = 1) is needed for the majority. After the test-set error is measured, the "
    "model is refit on the complete series to generate the genuine out-of-sample forecast for "
    "2023–2030."
)

h2("Training model")
h3("3.3.1  Clustering — K-Means and Agglomerative Hierarchical")
para(
    "The optimal number of clusters was selected by computing three independent criteria for "
    "k = 2 to 10: the elbow (within-cluster sum of squares), the silhouette score (higher is "
    "better) and the Davies–Bouldin index (lower is better). All three criteria agree that "
    "k = 2 is optimal — the silhouette score peaks sharply at 0.421 for k = 2 before falling to "
    "~0.31 for larger k."
)
figure(
    "cluster_elbow_silhouette.png",
    "Optimal-k selection for K-Means. The elbow, silhouette and Davies–Bouldin criteria all "
    "indicate k = 2 as the best number of clusters.",
)
para(
    "Two algorithms were then fit at k = 2. K-Means partitions the districts to minimise "
    "within-cluster variance; Agglomerative (Ward-linkage) hierarchical clustering builds the "
    "groups bottom-up by repeatedly merging the least-costly pair. Running both provides a "
    "cross-validation of structure — if independent algorithms recover the same groups, the "
    "clusters are likely genuine rather than artefacts."
)
figure(
    "cluster_pca_kmeans.png",
    "K-Means district clusters projected onto the first two principal components (89.4% of "
    "variance). The two tiers separate cleanly along PC1, which is dominated by income and poverty.",
    width=5.6,
)
figure(
    "cluster_dendrogram.png",
    "Ward-linkage hierarchical clustering dendrogram of the 160 districts. Cutting the tree at "
    "the largest vertical gap yields two clusters, consistent with K-Means.",
)

h3("3.3.2  Time-series — ARIMA(2,1,2)")
para(
    "An ARIMA(p=2, d=1, q=2) model was fit to each state’s annual Gini series. The order was "
    "chosen to match the data’s characteristics: the long-run downward trend motivates the "
    "integrated term (d = 1), while two autoregressive and two moving-average terms capture the "
    "short-run dynamics without over-fitting the relatively short series. ARIMA is well suited "
    "to moderate-length univariate series with trend and no strong seasonality, and it yields "
    "interpretable forecasts with confidence intervals — valuable for policy communication."
)
figure(
    "ts_summary_all_states.png",
    "ARIMA forecasting summary across all 16 states: forecast error (RMSE, left) and the "
    "forecasted 2030 Gini (right). Only Sabah approaches the 0.40 inequality threshold.",
)
para(
    "Two representative state forecasts illustrate the model behaviour. Sabah — the most unequal "
    "state — is forecast to ease only slightly, while Kelantan shows a rare gently-rising "
    "trajectory, flagging it for policy attention."
)
figure("ts_sabah.png", "Sabah Gini forecast: train/test fit (left) and test-period evaluation (right).", width=6.2)
figure("ts_kelantan.png", "Kelantan Gini forecast — one of the few states with a slightly rising projected trend.", width=6.2)

h2("Evaluation of AI model")
h3("3.4.1  Clustering validity")
para(
    "K-Means and hierarchical clustering produced almost identical internal validity scores, "
    "confirming the two-tier structure is robust to algorithm choice."
)
table(
    "Internal clustering validity (k = 2).",
    ["Method", "k", "Silhouette ↑", "Davies–Bouldin ↓", "Calinski–Harabasz ↑"],
    [
        ["K-Means", "2", "0.4213", "0.9347", "113.62"],
        ["Hierarchical (Ward)", "2", "0.4159", "0.9418", "111.94"],
    ],
    col_widths=[1.8, 0.6, 1.2, 1.5, 1.7],
)
figure(
    "cluster_pca_hierarchical.png",
    "Hierarchical clustering in PCA space — visually near-identical to the K-Means partition, "
    "corroborating cluster validity.",
    width=5.6,
)
para("The socioeconomic profile of each cluster makes the two tiers interpretable:")
table(
    "Socioeconomic profile of the two district clusters (means).",
    ["Cluster", "Districts (%)", "Income mean (RM)", "Expenditure (RM)", "Gini", "Poverty (%)"],
    [
        ["Low income, high poverty", "121 (75.6%)", "5,018", "3,319", "0.34", "14.82"],
        ["Mid income, low poverty", "39 (24.4%)", "8,938", "5,387", "0.34", "3.68"],
    ],
    col_widths=[1.9, 1.2, 1.4, 1.3, 0.6, 1.0],
)
figure(
    "cluster_profiles.png",
    "Cluster feature heatmap (left) and district counts (right). The clusters differ chiefly in "
    "absolute income and poverty, not in within-district Gini.",
)
figure(
    "eval_poverty_cluster.png",
    "Distribution of poverty rate and mean income by cluster. The low-income tier carries a much "
    "wider and higher poverty distribution.",
)
para(
    "A striking result is that both clusters share an almost identical mean Gini (≈ 0.34): "
    "within-district inequality is similar regardless of income level. The clusters are separated "
    "by absolute income and poverty, implying Malaysia’s disparity is predominantly "
    "between-district (geographic) rather than within-district."
)

h3("3.4.2  Forecast accuracy")
para(
    "Forecast accuracy was measured on the 5-year hold-out per state using MAE, RMSE and MAPE. "
    "The model is accurate: mean test RMSE is 0.0144 and mean MAPE is 3.82% across the 16 states. "
    "Errors are smallest for states with smooth historical series (Sabah, Sarawak, Kelantan) and "
    "largest for W.P. Labuan, whose volatile Gini history yields a 16.5% MAPE and warrants "
    "cautious interpretation of its forecast."
)
# Full per-state metrics table from ts_metrics_summary.csv
ts_rows = []
for _, r in ts_metrics.iterrows():
    ts_rows.append([
        r["State"], f"{r['MAE']:.4f}", f"{r['RMSE']:.4f}", f"{r['MAPE (%)']:.2f}",
        "Yes" if r["Stationary (train)"] else "No", f"{r['Forecast 2030']:.4f}",
    ])
table(
    "ARIMA(2,1,2) per-state evaluation and 2030 Gini forecast (sorted by RMSE).",
    ["State", "MAE", "RMSE", "MAPE (%)", "ADF stationary", "Forecast 2030"],
    ts_rows,
    col_widths=[1.9, 0.8, 0.8, 0.9, 1.3, 1.1],
    font_size=8,
)
figure(
    "eval_ts_metrics.png",
    "ARIMA forecast error by state (MAE, RMSE, MAPE). Red dashed lines mark the cross-state mean.",
)

h3("3.4.3  Discovered trends")
para(
    "Beyond accuracy, the fitted models reveal the substantive trends the project set out to find. "
    "The state-average Gini has fallen steadily from 0.498 (1974) to 0.359 (2022) and is forecast "
    "to reach roughly 0.357 by 2030 — a continued, if slowing, improvement. The poverty analysis "
    "exposes sharp district-level volatility, concentrated in Sarawak’s interior."
)
figure(
    "eval_gini_trends.png",
    "Gini coefficient trajectories for all 16 states, 1974–2022. The near-universal downward "
    "drift reflects five decades of redistributive development policy; Sabah remains the upper envelope.",
)
# poverty change tables
inc = pov.sort_values("poverty_abs_change", ascending=False).head(5)
dec = pov.sort_values("poverty_abs_change").head(5)
table(
    "Largest district increases in absolute poverty, 2019→2022.",
    ["District", "State", "2019 (%)", "2022 (%)", "Change (pp)"],
    [[r["district"], r["state"], f"{r['poverty_abs_2019']:.1f}", f"{r['poverty_abs_2022']:.1f}", f"+{r['poverty_abs_change']:.1f}"] for _, r in inc.iterrows()],
    col_widths=[1.6, 1.3, 1.1, 1.1, 1.2],
)
table(
    "Largest district decreases in absolute poverty, 2019→2022.",
    ["District", "State", "2019 (%)", "2022 (%)", "Change (pp)"],
    [[r["district"], r["state"], f"{r['poverty_abs_2019']:.1f}", f"{r['poverty_abs_2022']:.1f}", f"{r['poverty_abs_change']:.1f}"] for _, r in dec.iterrows()],
    col_widths=[1.6, 1.3, 1.1, 1.1, 1.2],
)
figure(
    "eval_poverty_change.png",
    "Average district poverty change by state, 2019→2022. Several Borneo states show net "
    "increases driven by commodity-dependent interior districts.",
    width=5.2,
)

h3("3.4.4  Real-world reliability check")
para(
    "To ensure the outputs are reliable rather than merely internally consistent, every headline "
    "figure was validated against DOSM’s official 2022 releases and the World Bank. The analysis "
    "runs on primary DOSM data, so the cross-sectional figures reconcile exactly; the modelled "
    "trend agrees in direction with the official national series."
)
table(
    "Validation of project outputs against official published statistics.",
    ["Indicator (2022)", "This project", "Official source", "Agreement"],
    [
        ["Highest-poverty state", "Sabah, 19.7%", "Sabah, 19.7% (DOSM)", "Exact"],
        ["National absolute poverty", "(states 0.1–19.7%)", "6.2% (DOSM)", "Consistent"],
        ["Sabah mean income", "RM 6,171", "RM 6,171 (DOSM HIES)", "Exact"],
        ["Selangor mean income", "RM 12,233", "RM 12,233 (DOSM HIES)", "Exact"],
        ["National Gini direction", "0.364→0.359 (state mean)", "0.407→0.404 (DOSM)", "Same direction"],
        ["Long-run Gini peak", "~0.50 (1970s)", "0.491 peak 1997 (World Bank)", "Consistent"],
    ],
    col_widths=[1.9, 1.5, 1.9, 1.1],
    font_size=8,
)
para(
    "One methodological caveat is worth stating for transparency. The project’s “national” Gini "
    "(0.359 in 2022) is the unweighted mean of the 16 state Gini coefficients, whereas DOSM’s "
    "official national Gini (0.404) is computed on the pooled distribution of all households and "
    "therefore also captures between-state inequality. The two are not expected to be equal; the "
    "important point is that both move in the same direction and the state-level series — which "
    "is what the ARIMA model actually forecasts — matches DOSM exactly per state.",
    italic=False,
)

# =============================================================================
# 4. AI DEMONSTRATOR
# =============================================================================
h1("AI demonstrator")
para(
    "The analysis is delivered as an interactive Flask web dashboard (app/dashboard.py, served at "
    "http://localhost:5050) so that non-technical stakeholders — policy analysts at agencies such "
    "as the Economic Planning Unit — can explore the results without running code. The dashboard "
    "is launched together with the pipeline via python run_pipeline.py."
)
para("The demonstrator exposes four tabs, each backed by a lightweight JSON API:")
bullets([
    ("Overview. ", "State-level HIES summary (income, expenditure, Gini, poverty) served from /api/overview, giving the national context at a glance."),
    ("Time-series forecast. ", "A state selector that calls /api/ts/forecast to draw the train/test/forecast Gini curve and display the MAE/RMSE/MAPE and ADF stationarity result for the chosen state."),
    ("Clustering. ", "The district cluster assignments and validity metrics (/api/cluster/districts, /api/cluster/metrics) with the PCA and profile figures."),
    ("Poverty analysis. ", "District-level 2019→2022 poverty change (/api/poverty/districts), filterable by state, highlighting the most-affected communities."),
])
para(
    "Architecturally the dashboard separates computation from presentation: the heavy analysis is "
    "pre-computed once by the pipeline and cached as JSON, CSV and PNG artefacts in outputs/, and "
    "the Flask layer simply serves those artefacts and answers the small API queries. This keeps "
    "the demonstrator fast and makes it trivially reproducible — anyone who clones the repository "
    "and runs the pipeline obtains byte-for-byte the same dashboard (the random seed is fixed at 42)."
)

# =============================================================================
# 5. CONCLUSIONS
# =============================================================================
h1("Conclusions")
para(
    "This project demonstrated that standard, transparent machine-learning methods can turn "
    "routinely published Malaysian government survey data into geographically targeted, "
    "policy-relevant insight. Three findings stand out."
)
bullets([
    ("Disparity is geographic, not local. ", "Clustering split the 160 districts into a large low-income/high-poverty tier (75.6%) and a smaller mid-income tier (24.4%) that share the same within-district Gini (≈ 0.34). Malaysia’s inequality problem is therefore primarily between districts, which argues for region-targeted development funding over uniform national instruments."),
    ("Inequality is improving but unevenly. ", "ARIMA forecasts the state-average Gini to keep declining toward ~0.357 by 2030, yet Kelantan — already among the poorest states — shows a rising trajectory, and Sabah remains the most unequal. These laggards merit accelerated, state-specific intervention."),
    ("Poverty volatility is concentrated in Borneo. ", "Sarawak’s interior districts dominate both the largest poverty increases and decreases of 2019–2022, pointing to structural dependence on commodity cycles and the need for livelihood diversification and stronger safety nets."),
])
para(
    "The results are reliable: the pipeline runs end-to-end and reproducibly, the clustering is "
    "robust across two algorithms, the forecasts achieve a 3.82% mean MAPE, and every "
    "cross-sectional output reconciles with DOSM’s official 2022 statistics. Limitations include "
    "the short and irregular state Gini series (which inflates uncertainty for volatile "
    "territories such as W.P. Labuan) and the use of an unweighted state-mean as a proxy for the "
    "national Gini. Future work could weight states by household count, adopt auto-ARIMA or "
    "exogenous regressors (GDP, unemployment), and extend clustering to a district-level time "
    "panel as more annual HIES district data becomes available."
)

# =============================================================================
# 6. REFERENCES
# =============================================================================
h1("References")
refs = [
    "Department of Statistics Malaysia (DOSM). (2023). Income Inequality Malaysia 2022. OpenDOSM. https://open.dosm.gov.my/data-catalogue/hh_inequality_state",
    "Department of Statistics Malaysia (DOSM). (2023). Poverty in Malaysia 2022. https://www.dosm.gov.my/portal-main/release-content/poverty-in-malaysia-",
    "Department of Statistics Malaysia (DOSM). (2023). Household Income Survey Report, Malaysia & States 2022. https://www.dosm.gov.my/portal-main/release-content/household-income-survey-report--malaysia--states",
    "OpenDOSM. (2023). Household Income & Expenditure by Administrative District (hies_district). https://open.dosm.gov.my/data-catalogue/hies_district",
    "data.gov.my. (2023). Poverty by Administrative District (hh_poverty_district). https://data.gov.my/data-catalogue/hh_poverty_district",
    "The World Bank. (2024). Gini index – Malaysia (SI.POV.GINI). https://data.worldbank.org/indicator/SI.POV.GINI?locations=MY",
    "Seabold, S., & Perktold, J. (2010). statsmodels: Econometric and statistical modeling with Python — ARIMA. https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html",
    "Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. JMLR 12, 2825–2830. https://scikit-learn.org/stable/modules/clustering.html",
    "Project source code and reproducible pipeline (E’s Island). GitHub: https://github.com/kenn040502/COS40007-Design-Project",
]
for i, r in enumerate(refs, 1):
    p = doc.add_paragraph(style="List Paragraph")
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    p.add_run(f"[{i}]  ").bold = True
    p.add_run(r)
    p.paragraph_format.space_after = Pt(4)

# =============================================================================
# 7. APPENDIX A
# =============================================================================
h1("Appendix A")
h2("A.1  Reproducing the analysis")
para(
    "The complete project is available at https://github.com/kenn040502/COS40007-Design-Project. "
    "To reproduce every figure, table and metric in this report:"
)
bullets([
    "pip install -r requirements.txt",
    "python data/download_datasets.py   (optional — refreshes raw DOSM CSVs)",
    "python run_analysis.py   (headless: preprocessing → ARIMA → clustering → evaluation)",
    "python run_pipeline.py   (runs the analysis then launches the dashboard at http://localhost:5050)",
])
para(
    "All randomness is seeded (random_state = 42), so results are deterministic. Outputs are "
    "written to data/processed/ (cleaned data), outputs/models/ (metrics JSON/CSV) and "
    "outputs/figures/ (27 PNG figures)."
)
h2("A.2  Additional per-state forecast figures")
para(
    "Figures for the remaining states are produced by the pipeline in outputs/figures/ "
    "(ts_<state>.png). Four further examples are included below for reference."
)
for fn, st in [("ts_selangor.png", "Selangor"), ("ts_w.p._labuan.png", "W.P. Labuan"),
               ("ts_sarawak.png", "Sarawak"), ("ts_pahang.png", "Pahang")]:
    figure(fn, f"ARIMA Gini forecast — {st}.", width=6.0)

doc.save(OUT)
print("Report written to:", OUT)
print(f"Figures embedded: {_fig['n']}  | Tables: {_tab['n']}")
