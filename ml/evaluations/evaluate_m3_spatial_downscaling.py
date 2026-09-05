import joblib
import numpy as np
import pandas as pd


# ============================================================
# TERRAMIND M3 SPATIAL DOWNSCALING VERIFICATION
# ============================================================
#
# This script does NOT retrain anything.
#
# It checks whether the M3 model is actually producing
# Panchayat-specific forecasts rather than simply applying
# the same correction everywhere.
#
# ============================================================


DATA_FILE = (
    "data/raw/v2_downscaling_training_dataset.csv"
)

PREDICTIONS_FILE = (
    "data/raw/v2_downscaling_predictions.csv"
)

MODEL_FILE = (
    "models/v2_downscaling_rain_regressor.pkl"
)

METADATA_FILE = (
    "models/v2_downscaling_metadata.pkl"
)


# ============================================================
# LOAD
# ============================================================

print(
    "========================================"
)

print(
    "M3 SPATIAL DOWNSCALING VERIFICATION"
)

print(
    "========================================"
)


df = pd.read_csv(
    DATA_FILE,
    parse_dates=["date"]
)

pred = pd.read_csv(
    PREDICTIONS_FILE,
    parse_dates=["date"]
)

model = joblib.load(
    MODEL_FILE
)

metadata = joblib.load(
    METADATA_FILE
)


features = metadata["features"]


print(
    "Training rows:",
    len(df)
)

print(
    "Prediction rows:",
    len(pred)
)

print(
    "Model features:",
    len(features)
)


# ============================================================
# TEST DATA
# ============================================================

TEST_START = pd.Timestamp(
    "2025-01-01"
)


test = df[
    df["date"] >= TEST_START
].copy()


print(
    "Test rows:",
    len(test)
)


# ============================================================
# 1. REGENERATE MODEL PREDICTIONS
# ============================================================

model_prediction = (
    model.predict(
        test[features]
    )
)


test[
    "model_prediction"
] = np.clip(
    model_prediction,
    0,
    None
)


# ============================================================
# 2. COARSE BASELINE
# ============================================================

test[
    "coarse_prediction"
] = (
    test["coarse_rain_mm"]
)


# ============================================================
# 3. SPATIAL SPREAD PER DATE
# ============================================================
#
# For each date:
#
# coarse rainfall = one common value
#
# model rainfall = potentially different value
# for each Panchayat.
#
# ============================================================

date_summary = (
    test
    .groupby("date")
    .agg(

        coarse_rain=(
            "coarse_rain_mm",
            "first"
        ),

        model_mean=(
            "model_prediction",
            "mean"
        ),

        model_min=(
            "model_prediction",
            "min"
        ),

        model_max=(
            "model_prediction",
            "max"
        ),

        model_std=(
            "model_prediction",
            "std"
        ),

        actual_mean=(
            "chirps_rain_mm",
            "mean"
        ),

        actual_min=(
            "chirps_rain_mm",
            "min"
        ),

        actual_max=(
            "chirps_rain_mm",
            "max"
        ),

        actual_std=(
            "chirps_rain_mm",
            "std"
        ),

        panchayats=(
            "panchayat_id",
            "count"
        )

    )
    .reset_index()
)


date_summary[
    "model_range"
] = (
    date_summary["model_max"]
    -
    date_summary["model_min"]
)


date_summary[
    "actual_range"
] = (
    date_summary["actual_max"]
    -
    date_summary["actual_min"]
)


# ============================================================
# 4. OVERALL SPATIAL DIFFERENTIATION
# ============================================================

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
    "Average model spatial range:",
    round(
        date_summary[
            "model_range"
        ].mean(),
        3
    ),
    "mm"
)


print(
    "Average actual spatial range:",
    round(
        date_summary[
            "actual_range"
        ].mean(),
        3
    ),
    "mm"
)


print(
    "Average model spatial std:",
    round(
        date_summary[
            "model_std"
        ].mean(),
        3
    ),
    "mm"
)


print(
    "Average actual spatial std:",
    round(
        date_summary[
            "actual_std"
        ].mean(),
        3
    ),
    "mm"
)


# ============================================================
# 5. PREDICTION VARIANCE RATIO
# ============================================================
#
# A value close to zero means the model is collapsing
# Panchayat differences.
#
# Around one means model spatial variability is similar
# in scale to the observed variability.
#
# ============================================================

model_variance = (
    date_summary[
        "model_std"
    ]
    .mean()
)


actual_variance = (
    date_summary[
        "actual_std"
    ]
    .mean()
)


