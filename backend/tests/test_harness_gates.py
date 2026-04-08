import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_pwsh_json(*args: str) -> dict:
    result = subprocess.run(
        ["pwsh", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def test_implement_gate_uses_module_plan_for_current_intent_module():
    payload = run_pwsh_json(
        "-File",
        ".specify/scripts/powershell/validate-stage-gates.ps1",
        "-Stage",
        "implement",
        "-Module",
        "pd-intent-library",
        "-Json",
    )

    assert payload["status"] == "warning"
    assert not any(issue["code"] == "GATE-PLAN-001" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-PLAN-003" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-PLAN-004" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-PD-003" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-AIPD-001" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-AIPD-002" for issue in payload["issues"])
    assert any(issue["code"] == "GATE-PD-002" for issue in payload["issues"])


def test_tasks_gate_uses_exact_module_ai_spec_for_user_mgmt():
    payload = run_pwsh_json(
        "-File",
        ".specify/scripts/powershell/validate-stage-gates.ps1",
        "-Stage",
        "tasks",
        "-Module",
        "pd-user-mgmt",
        "-Json",
    )

    assert payload["status"] == "warning"
    assert not any(issue["code"] == "GATE-PLAN-001" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-PLAN-002" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-PLAN-003" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-PLAN-004" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-PD-003" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-AIPD-001" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-AIPD-002" for issue in payload["issues"])
    assert not any(issue["code"] == "GATE-MODULE-007" for issue in payload["issues"])
    assert any(issue["code"] == "GATE-PD-002" for issue in payload["issues"])


def test_check_prerequisites_can_resolve_required_module_plan_path():
    result = subprocess.run(
        [
            "pwsh",
            "-File",
            ".specify/scripts/powershell/check-prerequisites.ps1",
            "-Json",
            "-RequirePlan",
            "-Module",
            "pd-intent-library",
            "-PathsOnly",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    normalized = payload["IMPL_PLAN"].replace("\\", "/")
    assert normalized.endswith("specs/master/plans/plan-intent-library.md")
    ai_pd_normalized = payload["AI_PD_DIR"].replace("\\", "/")
    assert ai_pd_normalized.endswith("specs/master/ai-pd")
    assert payload["REQUESTED_MODULE"] == "pd-intent-library"


def test_critical_modules_declare_page_route_and_capability_parity_probes():
    rollout_path = REPO_ROOT / ".specify" / "harness" / "module-rollout.json"
    rollout = json.loads(rollout_path.read_text(encoding="utf-8"))

    required_probes = {"page_boundary_parity", "route_navigation_chain", "capability_parity"}
    critical_modules = [module for module in rollout["modules"] if module.get("critical")]

    assert critical_modules
    for module in critical_modules:
        probes = set(module["browser_stage"]["quality_probes"])
        missing = required_probes - probes
        assert not missing, f"{module['module_key']} missing {sorted(missing)}"


def test_each_ai_pd_module_has_matching_manual_checklist():
    ai_pd_dir = REPO_ROOT / "specs" / "master" / "ai-pd"
    module_files = sorted(path for path in ai_pd_dir.glob("ai-*.md") if not path.name.endswith(".checklist.md"))

    assert module_files
    for module_file in module_files:
        checklist_path = module_file.with_name(module_file.stem + ".checklist.md")
        assert checklist_path.exists(), f"missing checklist for {module_file.name}"


def test_each_pd_readme_has_page_goal_and_primary_user_flows_for_every_html_page():
    pd_all_dir = REPO_ROOT / "specs" / "master" / "pd-all"
    module_dirs = sorted(path for path in pd_all_dir.iterdir() if path.is_dir() and path.name.startswith("pd-"))

    assert module_dirs
    for module_dir in module_dirs:
        readme_text = (module_dir / "README.md").read_text(encoding="utf-8")
        html_names = sorted(path.name for path in module_dir.glob("*.html"))
        assert html_names, f"{module_dir.name} has no html pages"

        for html_name in html_names:
            marker = f"### {html_name}"
            assert marker in readme_text, f"{module_dir.name} missing section for {html_name}"
            section = readme_text.split(marker, 1)[1]
            next_section_markers = [idx for idx in (section.find("\n### "), section.find("\n## ")) if idx != -1]
            if next_section_markers:
                section = section[: min(next_section_markers)]
            assert "`page_goal`" in section, f"{module_dir.name}:{html_name} missing page_goal"
            assert "`primary_user_flows`" in section, f"{module_dir.name}:{html_name} missing primary_user_flows"


def test_implement_gate_requires_manual_ai_pd_checklist_without_false_positive():
    payload = run_pwsh_json(
        "-File",
        ".specify/scripts/powershell/validate-stage-gates.ps1",
        "-Stage",
        "implement",
        "-Module",
        "pd-intent-library",
        "-Json",
    )

    assert not any(issue["code"] == "GATE-MODULE-007" for issue in payload["issues"])
