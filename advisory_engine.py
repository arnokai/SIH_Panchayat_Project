from dataclasses import asdict
from pathlib import Path

import yaml

from advisory_context import AdvisoryContext


# ============================================================
# TERRAMIND — ADVISORY RULE ENGINE
# ============================================================

RULES_FILE = (
    Path(__file__).parent
    / "rules.yaml"
)


# ============================================================
# LOAD RULES
# ============================================================

def load_rules():
    """
    Load advisory rules from rules.yaml.
    """

    if not RULES_FILE.exists():
        raise FileNotFoundError(
            f"Rules file not found: {RULES_FILE}"
        )

    with open(
        RULES_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "rules.yaml must contain a mapping."
        )

    rules = data.get("rules")

    if not isinstance(rules, list):
        raise ValueError(
            "rules.yaml must contain a 'rules' list."
        )

    return rules


# ============================================================
# CONTEXT FILTER
# ============================================================

def _matches_list(
    value,
    allowed_values
):
    """
    Match a context value against a YAML list.

    'all' means the rule accepts any value.
    Missing context means the rule does not apply.
    """

    if not allowed_values:
        return True

    normalized = [
        str(item).strip().lower()
        for item in allowed_values
    ]

    if "all" in normalized:
        return True

    if value is None:
        return False

    return (
        str(value).strip().lower()
        in normalized
    )


def rule_applies(
    rule,
    context
):
    """
    Evaluate non-numeric contextual filters such as:

        crop
        stage
        soil
    """

    if not _matches_list(
        context.crop,
        rule.get("crop", [])
    ):
        return False

    if not _matches_list(
        context.crop_stage,
        rule.get("stage", [])
    ):
        return False

    if not _matches_list(
        context.soil_type,
        rule.get("soil", [])
    ):
        return False

    return True


# ============================================================
# CONDITION EVALUATION
# ============================================================

def evaluate_condition(
    condition,
    context
):
    """
    Evaluate a YAML condition against AdvisoryContext.

    Only fields contained in AdvisoryContext are exposed.

    Missing values must never trigger a rule.
    """

    values = asdict(context)

    try:

        result = eval(
            condition,
            {
                "__builtins__": {}
            },
            values
        )

        return bool(result)

    except (
        NameError,
        TypeError
    ):
        # Example:
        #
        # humidity = None
        # condition = "humidity > 85"
        #
        # Unknown context means the rule cannot be
        # evaluated. It must not crash the engine.
        return False

    except Exception as exc:

        raise ValueError(
            f"Failed to evaluate condition "
            f"'{condition}': {exc}"
        ) from exc


# ============================================================
# ALL MATCHING RULES
# ============================================================

def evaluate_advisories(
    context: AdvisoryContext
):
    """
    Return every rule that matches the supplied context.
    """

    rules = load_rules()

    matches = []

    for rule in rules:

        if not isinstance(
            rule,
            dict
        ):
            continue

        if not rule_applies(
            rule,
            context
        ):
            continue

        condition = rule.get(
            "condition"
        )

        if not condition:
            continue

        if evaluate_condition(
            condition,
            context
        ):
            matches.append(rule)

    return matches


# ============================================================
# PRIORITY
# ============================================================

_PRIORITY_ORDER = {
    "high": 3,
    "medium": 2,
    "low": 1
}


# ============================================================
# PRIMARY ADVISORY
# ============================================================

def get_primary_advisory(
    context: AdvisoryContext
):
    """
    Select the highest-priority matching rule.

    If priorities are equal, the earlier rule in YAML wins.
    """

    matches = evaluate_advisories(
        context
    )

    if not matches:
        return None

    best = matches[0]

    best_priority = _PRIORITY_ORDER.get(
        str(
            best.get(
                "priority",
                "low"
            )
        ).lower(),
        0
    )

    for rule in matches[1:]:

        priority = _PRIORITY_ORDER.get(
            str(
                rule.get(
                    "priority",
                    "low"
                )
            ).lower(),
            0
        )

        if priority > best_priority:
            best = rule
            best_priority = priority

    return best


# ============================================================
# API-FRIENDLY RESPONSE
# ============================================================

