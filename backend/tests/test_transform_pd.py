import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "transform_pd.py"


def run_transform_pd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_transform_pd_can_render_user_mgmt_to_stdout():
    result = run_transform_pd("--feature", "master", "--module", "pd-user-mgmt", "--stdout")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "module_key: user-mgmt" in result.stdout
    assert "page_id: user-mgmt.index" in result.stdout
    assert "CAP-UM-INDEX-001" in result.stdout
    assert "instructional" in result.stdout
    assert "ui-capability" in result.stdout
    assert "page_boundary: main-page" in result.stdout
    assert "当前模块已覆盖对应 spec.md 范围" in result.stdout


def test_transform_pd_can_write_ai_pd_files(tmp_path: Path):
    output_dir = tmp_path / "ai-pd"

    result = run_transform_pd(
        "--feature",
        "master",
        "--module",
        "pd-user-mgmt",
        "--output-dir",
        str(output_dir),
    )

    assert result.returncode == 0, result.stderr or result.stdout

    readme_path = output_dir / "README.md"
    module_path = output_dir / "ai-user-mgmt.md"
    checklist_path = output_dir / "ai-user-mgmt.checklist.md"

    assert readme_path.exists()
    assert module_path.exists()
    assert checklist_path.exists()
    assert "ai-user-mgmt.md" in readme_path.read_text(encoding="utf-8")
    assert "ai-user-mgmt.checklist.md" in readme_path.read_text(encoding="utf-8")
    assert "pilot" in readme_path.read_text(encoding="utf-8")
    module_text = module_path.read_text(encoding="utf-8")
    checklist_text = checklist_path.read_text(encoding="utf-8")
    assert "CAP-UM-INDEX-001" in module_text
    assert "page_boundary: main-page" in module_text
    assert "当前模块已覆盖对应 spec.md 范围" in module_text
    assert "AI-PD 人工校对清单: user-mgmt" in checklist_text
    assert "模块级必查项" in checklist_text
    assert "### user-mgmt.index" in checklist_text
    assert "校对时必须直接修改 `ai-user-mgmt.md`" in checklist_text
    assert "不是“是否已修改完成”的状态记录" in checklist_text


