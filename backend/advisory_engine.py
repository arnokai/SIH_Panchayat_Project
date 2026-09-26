from dataclasses import asdict
from pathlib import Path

import yaml

from advisory_context import AdvisoryContext


# ============================================================
# TERRAMIND — ADVISORY RULE ENGINE
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

RULES_FILE = ROOT_DIR / "rules" / "rules.yaml"
if not RULES_FILE.exists():
    RULES_FILE = ROOT_DIR / "rules.yaml"
if not RULES_FILE.exists():
    RULES_FILE = BACKEND_DIR / "rules.yaml"


_RULES_CACHE = None


def load_rules(refresh: bool = False):
    """
    Load advisory rules from rules.yaml with in-memory caching.
    """
    global _RULES_CACHE
    if not refresh and _RULES_CACHE is not None:
        return _RULES_CACHE

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

    _RULES_CACHE = rules
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
# PRIORITY & CROP SPECIFICITY
# ============================================================

_PRIORITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1
}


def _is_specific_crop_match(rule, context_crop):
    """Check if rule specifically targets context_crop (not generic 'all')."""
    if not context_crop:
        return False
    rule_crops = [str(c).strip().lower() for c in rule.get("crop", [])]
    return "all" not in rule_crops and str(context_crop).strip().lower() in rule_crops


def _rule_score(rule, context_crop):
    """
    Score a matching rule:
    - Base priority (high=3, medium=2, low=1)
    - Exclusive single-crop rule boost (+0.6)
    - Multi-crop targeted rule boost (+0.3)
    - Generic 'all' rule (+0.0)
    """
    base_p = _PRIORITY_ORDER.get(
        str(rule.get("priority", "low")).lower(),
        0
    )
    rule_crops = [str(c).strip().lower() for c in rule.get("crop", [])]
    if not context_crop or "all" in rule_crops:
        crop_boost = 0.0
    elif len(rule_crops) == 1 and str(context_crop).strip().lower() in rule_crops:
        crop_boost = 0.6
    elif str(context_crop).strip().lower() in rule_crops:
        crop_boost = 0.3
    else:
        crop_boost = 0.0
    return base_p + crop_boost


# ============================================================
# PRIMARY ADVISORY
# ============================================================

def get_primary_advisory(
    context: AdvisoryContext
):
    """
    Select the highest-priority matching rule.
    Crop-specific rules are preferred over generic fallbacks at the same priority level.
    If scores are equal, the earlier rule in YAML wins.
    """

    matches = evaluate_advisories(
        context
    )

    if not matches:
        return None

    best = matches[0]
    best_score = _rule_score(best, context.crop)

    for rule in matches[1:]:
        score = _rule_score(rule, context.crop)
        if score > best_score:
            best = rule
            best_score = score

    return best


# ============================================================
# API-FRIENDLY RESPONSE
# ============================================================

REQUIRED_CROP_INSTITUTES = {
    "paddy": "ICAR-NRRI (National Rice Research Institute) & BCKV Agromet Field Unit",
    "potato": "ICAR-CPRI (Central Potato Research Institute) & BCKV Mohanpur",
    "mustard": "ICAR-DRMR (Directorate of Rapeseed-Mustard Research) & District KVKs",
    "jute": "ICAR-CRIJAF (Central Research Institute for Jute and Allied Fibres, Barrackpore)",
    "vegetables": "ICAR-IIHR (Indian Institute of Horticultural Research) & Dept. of Agriculture, WB",
}


def build_advisory_response(
    context: AdvisoryContext
):
    """
    Convert the selected rule into a stable response shape,
    enriched with authoritative source attribution, crop context, and action items.
    """

    advisory = get_primary_advisory(
        context
    )

    clean_crop = str(context.crop or "").strip().lower()
    req_source = REQUIRED_CROP_INSTITUTES.get(clean_crop)

    if advisory is None:
        return {
            "rule_id": "none",
            "priority": "low",
            "type": "info",
            "crop": context.crop or "all",
            "crop_stage": context.crop_stage,
            "source": req_source if req_source else "IMD Gramin Krishi Mausam Sewa (GKMS)",
            "action_items": [],
            "text_en": "",
            "text_bn": "",
        }

    rule_crops = advisory.get("crop", ["all"])
    resolved_crop = context.crop if context.crop else (rule_crops[0] if rule_crops else "all")
    source_val = advisory.get("source", "IMD Agromet Advisory Service (AAS)")

    if req_source:
        inst_tag = {
            "paddy": "NRRI",
            "potato": "CPRI",
            "mustard": "DRMR",
            "jute": "CRIJAF",
            "vegetables": "IIHR",
        }.get(clean_crop, "")
        if inst_tag and inst_tag not in source_val:
            source_val = f"{req_source} & {source_val}"

    return {
        "rule_id": advisory.get("id", "unknown"),
        "priority": advisory.get("priority", "low"),
        "type": advisory.get("type", "info"),
        "crop": resolved_crop,
        "crop_stage": context.crop_stage,
        "source": source_val,
        "action_items": advisory.get("action_items", []),
        "text_en": advisory.get("text_en", ""),
        "text_bn": advisory.get("text_bn", ""),
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