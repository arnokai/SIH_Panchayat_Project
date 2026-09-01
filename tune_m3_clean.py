import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)

from xgboost import XGBClassifier, XGBRegressor


# ============================================================
# TERRAMIND M3 CLEAN — VALIDATION-ONLY TUNING
# ============================================================
#
# IMPORTANT:
# The test period is NOT used to select hyperparameters.
#
# We compare a small number of controlled XGBoost
# configurations using the validation period only.
#
# After selecting the best configuration, we train one final
# model on TRAIN + VALIDATION and evaluate it ONCE on TEST.
#
# ============================================================


DATA_FILE = (
    "data/raw/m3_clean_downscaling_dataset.csv"
)

RESULTS_FILE = (
    "data/raw/m3_clean_tuning_results.csv"
)

METADATA_FILE = (
    "models/m3_clean_metadata.pkl"
)


TARGET = "chirps_rain_mm"

RAIN_THRESHOLD = 0.1

EVENT_THRESHOLD = 2.5


# ============================================================
# FEATURES
# ============================================================

FEATURES = [

    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",

    "latitude",
    "longitude",

    "elevation",
    "distance_to_river_m",

    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    "month",
    "day_of_year",
    "day_of_year_sin",
    "day_of_year_cos",
]


# ============================================================
# LOAD
# ============================================================

print(
    "========================================"
)

print(
    "M3 CLEAN VALIDATION TUNING"
)

print(
    "========================================"
)


df = pd.read_csv(
    DATA_FILE,
    parse_dates=["date"]
)


# ============================================================
# TEMPORAL SPLIT
# ============================================================

train = df[
    df["date"]
    <=
    pd.Timestamp("2024-08-31")
].copy()


validation = df[
    (
        df["date"]
        >=
        pd.Timestamp("2024-09-01")
    )
    &
    (
        df["date"]
        <=
        pd.Timestamp("2024-12-31")
    )
].copy()


test = df[
    df["date"]
    >=
    pd.Timestamp("2025-01-01")
].copy()


print(
    "Training:",
    len(train)
)

print(
    "Validation:",
    len(validation)
)

print(
    "Test:",
    len(test)
)


# ============================================================
# HELPER
# ============================================================

def event_metrics(
    actual,
    predicted
):

    observed = (
        actual
        >=
        EVENT_THRESHOLD
    )

    predicted_event = (
        predicted
        >=
        EVENT_THRESHOLD
    )


    hits = np.sum(
        observed
        &
        predicted_event
    )

    misses = np.sum(
        observed
        &
        ~predicted_event
    )

    false_alarms = np.sum(
        ~observed
        &
        predicted_event
    )


    pod = (
        hits
        /
        (hits + misses)
        if hits + misses
        else 0.0
    )

    far = (
        false_alarms
        /
        (
            hits
            +
            false_alarms
        )
        if (
            hits
            +
            false_alarms
        )
        else 0.0
    )

    csi = (
        hits
        /
        (
            hits
            +
            misses
            +
            false_alarms
        )
        if (
            hits
            +
            misses
            +
            false_alarms
        )
        else 0.0
    )


    return (
        pod,
        far,
        csi
    )


# ============================================================
# PARAMETER SEARCH
# ============================================================
#
# Small controlled search.
# We are NOT doing hundreds of trials.
#
# ============================================================

classifier_configs = [

    {
        "n_estimators": 250,
        "max_depth": 3,
        "learning_rate": 0.05,
    },

    {
        "n_estimators": 400,
        "max_depth": 3,
        "learning_rate": 0.05,
    },

    {
        "n_estimators": 400,
        "max_depth": 4,
        "learning_rate": 0.05,
    },

    {
        "n_estimators": 600,
        "max_depth": 4,
        "learning_rate": 0.03,
    },

]


regressor_configs = [

    {
        "n_estimators": 300,
        "max_depth": 3,
        "learning_rate": 0.05,
    },

    {
        "n_estimators": 500,
        "max_depth": 3,
        "learning_rate": 0.05,
    },

    {
        "n_estimators": 500,
        "max_depth": 4,
        "learning_rate": 0.05,
    },

    {
        "n_estimators": 700,
        "max_depth": 4,
        "learning_rate": 0.03,
    },

]


