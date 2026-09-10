from pathlib import Path
from datetime import date

import yaml


# ============================================================
# TERRAMIND — CROP CALENDAR LOOKUP
# ============================================================

CALENDAR_FILE = (
    Path(__file__).parent
    / "crop_calendar.yaml"
)


def load_crop_calendar():
    """
    Load the prototype crop calendar from YAML.
    """

    with open(
        CALENDAR_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return yaml.safe_load(file)


def _month_day(value: str):
    """
    Convert MM-DD text into a month/day tuple.
    """

    month, day = (
        str(value)
        .strip()
        .split("-")
    )

    return (
        int(month),
        int(day)
    )


def _in_period(
    target_date,
    start,
    end
):
    """
    Check whether a date falls inside an annual
    month/day period.

    Handles both normal and year-wrapping ranges.
    """

    target = (
        target_date.month,
        target_date.day
    )

    start_md = _month_day(start)
    end_md = _month_day(end)

    if start_md <= end_md:

        return (
            start_md
            <= target
            <= end_md
        )

    # Handles periods such as Nov-Feb.
    return (
        target >= start_md
        or
        target <= end_md
    )


def get_crop_context(
    target_date,
    crop="paddy"
):
    """
    Return crop-calendar context for a given date.

    Output:
        {
            "crop": ...,
            "season": ...,
            "crop_stage": ...,
            "harvest_window": ...
        }

    Returns None when no calendar entry matches.
    """

    if isinstance(
        target_date,
        str
    ):

        target_date = date.fromisoformat(
            target_date
        )

    crop = (
        crop
        .strip()
        .lower()
    )

    calendar = load_crop_calendar()

    for entry in calendar.get(
        "crops",
        []
    ):

        if (
            entry.get("crop", "")
            .strip()
            .lower()
            != crop
        ):
            continue


        variety_group = (
            entry.get(
                "variety_group"
            )
        )


        stages = entry.get(
            "stages",
            {}
        )

        for stage_name, stage_info in stages.items():
            if not isinstance(stage_info, dict):
                continue
            period = stage_info.get("approximate_period", {})
            start = period.get("start")
            end = period.get("end")
            if start and end and _in_period(target_date, start, end):
                return {
                    "crop": crop,
                    "season": variety_group,
                    "crop_stage": stage_name,
                    "harvest_window": (stage_name == "harvest"),
                }


    # --------------------------------------------------------
    # No matching stage
    # --------------------------------------------------------

    return {

        "crop":
            crop,

        "season":
            None,

        "crop_stage":
            None,

        "harvest_window":
            False,

    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        "CROP CALENDAR TEST"
    )

    print(
        "========================================"
    )


    test_dates = [

        "2026-09-20",

        "2026-10-10",

        "2026-11-15",

        "2026-12-20",

    ]


    for value in test_dates:

        context = get_crop_context(
            value,
            "paddy"
        )

        print(
            value,
            "→",
            context
        )