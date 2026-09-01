import joblib
import numpy as np
import pandas as pd


# ============================================================
# TERRAMIND — TUNED M3 SPATIAL VERIFICATION
# ============================================================

DATA_FILE = (
    "data/raw/m3_clean_downscaling_dataset.csv"
)

MODEL_FILE = (
    "models/m3_clean_tuned_rain_regressor.pkl"
)

METADATA_FILE = (
    "models/m3_clean_tuned_metadata.pkl"
)

OUTPUT_FILE = (
    "data/raw/m3_tuned_spatial_verification.csv"
)


TEST_START = pd.Timestamp(
    "2025-01-01"
)


# ============================================================
# LOAD
# ============================================================

print(
    "========================================"
)

print(
    "TUNED M3 SPATIAL VERIFICATION"
)

print(
    "========================================"
)


df = pd.read_csv(
    DATA_FILE,
    parse_dates=["date"]
)

model = joblib.load(
    MODEL_FILE
)

metadata = joblib.load(
    METADATA_FILE
)

features = metadata["features"]


test = df[
    df["date"] >= TEST_START
].copy()


# ============================================================
# PREDICTION
# ============================================================

test["predicted_rain_mm"] = np.clip(
    model.predict(
        test[features]
    ),
    0,
    None
)


test["coarse_rain_mm"] = (
    test["coarse_rain_mm"]
)


test["actual_rain_mm"] = (
    test["chirps_rain_mm"]
)


# ============================================================
# DATE-LEVEL SPATIAL STATISTICS
# ============================================================

date_summary = (
    test
    .groupby("date")
    .agg(

        coarse=(
            "coarse_rain_mm",
            "first"
        ),

        model_min=(
            "predicted_rain_mm",
            "min"
        ),

        model_max=(
            "predicted_rain_mm",
            "max"
        ),

        model_std=(
            "predicted_rain_mm",
            "std"
        ),

        actual_min=(
            "actual_rain_mm",
            "min"
        ),

        actual_max=(
            "actual_rain_mm",
            "max"
        ),

        actual_std=(
            "actual_rain_mm",
            "std"
        )

    )
    .reset_index()
)


date_summary["model_range"] = (
    date_summary["model_max"]
    -
    date_summary["model_min"]
)

date_summary["actual_range"] = (
    date_summary["actual_max"]
    -
    date_summary["actual_min"]
)


# ============================================================
# SPATIAL SUMMARY
# ============================================================

model_spatial_range = (
    date_summary["model_range"]
    .mean()
)

actual_spatial_range = (
    date_summary["actual_range"]
    .mean()
)

model_spatial_std = (
    date_summary["model_std"]
    .mean()
)

actual_spatial_std = (
    date_summary["actual_std"]
    .mean()
)


variance_ratio = (
    model_spatial_std
    /
    actual_spatial_std
    if actual_spatial_std > 0
    else np.nan
)


print(
    "\n========================================"
)

print(
    "SPATIAL DIFFERENTIATION"
)

print(
    "========================================"
)

print(
    f"Average model spatial range: "
    f"{model_spatial_range:.3f} mm"
)

print(
    f"Average actual spatial range: "
    f"{actual_spatial_range:.3f} mm"
)

print(
    f"Average model spatial std: "
    f"{model_spatial_std:.3f} mm"
)

print(
    f"Average actual spatial std: "
    f"{actual_spatial_std:.3f} mm"
)

print(
    f"Spatial variance ratio: "
    f"{variance_ratio:.3f}"
)


# ============================================================
# SPATIAL RANK CORRELATION
# ============================================================

correlations = []


for date, group in (
    test.groupby("date")
):

    if (
        group["actual_rain_mm"].nunique()
        < 2
    ):

        continue


    actual_rank = (
        group["actual_rain_mm"]
        .rank(
            method="average"
        )
    )

    model_rank = (
        group["predicted_rain_mm"]
        .rank(
            method="average"
        )
    )


    corr = actual_rank.corr(
        model_rank
    )


    if not pd.isna(corr):

        correlations.append(
            corr
        )


mean_rank_corr = (
    np.mean(correlations)
    if correlations
    else np.nan
)


print(
    "\n========================================"
)

print(
    "SPATIAL RANK CORRELATION"
)

print(
    "========================================"
)

print(
    f"Mean per-date rank correlation: "
    f"{mean_rank_corr:.3f}"
)


# ============================================================
# EXAMPLE DIFFERENTIATED DATES
# ============================================================

print(
    "\n========================================"
)

print(
    "EXAMPLE PANCHAYAT OUTPUTS"
)

print(
    "========================================"
)


example_dates = (
    date_summary
    .sort_values(
        "model_range",
        ascending=False
    )
    .head(10)
    ["date"]
)


for date in example_dates:

    x = test[
        test["date"] == date
    ].copy()


    print(
        f"\nDate: {date.date()}"
    )

    print(
        "Common coarse rainfall:",
        round(
            x[
                "coarse_rain_mm"
            ].iloc[0],
            2
        ),
        "mm"
    )


    print(
        x[
            [
                "panchayat_id",
                "panchayat_name",
                "actual_rain_mm",
                "predicted_rain_mm"
            ]
        ]
        .sort_values(
            "predicted_rain_mm",
            ascending=False
        )
        .round(2)
        .to_string(index=False)
    )


# ============================================================
# LOCAL FEATURE IMPORTANCE
# ============================================================

print(
    "\n========================================"
)

print(
    "LOCAL / TERRAIN FEATURE IMPORTANCE"
)

print(
    "========================================"
)


importance = pd.DataFrame({

    "feature":
        features,

    "importance":
        model.feature_importances_

})


importance = (
    importance
    .sort_values(
        "importance",
        ascending=False
    )
)


local_terms = [
    "latitude",
    "longitude",
    "elevation",
    "slope",
    "aspect",
    "roughness",
    "relative_elevation",
    "distance_to_river",
]


local_importance = (
    importance[
        importance["feature"]
        .str.lower()
        .apply(
            lambda x:
                any(
                    term in x
                    for term in local_terms
                )
        )
    ]
)


print(
    local_importance
    .round(6)
    .to_string(index=False)
)


# ============================================================
# SAVE
# ============================================================

date_summary.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    "\nSaved:"
)

print(
    OUTPUT_FILE
)


print(
    "\n========================================"
)

print(
    "TUNED M3 SPATIAL VERIFICATION COMPLETE"
)

print(
    "========================================"
)