results = []


# ============================================================
# TUNE
# ============================================================

trial_number = 0


for clf_config in classifier_configs:

    for reg_config in regressor_configs:

        trial_number += 1


        print(
            "\n----------------------------------------"
        )

        print(
            "Trial:",
            trial_number
        )

        print(
            "Classifier:",
            clf_config
        )

        print(
            "Regressor:",
            reg_config
        )


        # ----------------------------------------------------
        # CLASSIFIER
        # ----------------------------------------------------

        y_train_event = (
            train[TARGET]
            >
            RAIN_THRESHOLD
        ).astype(int)


        classifier = XGBClassifier(

            n_estimators=
                clf_config[
                    "n_estimators"
                ],

            max_depth=
                clf_config[
                    "max_depth"
                ],

            learning_rate=
                clf_config[
                    "learning_rate"
                ],

            subsample=0.9,

            colsample_bytree=0.9,

            objective="binary:logistic",

            eval_metric="logloss",

            random_state=42,

            n_jobs=-1,

        )


        classifier.fit(
            train[FEATURES],
            y_train_event
        )


        # ----------------------------------------------------
        # WET-DAY REGRESSOR
        # ----------------------------------------------------

        wet_train = train[
            train[TARGET]
            >
            RAIN_THRESHOLD
        ].copy()


        regressor = XGBRegressor(

            n_estimators=
                reg_config[
                    "n_estimators"
                ],

            max_depth=
                reg_config[
                    "max_depth"
                ],

            learning_rate=
                reg_config[
                    "learning_rate"
                ],

            subsample=0.9,

            colsample_bytree=0.9,

            objective="reg:squarederror",

            random_state=42,

            n_jobs=-1,

        )


        regressor.fit(

            wet_train[FEATURES],

            np.log1p(
                wet_train[TARGET]
            )

        )


        # ----------------------------------------------------
        # VALIDATION PREDICTION
        # ----------------------------------------------------

        probability = (
            classifier
            .predict_proba(
                validation[FEATURES]
            )[:, 1]
        )


        amount = np.expm1(
            regressor.predict(
                validation[FEATURES]
            )
        )


        prediction = np.where(
            probability >= 0.30,
            amount,
            0.0
        )


        prediction = np.clip(
            prediction,
            0.0,
            None
        )


        truth = (
            validation[TARGET]
            .to_numpy()
        )


        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        rmse = np.sqrt(
            mean_squared_error(
                truth,
                prediction
            )
        )


        mae = mean_absolute_error(
            truth,
            prediction
        )


        # ----------------------------------------------------
        # EVENT METRICS
        # ----------------------------------------------------

        pod, far, csi = event_metrics(
            truth,
            prediction
        )


        # ----------------------------------------------------
        # HEAVY RAIN
        # ----------------------------------------------------

        heavy = (
            truth >= 25.0
        )


        if heavy.sum() > 0:

            heavy_rmse = np.sqrt(
                mean_squared_error(
                    truth[heavy],
                    prediction[heavy]
                )
            )

            heavy_mae = (
                mean_absolute_error(
                    truth[heavy],
                    prediction[heavy]
                )
            )

        else:

            heavy_rmse = np.nan
            heavy_mae = np.nan


        print(
            f"Validation RMSE: {rmse:.2f}"
        )

        print(
            f"Validation MAE:  {mae:.2f}"
        )

        print(
            f"POD: {pod:.2f} | "
            f"FAR: {far:.2f} | "
            f"CSI: {csi:.2f}"
        )

        print(
            f"Heavy RMSE: "
            f"{heavy_rmse:.2f}"
        )


        results.append({

            "trial":
                trial_number,

            "clf_n_estimators":
                clf_config[
                    "n_estimators"
                ],

            "clf_max_depth":
                clf_config[
                    "max_depth"
                ],

            "clf_learning_rate":
                clf_config[
                    "learning_rate"
                ],

            "reg_n_estimators":
                reg_config[
                    "n_estimators"
                ],

            "reg_max_depth":
                reg_config[
                    "max_depth"
                ],

            "reg_learning_rate":
                reg_config[
                    "learning_rate"
                ],

            "validation_rmse":
                rmse,

            "validation_mae":
                mae,

            "validation_pod":
                pod,

            "validation_far":
                far,

            "validation_csi":
                csi,

            "validation_heavy_rmse":
                heavy_rmse,

            "validation_heavy_mae":
                heavy_mae,

        })