variance_ratio = (
    model_variance
    /
    actual_variance
    if actual_variance > 0
    else np.nan
)


print(
    "Spatial variance ratio:",
    round(
        variance_ratio,
        3
    )
)


# ============================================================
# 6. DATE-LEVEL EXAMPLES
# ============================================================

print(
    "\n========================================"
)

print(
    "EXAMPLE SPATIAL FORECASTS"
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
        "\nDate:",
        date.date()
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
                "chirps_rain_mm",
                "coarse_prediction",
                "model_prediction"
            ]
        ]
        .sort_values(
            "model_prediction",
            ascending=False
        )
        .round(2)
        .to_string(index=False)
    )


# ============================================================
# 7. ERROR COMPARISON BY PANCHAYAT
# ============================================================

print(
    "\n========================================"
)

print(
    "PANCHANTAY-LEVEL BASELINE VS MODEL"
)

print(
    "========================================"
)


panchayat_results = []


for panchayat_id, group in (
    test.groupby("panchayat_id")
):

    actual = (
        group[
            "chirps_rain_mm"
        ]
        .to_numpy()
    )

    coarse = (
        group[
            "coarse_prediction"
        ]
        .to_numpy()
    )

    model_pred = (
        group[
            "model_prediction"
        ]
        .to_numpy()
    )


    coarse_rmse = np.sqrt(
        np.mean(
            (
                actual
                -
                coarse
            )
            ** 2
        )
    )


    model_rmse = np.sqrt(
        np.mean(
            (
                actual
                -
                model_pred
            )
            ** 2
        )
    )


    coarse_mae = np.mean(
        np.abs(
            actual
            -
            coarse
        )
    )


    model_mae = np.mean(
        np.abs(
            actual
            -
            model_pred
        )
    )


    panchayat_results.append({

        "panchayat_id":
            panchayat_id,

        "coarse_rmse":
            coarse_rmse,

        "model_rmse":
            model_rmse,

        "rmse_change_percent":
            (
                (
                    coarse_rmse
                    -
                    model_rmse
                )
                /
                coarse_rmse
                *
                100
                if coarse_rmse > 0
                else 0
            ),

        "coarse_mae":
            coarse_mae,

        "model_mae":
            model_mae,

        "mae_change_percent":
            (
                (
                    coarse_mae
                    -
                    model_mae
                )
                /
                coarse_mae
                *
                100
                if coarse_mae > 0
                else 0
            )

    })


panchayat_results = (
    pd.DataFrame(
        panchayat_results
    )
    .sort_values(
        "panchayat_id"
    )
)


print(
    panchayat_results
    .round(3)
    .to_string(index=False)
)


# ============================================================
# 8. DOES THE MODEL IMPROVE SPATIAL ORDERING?
# ============================================================
#
# Compare model vs actual spatial ranking per date.
#
# We measure Spearman correlation manually using pandas
# rank() so no scipy dependency is required.
# ============================================================

spatial_correlations = []


for date, group in (
    test.groupby("date")
):

    if (
        group[
            "chirps_rain_mm"
        ].nunique()
        <
        2
    ):

        continue


    actual_rank = (
        group[
            "chirps_rain_mm"
        ]
        .rank(
            method="average"
        )
    )


    model_rank = (
        group[
            "model_prediction"
        ]
        .rank(
            method="average"
        )
    )


    correlation = (
        actual_rank
        .corr(
            model_rank
        )
    )


    if not pd.isna(
        correlation
    ):

        spatial_correlations.append(
            correlation
        )


if spatial_correlations:

    mean_spatial_correlation = (
        np.mean(
            spatial_correlations
        )
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
        "Mean per-date rank correlation:",
        round(
            mean_spatial_correlation,
            3
        )
    )


# ============================================================
# 9. FEATURE IMPORTANCE
# ============================================================

print(
    "\n========================================"
)

print(
    "TOP LOCAL / TERRAIN FEATURES"
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


local_keywords = [
    "latitude",
    "longitude",
    "elevation",
    "slope",
    "aspect",
    "roughness",
    "relative_elevation"
]


local_importance = (
    importance[
        importance["feature"]
        .str.lower()
        .apply(
            lambda x:
                any(
                    key in x
                    for key
                    in local_keywords
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
# 10. SAVE VERIFICATION OUTPUT
# ============================================================

OUTPUT_FILE = (
    "data/raw/"
    "m3_spatial_verification.csv"
)


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


# ============================================================
# COMPLETE
# ============================================================

print(
    "\n========================================"
)

print(
    "M3 SPATIAL VERIFICATION COMPLETE"
)

print(
    "========================================"
)