def build_advisory_response(
    context: AdvisoryContext
):
    """
    Convert the selected rule into a stable response shape.
    """

    advisory = get_primary_advisory(
        context
    )

    if advisory is None:

        return {
            "rule_id": "none",
            "priority": "low",
            "type": "info",
            "text_en": "",
            "text_bn": "",
        }

    return {
        "rule_id":
            advisory.get(
                "id",
                "unknown"
            ),

        "priority":
            advisory.get(
                "priority",
                "low"
            ),

        "type":
            advisory.get(
                "type",
                "info"
            ),

        "text_en":
            advisory.get(
                "text_en",
                ""
            ),

        "text_bn":
            advisory.get(
                "text_bn",
                ""
            ),
    }


# ============================================================
# TEST HELPERS
# ============================================================

def run_test(
    name,
    context
):
    result = build_advisory_response(
        context
    )

    print(
        f"\n{name}"
    )

    print(
        result
    )


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        "TERRAMIND ADVISORY ENGINE TEST"
    )

    print(
        "========================================"
    )


    # --------------------------------------------------------
    # 1. Heavy rain
    # --------------------------------------------------------

    run_test(
        "1. Heavy rain",

        AdvisoryContext(
            rain_mm=25.0,
            tmax_c=30.0,
            crop="paddy",
            crop_stage="vegetative",
        )
    )


    # --------------------------------------------------------
    # 2. Flowering heat stress
    # --------------------------------------------------------

    run_test(
        "2. Flowering heat stress",

        AdvisoryContext(
            rain_mm=2.0,
            tmax_c=39.0,
            crop="paddy",
            crop_stage="flowering",
        )
    )


    # --------------------------------------------------------
    # 3. Paddy blast risk
    # --------------------------------------------------------

    run_test(
        "3. Paddy blast risk",

        AdvisoryContext(
            rain_mm=5.0,
            tmax_c=31.0,
            humidity=88.0,
            humidity_days=3,
            crop="paddy",
            crop_stage="vegetative",
        )
    )


    # --------------------------------------------------------
    # 4. Sandy-soil dry spell
    # --------------------------------------------------------

    run_test(
        "4. Sandy-soil dry spell",

        AdvisoryContext(
            rain_mm=0.0,
            tmax_c=30.0,
            dry_days=7,
            soil_type="sandy",
            crop="paddy",
            crop_stage="vegetative",
        )
    )


    # --------------------------------------------------------
    # 5. Harvest rain
    # --------------------------------------------------------

    run_test(
        "5. Harvest rain",

        AdvisoryContext(
            rain_mm=8.0,
            tmax_c=30.0,
            crop="paddy",
            crop_stage="harvest",
            harvest_window=True,
        )
    )


    # --------------------------------------------------------
    # 6. Light rain
    # --------------------------------------------------------

    run_test(
        "6. Light rain",

        AdvisoryContext(
            rain_mm=3.0,
            tmax_c=30.0,
            crop="paddy",
            crop_stage="vegetative",
        )
    )


    # --------------------------------------------------------
    # 7. Moderate rain
    # --------------------------------------------------------

    run_test(
        "7. Moderate rain",

        AdvisoryContext(
            rain_mm=8.0,
            tmax_c=30.0,
            crop="paddy",
            crop_stage="vegetative",
        )
    )


    # --------------------------------------------------------
    # 8. No rain
    # --------------------------------------------------------

    run_test(
        "8. No rain",

        AdvisoryContext(
            rain_mm=0.0,
            tmax_c=30.0,
            crop="paddy",
            crop_stage="vegetative",
        )
    )


    # --------------------------------------------------------
    # 9. Missing humidity
    #
    # This specifically verifies that the blast rule does not
    # crash when humidity data is unavailable.
    # --------------------------------------------------------

    run_test(
        "9. Missing humidity",

        AdvisoryContext(
            rain_mm=8.0,
            tmax_c=30.0,
            humidity=None,
            humidity_days=None,
            crop="paddy",
            crop_stage="vegetative",
        )
    )


    print(
        "\n========================================"
    )

    print(
        "ADVISORY ENGINE TEST COMPLETE"
    )

    print(
        "========================================"
    )