# ============================================================
# RESULTS
# ============================================================

results_df = pd.DataFrame(
    results
)


results_df = (
    results_df
    .sort_values(
        [
            "validation_rmse",
            "validation_mae"
        ]
    )
    .reset_index(drop=True)
)


print(
    "\n========================================"
)

print(
    "VALIDATION RANKING"
)

print(
    "========================================"
)


print(
    results_df[
        [
            "trial",
            "validation_rmse",
            "validation_mae",
            "validation_pod",
            "validation_far",
            "validation_csi",
            "validation_heavy_rmse"
        ]
    ]
    .round(3)
    .to_string(index=False)
)


# ============================================================
# SELECT BEST BY VALIDATION RMSE
# ============================================================

best = (
    results_df
    .iloc[0]
)


print(
    "\n========================================"
)

print(
    "SELECTED CONFIGURATION"
)

print(
    "========================================"
)


print(
    best.to_string()
)


# ============================================================
# RETRAIN ON TRAIN + VALIDATION
# ============================================================
#
# Test is untouched until this exact point.
# ============================================================

development = pd.concat(
    [
        train,
        validation
    ],
    ignore_index=True
)


y_development_event = (
    development[TARGET]
    >
    RAIN_THRESHOLD
).astype(int)


final_classifier = XGBClassifier(

    n_estimators=
        int(
            best[
                "clf_n_estimators"
            ]
        ),

    max_depth=
        int(
            best[
                "clf_max_depth"
            ]
        ),

    learning_rate=
        float(
            best[
                "clf_learning_rate"
            ]
        ),

    subsample=0.9,

    colsample_bytree=0.9,

    objective="binary:logistic",

    eval_metric="logloss",

    random_state=42,

    n_jobs=-1,

)


final_classifier.fit(
    development[FEATURES],
    y_development_event
)


wet_development = development[
    development[TARGET]
    >
    RAIN_THRESHOLD
].copy()


final_regressor = XGBRegressor(

    n_estimators=
        int(
            best[
                "reg_n_estimators"
            ]
        ),

    max_depth=
        int(
            best[
                "reg_max_depth"
            ]
        ),

    learning_rate=
        float(
            best[
                "reg_learning_rate"
            ]
        ),

    subsample=0.9,

    colsample_bytree=0.9,

    objective="reg:squarederror",

    random_state=42,

    n_jobs=-1,

)


final_regressor.fit(

    wet_development[FEATURES],

    np.log1p(
        wet_development[TARGET]
    )

)


# ============================================================
# FINAL TEST — ONE TIME
# ============================================================

print(
    "\n========================================"
)

print(
    "FINAL TEST — SELECTED MODEL"
)

print(
    "========================================"
)


test_probability = (
    final_classifier
    .predict_proba(
        test[FEATURES]
    )[:, 1]
)


test_amount = np.expm1(
    final_regressor.predict(
        test[FEATURES]
    )
)


test_prediction = np.where(
    test_probability >= 0.30,
    test_amount,
    0.0
)


test_prediction = np.clip(
    test_prediction,
    0.0,
    None
)


test_truth = (
    test[TARGET]
    .to_numpy()
)


test_rmse = np.sqrt(
    mean_squared_error(
        test_truth,
        test_prediction
    )
)


test_mae = mean_absolute_error(
    test_truth,
    test_prediction
)


test_pod, test_far, test_csi = (
    event_metrics(
        test_truth,
        test_prediction
    )
)


test_heavy = (
    test_truth >= 25.0
)


if test_heavy.sum() > 0:

    test_heavy_rmse = np.sqrt(
        mean_squared_error(
            test_truth[test_heavy],
            test_prediction[test_heavy]
        )
    )

    test_heavy_mae = (
        mean_absolute_error(
            test_truth[test_heavy],
            test_prediction[test_heavy]
        )
    )

