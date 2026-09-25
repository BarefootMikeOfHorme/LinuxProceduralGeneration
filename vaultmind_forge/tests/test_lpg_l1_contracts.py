"""Contract tests for the inert LPG-L1 lifecycle and wizard schemas.

These tests do not exercise any runtime behavior. The schemas they load are
deliberately inert: nothing in LPG reads or writes them yet. What is enforced
here is that the contracts themselves stay coherent, and that the safety rules
they claim to express are actually machine-enforced rather than only written
down in prose.

If a new schema is added to LPGL1/L1/schemas, it is picked up automatically.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "LPGL1" / "L1" / "schemas"
DRAFT_DIR = REPO_ROOT / "LPGL1" / "L1" / "drafts"

INERT_SCHEMAS = (
    "lifecycle-stage.schema.json",
    "scan-choice.schema.json",
    "install-task.schema.json",
    "install-plan.schema.json",
    "surface-binding.schema.json",
)


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _strip_jsonc(path: Path) -> dict:
    """Parse a JSONC draft by removing full-line // comments.

    Only full-line comments are stripped. The drafts deliberately avoid
    trailing inline comments so this stays a trivial transformation.
    """
    raw = path.read_text(encoding="utf-8")
    return json.loads(re.sub(r"^\s*//.*$", "", raw, flags=re.MULTILINE))


def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(_load_schema(name))


def _errors(validator: Draft202012Validator, document) -> list[str]:
    return [error.message for error in validator.iter_errors(document)]


# ---------------------------------------------------------------------------
# Meta-validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", sorted(SCHEMA_DIR.glob("*.schema.json")), ids=lambda p: p.name)
def test_every_schema_is_a_valid_draft_2020_12_schema(path):
    Draft202012Validator.check_schema(_load_schema(path.name))


@pytest.mark.parametrize("name", INERT_SCHEMAS, ids=lambda n: n)
def test_inert_schemas_declare_themselves_inert(name):
    """An inert contract must say so, so nobody mistakes it for live authority."""
    schema = _load_schema(name)

    assert "_comment" in schema, f"{name} must carry a _comment"
    assert "INERT" in schema["_comment"].upper()


def test_inert_schemas_are_not_part_of_the_promotion_evidence_set():
    """The inert contracts must not be reachable from the promotion gate.

    A partial or speculative wizard contract must never be able to satisfy the
    evidence requirement for promoting observed state.
    """
    promotion = _load_schema("promotion-evidence.schema.json")
    serialized = json.dumps(promotion)

    for name in INERT_SCHEMAS:
        assert name not in serialized


# ---------------------------------------------------------------------------
# Draft catalog
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def stage_catalog() -> dict:
    return _strip_jsonc(DRAFT_DIR / "stage-catalog.draft.jsonc")


@pytest.fixture(scope="module")
def wizard_examples() -> dict:
    return _strip_jsonc(DRAFT_DIR / "wizard-flow.examples.jsonc")["examples"]


def test_stage_catalog_covers_every_tier_in_order(stage_catalog):
    stages = stage_catalog["stages"]

    assert [stage["tier"] for stage in stages] == ["L1", "L1", "L2", "L3", "L4", "L5", "L6"]
    assert [stage["order"] for stage in stages] == list(range(len(stages)))


def test_stage_catalog_is_declared_inert_and_surface_neutral(stage_catalog):
    assert stage_catalog["status"] == "inert-draft"
    assert stage_catalog["default_surface"] == "windows-wizard"
    assert "windows-wizard" in stage_catalog["supported_surfaces"]
    assert len(stage_catalog["supported_surfaces"]) >= 3


@pytest.mark.parametrize("stage_id", [
    "lpg-l1.stage.l1.machine",
    "lpg-l1.stage.l1.profile",
    "lpg-l1.stage.l2.environment",
    "lpg-l1.stage.l3.programs",
    "lpg-l1.stage.l4.contracts",
    "lpg-l1.stage.l5.knowledge",
    "lpg-l1.stage.l6.content",
])
def test_every_catalog_stage_validates_against_the_stage_contract(stage_catalog, stage_id):
    stage = next(s for s in stage_catalog["stages"] if s["stage_id"] == stage_id)
    document = {
        "schema_version": stage_catalog["schema_version"],
        "profile": stage_catalog["profile"],
        **stage,
    }

    assert _errors(_validator("lifecycle-stage.schema.json"), document) == []


def test_every_stage_declares_at_least_one_exit_validation(stage_catalog):
    for stage in stage_catalog["stages"]:
        assert stage["exit_validation"], f"{stage['stage_id']} must define exit validation"


def test_a_failed_stage_may_not_be_marked_complete(stage_catalog):
    """Exit criteria carry observed results, and failure keeps the stage failed.

    This is the machine-readable form of "the wizard never says done here".
    """
    stage = next(s for s in stage_catalog["stages"] if s["tier"] == "L3")
    document = {
        "schema_version": stage_catalog["schema_version"],
        "profile": stage_catalog["profile"],
        **{k: v for k, v in stage.items() if k not in ("kind", "status")},
        "kind": "record",
        "status": "failed",
        "status_reasons": ["forge doctor failed: native module not importable"],
        "exit_validation": [
            {**criterion, "observed_result": "fail", "evidence": "forge-doctor.log"}
            for criterion in stage["exit_validation"]
        ],
    }

    assert _errors(_validator("lifecycle-stage.schema.json"), document) == []
    assert document["status"] != "complete"


# ---------------------------------------------------------------------------
# Scan choice: present is not the same as valid
# ---------------------------------------------------------------------------


def test_examples_cover_all_three_detection_states(wizard_examples):
    states = {choice["detection_state"] for choice in wizard_examples["scan_choices"]}

    assert {"present_and_valid", "present_invalid", "absent"} <= states


@pytest.mark.parametrize("index", [0, 1, 2])
def test_example_scan_choices_validate(wizard_examples, index):
    choice = wizard_examples["scan_choices"][index]

    assert _errors(_validator("scan-choice.schema.json"), choice) == []


def test_present_but_invalid_may_never_be_silently_skipped(wizard_examples):
    """The core rule.

    A present-but-incompatible component must be explained, not skipped, because
    silently skipping it is how a broken install ends up looking healthy.
    """
    invalid = next(
        c for c in wizard_examples["scan_choices"] if c["detection_state"] == "present_invalid"
    )
    validator = _validator("scan-choice.schema.json")

    assert invalid["skip_is_silent"] is False
    assert invalid["incompatibility_reasons"]
    assert invalid["explanation"]

    silent = {**invalid, "skip_is_silent": True}
    assert _errors(validator, silent), "silent skip of a present-invalid component must be rejected"

    unreasoned = {**invalid, "incompatibility_reasons": []}
    assert _errors(validator, unreasoned), "present_invalid without a reason must be rejected"


def test_present_and_valid_may_be_skipped_without_ceremony(wizard_examples):
    """Avoid-if-present is real, but only for components that are actually valid."""
    valid = next(
        c for c in wizard_examples["scan_choices"] if c["detection_state"] == "present_and_valid"
    )
    validator = _validator("scan-choice.schema.json")

    if valid["recommended_action"] == "skip":
        assert valid["skip_is_silent"] is True
    else:
        quiet_skip = {**valid, "recommended_action": "skip", "skip_is_silent": True}
        assert _errors(validator, quiet_skip) == []

        loud_skip = {**valid, "recommended_action": "skip", "skip_is_silent": False}
        assert _errors(validator, loud_skip), (
            "a valid component must not demand approval just to be left alone"
        )


def test_absent_component_must_state_what_capability_is_lost(wizard_examples):
    absent = next(c for c in wizard_examples["scan_choices"] if c["detection_state"] == "absent")
    validator = _validator("scan-choice.schema.json")

    assert absent["skip_is_silent"] is False
    for option in absent["options"]:
        assert option["consequences"], "every offered option must state its consequences"

    stripped = json.loads(json.dumps(absent))
    stripped["options"][0]["consequences"] = []
    assert _errors(validator, stripped)


def test_advisory_links_are_never_authority_and_never_consent(wizard_examples):
    validator = _validator("scan-choice.schema.json")

    for choice in wizard_examples["scan_choices"]:
        for link in choice["advisory_links"]:
            assert link["authority"] == "advisory"
            assert link["user_initiated"] is True

    choice = json.loads(json.dumps(wizard_examples["scan_choices"][0]))
    choice["advisory_links"] = [
        {"kind": "browser", "target": "https://example.invalid", "authority": "authority", "user_initiated": False}
    ]
    assert _errors(validator, choice)


# ---------------------------------------------------------------------------
# Install plan
# ---------------------------------------------------------------------------


def test_example_install_plan_validates(wizard_examples):
    assert _errors(_validator("install-plan.schema.json"), wizard_examples["install_plan"]) == []


def test_plan_from_a_partial_scan_is_forced_to_blocked(wizard_examples):
    validator = _validator("install-plan.schema.json")
    plan = json.loads(json.dumps(wizard_examples["install_plan"]))

    plan["scan_complete"] = False
    plan["plan_state"] = "awaiting-approval"
    assert _errors(validator, plan), "a partial scan must not produce an approvable plan"

    plan["plan_state"] = "blocked"
    assert _errors(validator, plan) == []


@pytest.mark.parametrize("disposition", ["skip", "already-satisfied", "blocked", "deferred"])
def test_every_task_that_will_not_run_must_say_why(wizard_examples, disposition):
    """A plan must never be indistinguishable from a silent failure."""
    validator = _validator("install-plan.schema.json")
    plan = json.loads(json.dumps(wizard_examples["install_plan"]))

    plan["stages"][1]["tasks"][0]["disposition"] = disposition
    plan["stages"][1]["tasks"][0]["reason"] = None
    assert _errors(validator, plan), f"a {disposition} task with no reason must be rejected"

    plan["stages"][1]["tasks"][0]["reason"] = "already satisfied by the validated baseline"
    assert _errors(validator, plan) == []


def test_a_running_task_must_not_carry_a_stale_reason(wizard_examples):
    """A reason belongs to dispositions that do something; run is self-evident."""
    validator = _validator("install-plan.schema.json")
    plan = json.loads(json.dumps(wizard_examples["install_plan"]))

    plan["stages"][1]["tasks"][0]["disposition"] = "run"
    plan["stages"][1]["tasks"][0]["reason"] = "left over from an earlier plan"
    assert _errors(validator, plan)


def test_plan_carries_git_source_lineage(wizard_examples):
    """Git is the source lineage anchor; a plan may not exist without one."""
    lineage = wizard_examples["install_plan"]["source_lineage"]

    assert lineage["commit"]
    assert lineage["dirty"] is False


def test_example_install_task_validates(wizard_examples):
    assert _errors(_validator("install-task.schema.json"), wizard_examples["install_task"]) == []


def test_install_task_approval_and_rollback_are_explicit(wizard_examples):
    task = wizard_examples["install_task"]

    assert task["requires_approval"] is True
    assert task["rollback"]["strategy"] != "none"
    assert task["rollback"]["verified"] is True
    assert task["dry_run"] is True
    assert task["validation"], "a task must declare how it will be validated"


# ---------------------------------------------------------------------------
# Surface binding: the wizard is not the authority
# ---------------------------------------------------------------------------


def test_example_surface_binding_validates(wizard_examples):
    binding = wizard_examples["surface_binding"]

    assert _errors(_validator("surface-binding.schema.json"), binding) == []


def test_windows_wizard_is_the_first_surface_but_not_the_authority(wizard_examples):
    binding = wizard_examples["surface_binding"]

    assert binding["surface"] == "windows-wizard"
    assert binding["surface_role"] == "presentation+input"
    assert "no-derive-authority" in binding["prohibitions"]
    assert "no-execute-discovered-code" in binding["prohibitions"]
    assert "no-silent-install" in binding["prohibitions"]


def test_surface_binding_points_at_the_authority_records(wizard_examples):
    binding = wizard_examples["surface_binding"]["binds_to"]

    assert binding["plan_schema"] == "al1.schema.lpg-l1.install-plan"
    assert binding["choice_schema"] == "al1.schema.lpg-l1.scan-choice"
    assert binding["task_schema"] == "al1.schema.lpg-l1.install-task"
    assert binding["plan_id"]


def test_wizard_authorization_shows_consequences_before_consent(wizard_examples):
    authorization = wizard_examples["surface_binding"]["authorization"]

    assert authorization["requires_explicit_approval"] is True
    assert "approve" in authorization["options"]
    assert "cancel" in authorization["options"]
    for required in ("changes", "locations", "validation", "rollback"):
        assert required in authorization["shows"], f"authorization popup must show {required}"


def test_wizard_reacts_to_failure_without_claiming_completion(wizard_examples):
    updates = {u["event"]: u for u in wizard_examples["surface_binding"]["dynamic_updates"]}

    assert "validation-failed" in updates
    failure = updates["validation-failed"]
    assert failure["replan"] is True
    assert "incomplete" in failure["effect"].lower()


def test_wizard_help_is_user_initiated_and_advisory(wizard_examples):
    validator = _validator("surface-binding.schema.json")

    for entry in wizard_examples["surface_binding"]["help"]:
        assert entry["authority"] == "advisory"
        assert entry["user_initiated"] is True

    binding = json.loads(json.dumps(wizard_examples["surface_binding"]))
    binding["help"][0]["user_initiated"] = False
    assert _errors(validator, binding), "a surface may not open help on the user's behalf"

    binding = json.loads(json.dumps(wizard_examples["surface_binding"]))
    binding["help"][0]["authority"] = "authority"
    assert _errors(validator, binding), "help may never be typed as authority"


def test_a_surface_may_not_opt_out_of_a_prohibition(wizard_examples):
    """Omitting a rule is not the same as declaring it.

    A surface that simply leaves a prohibition out must be rejected, otherwise
    the safest contract is also the shortest one.
    """
    validator = _validator("surface-binding.schema.json")
    binding = json.loads(json.dumps(wizard_examples["surface_binding"]))

    binding["prohibitions"] = ["no-derive-authority"]
    assert _errors(validator, binding), "a partial prohibition set must be rejected"

    binding["prohibitions"] = [
        "no-derive-authority",
        "no-execute-discovered-code",
        "no-silent-install",
        "no-silent-downgrade",
        "no-secret-read",
        "no-unapproved-network",
        "no-derive-authority",
    ]
    assert _errors(validator, binding), "duplicate prohibitions must be rejected"

    binding["prohibitions"] = [
        "no-derive-authority",
        "no-execute-discovered-code",
        "no-silent-install",
        "no-silent-downgrade",
        "no-secret-read",
        "no-unapproved-network",
        "trust-the-ui",
    ]
    assert _errors(validator, binding), "an unknown prohibition must be rejected"
