import pytest
from unittest.mock import Mock, call
from genesys_code_compare.analyze import ActivityCodeAnalyze
from genesys_code_compare.models.genesys import ActivityCode, BusinessUnit
from genesys_code_compare.models.analyze import MatchResult, CodePresence
from genesys_code_compare.cli import CLI


def make_code(
    bu_id: str, name: str, category: str, default_code: bool = False
) -> ActivityCode:
    return ActivityCode(
        ac_id=f"{bu_id}-{name.lower().replace(' ', '-')}",
        name=name,
        category=category,
        default_code=default_code,
        default_name_changed=False,
    )


@pytest.fixture
def cli():
    return Mock(spec=CLI)


@pytest.fixture
def analyzer(cli):
    return ActivityCodeAnalyze(cli)


@pytest.fixture
def business_units(analyzer) -> list[BusinessUnit]:
    """Return fresh objects so experiments do not affect later calls."""
    return [
        BusinessUnit(
            bu_id="bu-a",
            name="BU A",
            activity_codes=(
                make_code("bu-a", "Lunch", "Meal", True),
                make_code("bu-a", "Break", "Break", True),
                make_code("bu-a", "Training", "Training"),
                make_code("bu-a", "Meeting", "Meeting", True),
                make_code("bu-a", "Coaching", "Training"),
                make_code("bu-a", "Project Work", "OnQueueWork"),
                make_code("bu-a", "Admin", "OffQueueWork"),
            ),
        ),
        BusinessUnit(
            bu_id="bu-b",
            name="BU B",
            activity_codes=(
                make_code("bu-b", "Lunch", "Meal", True),
                make_code("bu-b", "Break", "Break", True),
                make_code("bu-b", "Training", "Meeting"),
                make_code("bu-b", "Meeting", "Meeting", False),
                make_code("bu-b", "Coaching", "Training"),
                make_code("bu-b", "Team Huddle", "Meeting"),
            ),
        ),
        BusinessUnit(
            bu_id="bu-c",
            name="BU C",
            activity_codes=(
                make_code("bu-c", "Lunch", "Meal", True),
                make_code("bu-c", "Break", "Break", True),
                make_code("bu-c", "Training", "Training"),
                make_code("bu-c", "Meeting", "Meeting", True),
                make_code("bu-c", "Project Work", "OffQueueWork"),
                make_code("bu-c", "System Outage", "Unavailable"),
            ),
        ),
    ]


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("exact_name_matches", ["Break", "Lunch", "Meeting", "Training"]),
        ("exact_field_matches", ["Break", "Lunch"]),
        ("field_differences", ["Meeting", "Training"]),
        ("partial_matches", ["Coaching", "Project Work"]),
        ("unique", ["Admin", "System Outage", "Team Huddle"]),
    ],
)
def test_analyze_classifies_codes(analyzer, business_units, category, expected):
    result = analyzer.analyze(business_units)

    assert [entry.name for entry in getattr(result, category)] == expected


@pytest.mark.parametrize(
    ("category", "name", "present", "missing"),
    [
        ("exact_field_matches", "Lunch", ["BU A", "BU B", "BU C"], []),
        ("field_differences", "Training", ["BU A", "BU B", "BU C"], []),
        ("partial_matches", "Coaching", ["BU A", "BU B"], ["BU C"]),
        ("partial_matches", "Project Work", ["BU A", "BU C"], ["BU B"]),
        ("unique", "Admin", ["BU A"], ["BU B", "BU C"]),
        ("unique", "Team Huddle", ["BU B"], ["BU A", "BU C"]),
        ("unique", "System Outage", ["BU C"], ["BU A", "BU B"]),
    ],
)
def test_analyze_preserves_presence_and_activity_data(
    analyzer, business_units, category, name, present, missing
):
    result = analyzer.analyze(business_units)
    entry = next(item for item in getattr(result, category) if item.name == name)

    assert sorted(entry.present_in) == present
    assert entry.missing_from == missing
    for bu in business_units:
        if bu.name in present:
            original = next(code for code in bu.activity_codes if code.name == name)
            assert entry.present_in[bu.name] is original


@pytest.mark.parametrize(
    "business_units",
    [[], [BusinessUnit(bu_id="empty", name="Empty BU")]],
)
def test_analyze_without_codes_returns_empty_results(analyzer, business_units):
    result = analyzer.analyze(business_units)

    assert result.exact_name_matches == []
    assert result.exact_field_matches == []
    assert result.field_differences == []
    assert result.partial_matches == []
    assert result.unique == []


def test_analyze_exact_matching_code(analyzer):
    code_a = make_code("bu-a", "Lunch", "Meal", True)
    code_b = make_code("bu-b", "Lunch", "Meal", True)

    business_units = [
        BusinessUnit(
            bu_id="bu-a",
            name="BU A",
            activity_codes=(code_a,),
        ),
        BusinessUnit(
            bu_id="bu-b",
            name="BU B",
            activity_codes=(code_b,),
        ),
    ]

    presence = CodePresence(
        name="Lunch",
        present_in={"BU A": code_a, "BU B": code_b},
        missing_from=[],
    )

    expected = MatchResult(
        exact_name_matches=[presence],
        exact_field_matches=[presence],
        field_differences=[],
        partial_matches=[],
        unique=[],
    )

    actual = analyzer.analyze(business_units)

    assert actual == expected