else:

    test_heavy_rmse = np.nan
    test_heavy_mae = np.nan


baseline_test_rmse = np.sqrt(
    mean_squared_error(
        test_truth,
        test[
            "coarse_rain_mm"
        ].to_numpy()
    )
)


improvement = (
    (
        baseline_test_rmse
        -
        test_rmse
    )
    /
    baseline_test_rmse
    *
    100
)


print(
    f"Baseline RMSE: {baseline_test_rmse:.2f} mm"
)

print(
    f"Model RMSE:    {test_rmse:.2f} mm"
)

print(
    f"Model MAE:     {test_mae:.2f} mm"
)

print(
    f"Improvement:   {improvement:.1f}%"
)

print(
    "\nPOD:",
    f"{test_pod:.2f}"
)

print(
    "FAR:",
    f"{test_far:.2f}"
)

print(
    "CSI:",
    f"{test_csi:.2f}"
)

print(
    "Heavy RMSE:",
    f"{test_heavy_rmse:.2f} mm"
)

print(
    "Heavy MAE:",
    f"{test_heavy_mae:.2f} mm"
)


# ============================================================
# SAVE RESULTS
# ============================================================

results_df.to_csv(
    RESULTS_FILE,
    index=False
)


# ============================================================
# SAVE FINAL MODELS
# ============================================================

joblib.dump(
    final_classifier,
    "models/m3_clean_tuned_rain_classifier.pkl"
)


joblib.dump(
    final_regressor,
    "models/m3_clean_tuned_rain_regressor.pkl"
)


# ============================================================
# SAVE METADATA
# ============================================================

final_metadata = {

    "model_version":
        "M3-clean-tuned",

    "architecture":
        "XGBoost two-stage rainfall downscaling",

    "features":
        FEATURES,

    "rain_threshold":
        RAIN_THRESHOLD,

    "event_threshold":
        EVENT_THRESHOLD,

    "selected_configuration":
        {
            "classifier_n_estimators":
                int(
                    best[
                        "clf_n_estimators"
                    ]
                ),

            "classifier_max_depth":
                int(
                    best[
                        "clf_max_depth"
                    ]
                ),

            "classifier_learning_rate":
                float(
                    best[
                        "clf_learning_rate"
                    ]
                ),

            "regressor_n_estimators":
                int(
                    best[
                        "reg_n_estimators"
                    ]
                ),

            "regressor_max_depth":
                int(
                    best[
                        "reg_max_depth"
                    ]
                ),

            "regressor_learning_rate":
                float(
                    best[
                        "reg_learning_rate"
                    ]
                ),

        },

    "validation_rmse":
        float(
            best[
                "validation_rmse"
            ]
        ),

    "validation_mae":
        float(
            best[
                "validation_mae"
            ]
        ),

    "test_rmse":
        float(
            test_rmse
        ),

    "test_mae":
        float(
            test_mae
        ),

    "test_improvement_percent":
        float(
            improvement
        ),

    "pod":
        float(test_pod),

    "far":
        float(test_far),

    "csi":
        float(test_csi),

    "heavy_rmse":
        (
            float(
                test_heavy_rmse
            )
            if not np.isnan(
                test_heavy_rmse
            )
            else None
        ),

    "heavy_mae":
        (
            float(
                test_heavy_mae
            )
            if not np.isnan(
                test_heavy_mae
            )
            else None
        ),

    "warning":
        (
            "Retrospective experiment using "
            "historical coarse archive data, "
            "not archived issued forecasts."
        )
}


joblib.dump(
    final_metadata,
    "models/m3_clean_tuned_metadata.pkl"
)


print(
    "\n========================================"
)

print(
    "TUNING COMPLETE"
)

print(
    "Saved:"
)

print(
    RESULTS_FILE
)

print(
    "models/m3_clean_tuned_rain_classifier.pkl"
)

print(
    "models/m3_clean_tuned_rain_regressor.pkl"
)

print(
    "models/m3_clean_tuned_metadata.pkl"
)