def test_transform_pd_can_extract_multi_page_intent_library_ai_pd_semantics(tmp_path: Path):
    output_dir = tmp_path / "ai-pd"
    result = run_transform_pd(
        "--feature",
        "master",
        "--module",
        "pd-intent-library",
        "--output-dir",
        str(output_dir),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    module_text = (output_dir / "ai-intent-library.md").read_text(encoding="utf-8")
    assert "page_id: intent-library.detail" in module_text
    assert "page_id: intent-library.datasets" in module_text
    assert "page_id: intent-library.dataset-detail" in module_text
    assert "page_id: intent-library.test" in module_text
    assert "page_boundary: sub-page" in module_text
    assert "parent_page: intent-library.datasets" in module_text
    assert "意图配置 Drawer" in module_text
    assert "批量导入实体" in module_text
    assert "保存意图" in module_text
    assert "FR-050" in module_text
    assert "| `HID-DATASET_DETAIL-001` | `drawer-or-modal` | `ui-capability` | 意图配置 Drawer | 意图配置 Drawer |" in module_text
    assert "| `HID-DATASET_DETAIL-006` | `drawer-or-modal` | `instructional` | 数据模型 / 批量导入说明 / 易错点标签页 | 数据模型 / 批量导入说明 / 易错点标签页 |" in module_text
    assert "user-mgmt.index" not in module_text
    assert "浏览用户目录与统计卡" not in module_text
    assert "启停用账号" not in module_text

    dataset_overview = module_text.split("## Page: intent-library.dataset-detail", 1)[1].split("### visible_ui", 1)[0]
    datasets_overview = module_text.split("## Page: intent-library.datasets", 1)[1].split("### visible_ui", 1)[0]
    test_overview = module_text.split("## Page: intent-library.test", 1)[1].split("### visible_ui", 1)[0]
    assert "goal: 维护意图、词槽、实体和问法数据，并确保保存/导入结果真实回读" in dataset_overview
    assert "- 进入数据管理页 → 保存意图配置 → 列表回读最新值" in dataset_overview
    assert "goal: 统一管理指令库的训练数据集和评估数据集，支持手工创建和 LLM 合成扩充" in datasets_overview
    assert "- 点击 LLM 合成 → 选择数据集/模型/样本数/提示词 → 提交 → 展示生成结果条数" in datasets_overview
    assert "goal: 验证模型推理质量，通过单条对话式测试和库内批量评估确认模型可用性" in test_overview
    assert "- 选择模型 → 新建会话 → 输入测试文本 → 发送 → 查看意图/置信度/槽位/耗时" in test_overview

    fr_mapping_section = module_text.split("## fr_mapping", 1)[1]
    fr_rows = [line for line in fr_mapping_section.splitlines() if line.startswith("| `CAP-")]
    assert len(fr_rows) == len(set(fr_rows))


def test_transform_pd_can_generate_remaining_modules_without_scope_pollution(tmp_path: Path):
    output_dir = tmp_path / "ai-pd"
    result = run_transform_pd("--feature", "master", "--output-dir", str(output_dir))

    assert result.returncode == 0, result.stderr or result.stdout

    knowledge_text = (output_dir / "ai-knowledge-base.md").read_text(encoding="utf-8")
    knowledge_checklist = (output_dir / "ai-knowledge-base.checklist.md").read_text(encoding="utf-8")
    assert "- **覆盖 FR**: FR-004, FR-005, FR-006" in knowledge_text
    assert "parent_page: knowledge-base.index" in knowledge_text
    assert "page_id: knowledge-base.index" in knowledge_text
    assert "parent_page: none" in knowledge_text
    assert "### knowledge-base.index" in knowledge_checklist

    dialog_text = (output_dir / "ai-dialog-profile.md").read_text(encoding="utf-8")
    dialog_checklist = (output_dir / "ai-dialog-profile.checklist.md").read_text(encoding="utf-8")
    assert "- **覆盖 FR**: FR-007, FR-008, FR-009, FR-010, FR-011, FR-015, FR-016, FR-040, FR-047" in dialog_text
    assert "parent_page: dialog-profile.index" in dialog_text
    assert "parent_page: dialog-profile.detail" in dialog_text
    assert "进入平台级批量测试" in dialog_text
    assert "FR-012" not in dialog_text.split("## 模块摘要", 1)[1].split("## 页面索引", 1)[0]
    assert "### dialog-profile.detail" in dialog_checklist

    batch_text = (output_dir / "ai-batch-test.md").read_text(encoding="utf-8")
    batch_checklist = (output_dir / "ai-batch-test.checklist.md").read_text(encoding="utf-8")
    assert "- **覆盖 FR**: FR-012, FR-013, FR-014" in batch_text
    assert batch_text.count("当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。") == 1
    assert "parent_page: batch-test.index" in batch_text
    assert "### batch-test.detail" in batch_checklist

    monitoring_text = (output_dir / "ai-monitoring.md").read_text(encoding="utf-8")
    monitoring_checklist = (output_dir / "ai-monitoring.checklist.md").read_text(encoding="utf-8")
    assert "- **覆盖 FR**: FR-030, FR-031, FR-032, FR-034, FR-035, FR-038" in monitoring_text
    assert "parent_page: monitoring.index" in monitoring_text
    assert "配置告警规则" in monitoring_text
    assert "### monitoring.index" in monitoring_checklist


def test_transform_pd_fails_fast_when_pd_page_semantics_are_missing(tmp_path: Path):
    feature_name = "_tmp_missing_page_semantics"
    feature_dir = REPO_ROOT / "specs" / feature_name
    module_dir = feature_dir / "pd-all" / "pd-knowledge-base"
    source_dir = REPO_ROOT / "specs" / "master" / "pd-all" / "pd-knowledge-base"

    if feature_dir.exists():
        shutil.rmtree(feature_dir)

    try:
        module_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, module_dir)

        readme_path = module_dir / "README.md"
        readme_text = readme_path.read_text(encoding="utf-8")
        broken_text = readme_text.replace("- `page_goal`: 预览文档解析内容并验证检索质量，确认索引后知识可被正确命中\n", "", 1)
        readme_path.write_text(broken_text, encoding="utf-8")

        result = run_transform_pd("--feature", feature_name, "--module", "pd-knowledge-base", "--output-dir", str(tmp_path / "ai-pd"))

        assert result.returncode != 0
        combined_output = f"{result.stdout}\n{result.stderr}"
        assert "GATE-PD-003" in combined_output
        assert "detail.html" in combined_output
        assert "page_goal" in combined_output
    finally:
        if feature_dir.exists():
            shutil.rmtree(feature_dir)