def test_analyze_un_matching_code(analyzer):
    code_a = make_code("bu-a", "Lunch 1", "Meal", True)
    code_b = make_code("bu-b", "Lunch", "Meal", True)

    business_units = [
        BusinessUnit(
            bu_id="bu-a",
            name="BU A",
            activity_codes=(code_a,),
        ),
        BusinessUnit(
            bu_id="bu-b",
            name="BU B",
            activity_codes=(code_b,),
        ),
    ]

    presence_1 = CodePresence(
        name="Lunch 1",
        present_in={"BU A": code_a},
        missing_from=["BU B"],
    )
    presence_2 = CodePresence(
        name="Lunch",
        present_in={"BU B": code_b},
        missing_from=["BU A"],
    )

    expected = MatchResult(
        exact_name_matches=[],
        exact_field_matches=[],
        field_differences=[],
        partial_matches=[],
        unique=[presence_2, presence_1],
    )

    actual = analyzer.analyze(business_units)

    assert actual == expected


def test_analyze_un_matching_detail_fields(analyzer):
    code_a = make_code("bu-a", "Lunch", "Meal", True)
    code_b = make_code("bu-b", "Lunch", "Break", True)

    business_units = [
        BusinessUnit(
            bu_id="bu-a",
            name="BU A",
            activity_codes=(code_a,),
        ),
        BusinessUnit(
            bu_id="bu-b",
            name="BU B",
            activity_codes=(code_b,),
        ),
    ]

    presence_1 = CodePresence(
        name="Lunch",
        present_in={"BU A": code_a, "BU B": code_b},
        missing_from=[],
    )

    expected = MatchResult(
        exact_name_matches=[
            presence_1,
        ],
        exact_field_matches=[],
        field_differences=[
            presence_1,
        ],
        partial_matches=[],
        unique=[],
    )

    actual = analyzer.analyze(business_units)

    assert actual == expected


def test_analyze_partial_match(analyzer, cli):
    code_a = make_code("bu-a", "Lunch", "Meal", True)
    code_b = make_code("bu-b", "Lunch", "Meal", True)
    code_c = make_code("bu-c", "Break", "Break", False)

    business_units = [
        BusinessUnit(
            bu_id="bu-a",
            name="BU A",
            activity_codes=(code_a,),
        ),
        BusinessUnit(
            bu_id="bu-b",
            name="BU B",
            activity_codes=(code_b,),
        ),
        BusinessUnit(
            bu_id="bu-c",
            name="BU C",
            activity_codes=(code_c,),
        ),
    ]

    presence_1 = CodePresence(
        name="Lunch",
        present_in={"BU A": code_a, "BU B": code_b},
        missing_from=["BU C"],
    )

    presence_2 = CodePresence(
        name="Break",
        present_in={"BU C": code_c},
        missing_from=["BU A", "BU B"],
    )

    expected = MatchResult(
        exact_name_matches=[],
        exact_field_matches=[],
        field_differences=[],
        partial_matches=[presence_1],
        unique=[presence_2],
    )

    actual = analyzer.analyze(business_units)

    assert actual == expected


def test_analyze_unique_match(analyzer, cli):
    code_a = make_code("bu-a", "Lunch", "Meal", True)
    code_b = make_code("bu-b", "Lunch", "Meal", True)
    code_c = make_code("bu-c", "Break", "Break", False)
    code_d = make_code("bu-d", "Vacation", "Holiday", False)

    business_units = [
        BusinessUnit(
            bu_id="bu-a",
            name="BU A",
            activity_codes=(code_a,),
        ),
        BusinessUnit(
            bu_id="bu-b",
            name="BU B",
            activity_codes=(code_b,),
        ),
        BusinessUnit(
            bu_id="bu-c",
            name="BU C",
            activity_codes=(code_c,),
        ),
        BusinessUnit(
            bu_id="bu-d",
            name="BU D",
            activity_codes=(code_d,),
        ),
    ]

    presence_1 = CodePresence(
        name="Lunch",
        present_in={"BU A": code_a, "BU B": code_b},
        missing_from=["BU C", "BU D"],
    )

    presence_2 = CodePresence(
        name="Break",
        present_in={"BU C": code_c},
        missing_from=["BU A", "BU B", "BU D"],
    )
    presence_3 = CodePresence(
        name="Vacation",
        present_in={"BU D": code_d},
        missing_from=["BU A", "BU B", "BU C"],
    )

    expected = MatchResult(
        exact_name_matches=[],
        exact_field_matches=[],
        field_differences=[],
        partial_matches=[presence_1],
        unique=[presence_2, presence_3],
    )

    actual = analyzer.analyze(business_units)
    cli.print_info.assert_called_once_with(
        "Starting to Analyze Business Units Activity Codes."
    )
    cli.print_status.assert_has_calls(
        [
            call("Completed Analyzing Business Unit's Activity Codes."),
            call("Exact Name Matches: 0"),
            call("Exact Partial Matches: 1"),
            call("Exact Unique Codes: 2"),
        ]
    )

    assert actual == expected
