#!/usr/bin/env python3
"""Semi-automatic HumanPD -> AI-PD transformer."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_module_key(module: str) -> str:
    return module[3:] if module.startswith("pd-") else module


def module_code(module_key: str) -> str:
    return "".join(part[0].upper() for part in re.split(r"[^a-zA-Z0-9]+", module_key) if part)


def page_code(page_name: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", page_name.upper()).strip("_")


def compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_frs(text: str) -> list[str]:
    frs: set[str] = set()
    pattern = re.compile(r"FR-(\d{3})(?:\s*[~-]\s*(?:FR-)?(\d{3}))?")
    for start, end in pattern.findall(text):
        if end:
            start_num = int(start)
            end_num = int(end)
            step = 1 if start_num <= end_num else -1
            for value in range(start_num, end_num + step, step):
                frs.add(f"FR-{value:03d}")
        else:
            frs.add(f"FR-{int(start):03d}")
    return sorted(frs)


def extract_covered_frs(readme_text: str) -> list[str]:
    match = re.search(
        r"##\s*需求追溯矩阵\s*\(FR\s*→\s*PD\)\s*(.*?)(?:\n##\s+|\Z)",
        readme_text,
        re.S,
    )
    if not match:
        return parse_frs(readme_text)

    frs: set[str] = set()
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 5 or cells[0] in {"FR 编号", "---------"}:
            continue
        status = cells[4]
        if status.startswith("🔲"):
            continue
        frs.update(parse_frs(cells[0]))
    return sorted(frs)


def extract_page_rows(readme_text: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for line in readme_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0].endswith(".html"):
            continue
        rows[cells[0]] = {
            "type": cells[1],
            "sider": cells[2],
            "back": cells[3],
            "drawer": cells[4],
        }
    return rows


def extract_navigation_parents(readme_text: str) -> dict[str, str]:
    parents: dict[str, str] = {}
    nav_match = re.search(
        r"(?:\*\*导航逻辑\*\*[:：]|##\s*导航逻辑)\s*```(.*?)```",
        readme_text,
        re.S | re.I,
    )
    nav_text = nav_match.group(1) if nav_match else ""
    for source, target in re.findall(r"([a-z0-9-]+\.html).*?→.*?([a-z0-9-]+\.html)", nav_text, re.I):
        if target not in parents:
            parents[target] = source
    return parents


def extract_page_semantics(readme_text: str) -> dict[str, dict[str, object]]:
    semantics: dict[str, dict[str, object]] = {}
    section_pattern = re.compile(
        r"###\s+([a-z0-9-]+\.html)\s*\n(.*?)(?=\n###\s+[a-z0-9-]+\.html|\n##\s+|\Z)",
        re.S | re.I,
    )
    for page_name, body in section_pattern.findall(readme_text):
        page_data: dict[str, object] = {}
        current_key: str | None = None
        current_items: list[str] = []
        for raw_line in body.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            if not stripped:
                continue

            indent = len(raw_line) - len(raw_line.lstrip(" "))
            key_match = re.match(r"-\s+`([^`]+)`:\s*(.*)", stripped)
            if key_match and indent == 0:
                if current_key is not None:
                    page_data[current_key] = current_items[:]
                current_key = key_match.group(1)
                first_value = compact_whitespace(key_match.group(2))
                current_items = [first_value] if first_value else []
                continue

            if stripped.startswith("- "):
                item = compact_whitespace(stripped[2:])
                if current_key is not None and item:
                    current_items.append(item)

        if current_key is not None:
            page_data[current_key] = current_items[:]

        if page_data:
            semantics[page_name] = page_data
    return semantics


def find_missing_page_semantic_anchors(
    readme_text: str,
    html_pages: dict[str, str],
) -> list[dict[str, object]]:
    page_semantics = extract_page_semantics(readme_text)
    missing_items: list[dict[str, object]] = []

    for page_name in sorted(html_pages):
        semantic_page = page_semantics.get(page_name, {})
        missing_fields: list[str] = []
        if not get_semantic_entries(semantic_page, "page_goal", "goal"):
            missing_fields.append("page_goal")
        if not get_semantic_entries(semantic_page, "primary_user_flows", "page_flows", "user_flows"):
            missing_fields.append("primary_user_flows")
        if missing_fields:
            missing_items.append(
                {
                    "page_name": page_name,
                    "missing_fields": missing_fields,
                }
            )

    return missing_items


def format_missing_page_semantic_anchors(module_dir: Path, missing_items: list[dict[str, object]]) -> str:
    details = "\n".join(
        f"- {item['page_name']}: 缺少 {', '.join(item['missing_fields'])}"
        for item in missing_items
    )
    return (
        f"GATE-PD-003: `{module_dir / 'README.md'}` 缺少页面级 `page_goal / primary_user_flows`，"
        "transform-pd 已停止。请先补齐 HumanPD 再重新生成 AI-PD。\n"
        f"{details}"
    )


def extract_success_standard(readme_text: str) -> str:
    match = re.search(r"\*\*成功标准\*\*[:：](.+)", readme_text)
    return compact_whitespace(match.group(1)) if match else "关键操作必须有真实回读结果"


def extract_use_cases(readme_text: str) -> list[str]:
    match = re.search(r"\*\*使用场景\*\*[:：]\s*(.*?)(?:\n-\s+\*\*成功标准\*\*|\n## |\Z)", readme_text, re.S)
    if not match:
        return []

    use_cases = []
    for line in match.group(1).splitlines():
        cleaned = compact_whitespace(re.sub(r"^\d+\.\s*", "", line.strip()))
        if cleaned:
            use_cases.append(cleaned)
    return use_cases


def get_semantic_entries(page_data: dict[str, object], *keys: str) -> list[str]:
    for key in keys:
        entries = page_data.get(key, [])
        if not isinstance(entries, list):
            continue
        normalized_entries = [compact_whitespace(str(entry)) for entry in entries if compact_whitespace(str(entry))]
        if normalized_entries:
            return normalized_entries
    return []


def clean_semantic_entry(value: str) -> str:
    return compact_whitespace(re.sub(r"`([^`]+)`", r"\1", value))


def extract_action_name_and_detail(entry: str) -> tuple[str, str]:
    normalized = clean_semantic_entry(entry)
    action, _, detail = normalized.partition(":")
    return action.strip(), detail.strip()


def pick_representative_items(items: list[str], *, max_items: int = 2) -> list[str]:
    normalized = []
    seen = set()
    for item in items:
        cleaned = compact_whitespace(item)
        if cleaned and cleaned not in seen:
            normalized.append(cleaned)
            seen.add(cleaned)

    generic_items = {"查看页面主数据", "编辑当前项", "删除当前项", "完成页面主要操作"}
    preferred = [item for item in normalized if item not in generic_items]
    chosen = preferred or normalized
    return chosen[:max_items]


def infer_page_goal(
    *,
    page_name: str,
    semantic_page: dict[str, object],
    capabilities: list[dict[str, str]],
    actions: list[dict[str, str]],
) -> str:
    explicit_goal = get_semantic_entries(semantic_page, "page_goal", "goal")
    if explicit_goal:
        return clean_semantic_entry(explicit_goal[0])

    semantic_capabilities = [clean_semantic_entry(entry) for entry in get_semantic_entries(semantic_page, "capability_checklist")]
    action_titles = [item["action"] for item in actions if item["action"] != "无需显式动作契约"]
    capability_titles = semantic_capabilities or [item["title"] for item in capabilities]
    representatives = pick_representative_items(action_titles + capability_titles, max_items=2)

    if len(representatives) >= 2:
        return f"围绕{representatives[0]}、{representatives[1]}等关键动作完成{page_name}页闭环，并确保结果真实回读"
    if len(representatives) == 1:
        return f"围绕{representatives[0]}完成{page_name}页核心闭环，并确保结果真实回读"
    return f"完成{page_name}页的核心操作，并确保结果真实回读"


def infer_primary_user_flows(
    *,
    page_name: str,
    semantic_page: dict[str, object],
    actions: list[dict[str, str]],
    capabilities: list[dict[str, str]],
) -> list[str]:
    explicit_flows = [clean_semantic_entry(entry) for entry in get_semantic_entries(semantic_page, "primary_user_flows", "page_flows", "user_flows")]
    if explicit_flows:
        return explicit_flows

    semantic_actions = get_semantic_entries(semantic_page, "action_contracts")
    if semantic_actions:
        flows = []
        for entry in semantic_actions[:3]:
            action, detail = extract_action_name_and_detail(entry)
            if not action:
                continue
            success_detail = detail or f"{action} 的结果必须真实回读"
            flows.append(f"在{page_name}页执行 {action} → {success_detail}")
        if flows:
            return flows

    generic_actions = {"编辑当前项", "删除当前项", "查看页面主数据", "完成页面主要操作"}
    action_items = [action for action in actions if action["action"] != "无需显式动作契约"]
    preferred_action_items = [action for action in action_items if action["action"] not in generic_actions]
    action_flows = []
    for action in preferred_action_items or action_items:
        action_flows.append(f"进入{page_name}页 → {action['action']} → {action['success_signal']}")
    if action_flows:
        return action_flows[:3]

    capability_flows = []
    for capability in capabilities:
        capability_flows.append(f"进入{page_name}页 → {capability['title']} → {capability['done_signal']}")
    return capability_flows[:2] or [f"进入{page_name}页 → 完成核心操作 → 结果以真实回读或明确反馈收敛"]


def extract_out_of_scope(readme_text: str) -> list[str]:
    match = re.search(r"\*\*范围外 FR\*\*[:：]\s*(.*?)(?:\n\*\*跨模块引用\*\*|\n## |\Z)", readme_text, re.S)
    if not match:
        return ["当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。"]

    rows = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3 or cells[0] in {"FR 编号", "---------"}:
            continue
        if cells[0] == "无":
            rows.append(cells[1])
        else:
            rows.append(f"{cells[0]}: {cells[1]}（{cells[2]}）")

    return rows or ["当前模块未声明额外范围外 FR。"]


def map_page_boundary(page_type: str) -> str:
    normalized = compact_whitespace(page_type)
    if "主导航" in normalized:
        return "main-page"
    if "下级" in normalized:
        return "sub-page"
    return "page"


def normalize_semantic_boundary(value: str) -> str:
    normalized = compact_whitespace(value)
    if "主导航" in normalized:
        return "main-page"
    if "下级" in normalized:
        return "sub-page"
    if normalized in {"main-page", "sub-page", "page"}:
        return normalized
    return "page"


def extract_title(html_text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html_text, re.S | re.I)
    if not match:
        return "未命名页面"
    title = compact_whitespace(match.group(1))
    return re.sub(r"\s*\|\s*SmartChef PD\s*$", "", title)


def extract_button_texts(html_text: str) -> list[str]:
    buttons = []
    for match in re.findall(r">([^<>]{2,20})</Button>", html_text):
        label = compact_whitespace(match)
        if label and label not in buttons:
            buttons.append(label)
    return buttons


def extract_stat_titles(html_text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r'Statistic\s+title="([^"]+)"', html_text)))


def extract_column_groups(html_text: str) -> list[list[str]]:
    groups: list[list[str]] = []
    for _, body in re.findall(r"const\s+(\w+Columns)\s*=\s*\[(.*?)\n\s*\];", html_text, re.S):
        titles = [
            compact_whitespace(title)
            for title in re.findall(r'title:\s*"([^"]+)"', body)
            if compact_whitespace(title)
        ]
        if titles:
            groups.append(list(dict.fromkeys(titles)))
    return groups


def extract_form_fields(html_text: str) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    pattern = re.compile(
        r'Form\.Item(?:(?!Form\.Item).)*?name="([^"]+)"(?:(?!Form\.Item).)*?label="([^"]+)"',
        re.S,
    )
    for name, label in pattern.findall(html_text):
        entry = (name.strip(), compact_whitespace(label))
        if entry not in fields:
            fields.append(entry)
    return fields


def infer_shape(field_name: str) -> str:
    mapping = {
        "username": "string",
        "name": "string",
        "password": "string",
        "role": "enum",
        "newRole": "enum",
        "status": "enum",
        "createdAt": "date",
        "lastLogin": "datetime/null",
    }
    return mapping.get(field_name, "string")


def build_hidden_interactions(html_text: str) -> list[dict[str, str]]:
    interactions: list[dict[str, str]] = []

    if "setDrawerVisible(true)" in html_text or "说明" in html_text:
        interactions.append(
            {
                "id": "001",
                "container": "drawer",
                "classification": "instructional",
                "entry": "说明按钮",
                "purpose": "解释页面逻辑、状态流转、字段说明和易错点",
            }
        )

    if "createModalOpen" in html_text:
        interactions.append(
            {
                "id": "002",
                "container": "modal",
                "classification": "ui-capability",
                "entry": "新建账号",
                "purpose": "创建账号并指定初始角色",
            }
        )

    if "editRoleOpen" in html_text:
        interactions.append(
            {
                "id": "003",
                "container": "modal",
                "classification": "ui-capability",
                "entry": "编辑角色",
                "purpose": "调整角色并预览能力点变化",
            }
        )

    if "重置密码" in html_text:
        interactions.append(
            {
                "id": "004",
                "container": "confirm-modal",
                "classification": "ui-capability",
                "entry": "重置密码",
                "purpose": "重置账号密码并返回临时密码结果",
            }
        )

    if "不能禁用内置管理员账号" in html_text or "最后一个管理员保护" in html_text:
        interactions.append(
            {
                "id": "005",
                "container": "inline-alert",
                "classification": "domain-rule",
                "entry": "状态开关 / 风险提示",
                "purpose": "约束内置 admin 与最后一个启用管理员保护",
            }
        )

    return interactions


def build_hidden_interactions_from_semantics(entries: list[str]) -> list[dict[str, str]]:
    interactions: list[dict[str, str]] = []
    for index, entry in enumerate(entries, start=1):
        normalized = compact_whitespace(entry)
        prefix_match = re.match(r"`?([a-zA-Z-]+)`?\s*:\s*(.+)", normalized)
        prefix = prefix_match.group(1) if prefix_match else ""
        content = prefix_match.group(2) if prefix_match else normalized
        content = compact_whitespace(content.strip("`"))

        classification_map = {
            "functional-hidden-ui": "ui-capability",
            "explanatory-only": "instructional",
            "domain-rule": "domain-rule",
            "instructional": "instructional",
            "non-actionable-note": "non-actionable-note",
        }
        classification = classification_map.get(prefix, "ui-capability")
        interactions.append(
            {
                "id": f"{index:03d}",
                "container": "drawer-or-modal",
                "classification": classification,
                "entry": content,
                "purpose": content,
            }
        )
    return interactions


def build_capabilities(
    buttons: list[str],
    html_text: str,
    page_code_value: str,
    mod_code: str,
    *,
    has_data_view: bool,
) -> list[dict[str, str]]:
    capabilities = []
    if has_data_view:
        capabilities.append(
            {
                "id": f"CAP-{mod_code}-{page_code_value}-001",
                "title": "查看页面主数据",
                "type": "DATA",
                "priority": "P0",
                "done_signal": "页面主数据来自真实回读，而非本地硬编码",
            }
        )

    catalog = [
        ("新建账号", "创建账号", "CRUD", "P0", "创建成功后列表新增账号且统计卡回读更新"),
        ("新建方案", "创建方案", "CRUD", "P0", "创建成功后列表回读出现新方案"),
        ("编辑角色", "调整角色与能力预览", "STATE", "P0", "角色更新后列表回读，预览矩阵与新角色一致"),
        ("重置密码", "重置密码", "FEEDBACK", "P1", "确认后返回默认密码或明确失败原因"),
        ("状态开关", "启停用账号", "STATE", "P0", "状态切换后列表回读更新，管理员保护规则生效"),
        ("权限矩阵", "查看权限矩阵", "PERMISSION", "P0", "管理员、PM、测试三类角色能力点可见且条件说明明确"),
        ("新建分类", "创建知识分类", "CRUD", "P0", "创建成功后分类列表真实回读更新"),
        ("上传文档", "上传知识文档", "DATA", "P0", "上传后文档列表与解析状态真实回读更新"),
        ("检索测试", "验证知识检索", "FEEDBACK", "P1", "检索验证结果必须真实回读或明确失败原因"),
        ("模拟上传", "模拟上传解析", "ASYNC", "P1", "模拟上传后必须返回真实解析结果或明确失败原因"),
        ("新建指令库", "新建指令库", "CRUD", "P0", "新建成功后列表回读出现新库"),
        ("绑定指令库", "绑定指令库", "DATA", "P0", "绑定结果真实回读并反映到方案详情"),
        ("切换人设", "切换人设", "STATE", "P1", "切换后当前方案人设真实回读更新"),
        ("编辑人设", "编辑人设", "CRUD", "P1", "保存后人设配置真实回读更新"),
        ("新建人设", "新建人设", "CRUD", "P1", "创建后人设列表真实回读更新"),
        ("手动测试", "执行手动测试", "FEEDBACK", "P0", "手动测试结果与调试信息真实回读展示"),
        ("平台级批量测试", "进入平台级批量测试", "NAVIGATION", "P1", "可跳转到批量测试模块入口"),
        ("编辑", "编辑当前项", "CRUD", "P1", "保存后页面主数据回读为最新值"),
        ("删除", "删除当前项", "CRUD", "P1", "删除后列表或详情不再显示目标项"),
        ("新建批次", "创建测试批次", "ASYNC", "P0", "测试批次创建后列表真实回读出现新批次"),
        ("上传用例", "上传测试用例", "DATA", "P0", "上传后用例列表真实回读更新"),
        ("生成用例", "生成测试用例", "ASYNC", "P1", "生成后用例列表与摘要真实回读更新"),
        ("导入训练集", "导入训练集", "DATA", "P0", "训练集导入结果必须真实回读"),
        ("导入评估集", "导入评估集", "DATA", "P0", "评估集导入结果必须真实回读"),
        ("LLM生成训练集", "LLM 生成训练集", "ASYNC", "P1", "生成任务必须返回真实结果或明确失败原因"),
        ("LLM生成评估集", "LLM 生成评估集", "ASYNC", "P1", "生成任务必须返回真实结果或明确失败原因"),
        ("管理数据", "管理数据集内容", "DATA", "P0", "进入数据管理页后应可回读最新数据"),
        ("新建训练任务", "创建训练任务", "ASYNC", "P0", "训练任务创建后列表回读出现新任务"),
        ("新建训练", "创建训练任务", "ASYNC", "P0", "训练任务创建后列表回读出现新任务"),
        ("发布模型", "发布模型", "STATE", "P0", "发布完成后模型状态真实回读更新"),
        ("归档版本", "归档模型版本", "STATE", "P1", "归档后版本状态真实回读更新"),
        ("下载模型", "下载模型", "FEEDBACK", "P1", "下载动作返回真实文件或明确失败原因"),
        ("新建测试任务", "创建测试任务", "ASYNC", "P0", "测试任务创建后列表回读出现新任务"),
        ("重新执行", "重新执行测试批次", "ASYNC", "P1", "重新执行后批次结果与状态真实回读更新"),
        ("导出报告", "导出测试报告", "FEEDBACK", "P1", "导出动作返回真实报告文件或明确失败原因"),
        ("智能分析", "查看智能分析", "FEEDBACK", "P1", "分析结果必须来自真实计算或明确失败原因"),
        ("设备日志", "查看设备日志", "NAVIGATION", "P0", "可进入设备日志页查看链路排查结果"),
        ("告警规则", "配置告警规则", "NAVIGATION", "P0", "可进入告警规则页配置并查看规则状态"),
        ("手动刷新", "刷新监控指标", "FEEDBACK", "P1", "刷新后最新监控指标真实回读更新"),
        ("新建规则", "创建告警规则", "CRUD", "P0", "创建后规则列表真实回读更新"),
    ]

    current_index = len(capabilities) + 1
    text = html_text + "\n" + "\n".join(buttons)
    seen_titles = {item["title"] for item in capabilities}
    for needle, title, cap_type, priority, done_signal in catalog:
        if needle in text and title not in seen_titles:
            capabilities.append(
                {
                    "id": f"CAP-{mod_code}-{page_code_value}-{current_index:03d}",
                    "title": title,
                    "type": cap_type,
                    "priority": priority,
                    "done_signal": done_signal,
                }
            )
            seen_titles.add(title)
            current_index += 1

    if not capabilities:
        capabilities.append(
            {
                "id": f"CAP-{mod_code}-{page_code_value}-001",
                "title": "完成页面主要操作",
                "type": "STATE",
                "priority": "P0",
                "done_signal": "关键操作结果必须真实回读",
            }
        )

    return capabilities


def build_capabilities_from_semantics(entries: list[str], page_code_value: str, mod_code: str) -> list[dict[str, str]]:
    capabilities = []
    for index, entry in enumerate(entries, start=1):
        title = compact_whitespace(re.sub(r"`([^`]+)`", r"\1", entry))
        capabilities.append(
            {
                "id": f"CAP-{mod_code}-{page_code_value}-{index:03d}",
                "title": title,
                "type": "DATA" if "管理" in title or "CRUD" in title else "STATE",
                "priority": "P0",
                "done_signal": f"{title} 的结果必须真实回读",
            }
        )
    return capabilities


def build_action_contracts(capabilities: list[dict[str, str]]) -> list[dict[str, str]]:
    contracts: list[dict[str, str]] = []
    for index, capability in enumerate(capabilities, start=1):
        title = capability["title"]
        if title.startswith("浏览") or title.startswith("查看"):
            continue
        contracts.append(
            {
                "id": f"ACT-{index:03d}",
                "action": title,
                "preconditions": "必要字段合法且权限满足",
                "success_signal": capability["done_signal"],
                "failure_feedback": "必须给出明确错误提示，不允许假成功",
                "state_change": title,
            }
        )
    return contracts


def build_action_contracts_from_semantics(entries: list[str]) -> list[dict[str, str]]:
    contracts: list[dict[str, str]] = []
    for index, entry in enumerate(entries, start=1):
        normalized = compact_whitespace(re.sub(r"`([^`]+)`", r"\1", entry))
        action, _, detail = normalized.partition(":")
        detail = detail.strip() or f"{action} 的结果必须真实回读"
        contracts.append(
            {
                "id": f"ACT-{index:03d}",
                "action": action.strip(),
                "preconditions": "前置字段与权限满足",
                "success_signal": detail,
                "failure_feedback": "必须给出明确失败反馈",
                "state_change": action.strip(),
            }
        )
    return contracts


def build_business_rules(html_text: str, capability_id: str, scope: str) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    lower_html = html_text.lower()

    if "capability" in lower_html and ("管理员" in html_text or "权限矩阵" in html_text or "role" in lower_html):
        rules.append(
            {
                "id": "RULE-001",
                "rule": "权限判断必须基于 capability，而不是硬编码角色名",
                "scope": scope,
                "related_capability": capability_id,
            }
        )

    if "不能禁用内置管理员账号" in html_text:
        rules.append(
            {
                "id": "RULE-002",
                "rule": "内置管理员账号不可禁用",
                "scope": scope,
                "related_capability": capability_id,
            }
        )

    if "最后一个管理员保护" in html_text:
        rules.append(
            {
                "id": "RULE-003",
                "rule": "系统至少保留一个启用中的管理员账号",
                "scope": scope,
                "related_capability": capability_id,
            }
        )

    return rules


def build_business_rules_from_semantics(entries: list[str], scope: str, capability_id: str) -> list[dict[str, str]]:
    return [
        {
            "id": f"RULE-{index:03d}",
            "rule": compact_whitespace(re.sub(r"`([^`]+)`", r"\1", entry)),
            "scope": scope,
            "related_capability": capability_id,
        }
        for index, entry in enumerate(entries, start=1)
    ]


def build_exception_flows(html_text: str) -> list[dict[str, str]]:
    flows = []
    if "不能禁用内置管理员账号" in html_text:
        flows.append(
            {
                "id": "EX-001",
                "scenario": "尝试禁用内置管理员账号",
                "expected_feedback": "立即回弹开关并提示不可禁用",
                "recovery": "保持原状态，管理员改为处理其他账号",
            }
        )
    if "重置密码" in html_text:
        flows.append(
            {
                "id": "EX-002",
                "scenario": "重置密码失败或被拒绝",
                "expected_feedback": "提示失败原因，不得伪造成功提示",
                "recovery": "允许管理员重新发起操作",
            }
        )
    return flows


def render_module_markdown(
    *,
    module_key: str,
    readme_text: str,
    html_pages: dict[str, str],
    source_dir: Path,
) -> tuple[str, str]:
    mod_code = module_code(module_key)
    frs = extract_covered_frs(readme_text)
    success_standard = extract_success_standard(readme_text)
    out_of_scope_items = list(dict.fromkeys(extract_out_of_scope(readme_text)))
    page_rows = extract_page_rows(readme_text)
    navigation_parents = extract_navigation_parents(readme_text)
    page_semantics = extract_page_semantics(readme_text)

    page_sections = []
    page_index_rows = []
    fr_mapping_rows: list[str] = []
    review_pages: list[dict[str, object]] = []

    for filename, html_text in html_pages.items():
        page_key = filename[:-5]
        page_id = f"{module_key}.{page_key}"
        page_code_value = page_code(page_key)
        title = extract_title(html_text)
        page_row = page_rows.get(filename, {})
        semantic_page = page_semantics.get(filename, {})
        semantic_boundary_items = semantic_page.get("page_boundary", [])
        semantic_boundary = semantic_boundary_items[0] if semantic_boundary_items else ""
        page_boundary = normalize_semantic_boundary(semantic_boundary) if semantic_boundary else map_page_boundary(page_row.get("type", "page"))
        parent_html = navigation_parents.get(filename)
        if parent_html and parent_html not in html_pages:
            parent_html = None
        parent_page = f"{module_key}.{parent_html[:-5]}" if parent_html else "none"
        buttons = extract_button_texts(html_text)
        stats = extract_stat_titles(html_text)
        column_groups = extract_column_groups(html_text)
        form_fields = extract_form_fields(html_text)
        semantic_hidden = semantic_page.get("interactive_containers", [])
        semantic_caps = semantic_page.get("capability_checklist", [])
        semantic_actions = semantic_page.get("action_contracts", [])
        semantic_rules = semantic_page.get("business_rules", [])
        semantic_frs = parse_frs("\n".join(semantic_page.get("fr_mapping", []))) or frs or ["FR-UNKNOWN"]

        hidden_interactions = (
            build_hidden_interactions_from_semantics(semantic_hidden)
            if semantic_hidden
            else build_hidden_interactions(html_text)
        )
        capabilities = (
            build_capabilities_from_semantics(semantic_caps, page_code_value, mod_code)
            if semantic_caps
            else build_capabilities(
                buttons,
                html_text,
                page_code_value,
                mod_code,
                has_data_view=bool(stats or column_groups),
            )
        )
        actions = (
            build_action_contracts_from_semantics(semantic_actions)
            if semantic_actions
            else build_action_contracts(capabilities)
        )
        business_rules = (
            build_business_rules_from_semantics(semantic_rules, page_id, capabilities[0]["id"])
            if semantic_rules
            else build_business_rules(html_text, capabilities[0]["id"], page_id)
        )
        exceptions = build_exception_flows(html_text)

        visible_ui_rows = []
        ui_index = 1
        if stats:
            visible_ui_rows.append(
                f"| `UI-{page_code_value}-{ui_index:03d}` | `stats` | 统计卡 | {', '.join(stats)} | prototype state |"
            )
            ui_index += 1

        for idx, columns in enumerate(column_groups, start=ui_index):
            visible_ui_rows.append(
                f"| `UI-{page_code_value}-{idx:03d}` | `table` | 表格 | {', '.join(columns)} | prototype columns |"
            )
        next_idx = ui_index + len(column_groups)

        if buttons:
            visible_ui_rows.append(
                f"| `UI-{page_code_value}-{next_idx:03d}` | `actions` | 操作入口 | {', '.join(buttons)} | page actions |"
            )

        hidden_rows = [
            f"| `HID-{page_code_value}-{item['id']}` | `{item['container']}` | `{item['classification']}` | {item['entry']} | {item['purpose']} |"
            for item in hidden_interactions
        ] or ["| `HID-NONE` | `none` | `non-actionable-note` | 无 | 当前页面无额外隐藏交互 |"]

        capability_rows = [
            f"| `{item['id']}` | {item['title']} | `{item['type']}` | `{item['priority']}` | {item['done_signal']} |"
            for item in capabilities
        ]
        action_rows = [
            f"| `{item['id']}` | {item['action']} | {item['preconditions']} | {item['success_signal']} | {item['failure_feedback']} | {item['state_change']} |"
            for item in actions
        ] or ["| `ACT-NONE` | 无需显式动作契约 | - | - | - | - |"]

        data_rows = []
        for idx, (field_name, label) in enumerate(form_fields, start=1):
            data_rows.append(
                f"| `DATA-{page_code_value}-{idx:03d}` | `{field_name}` | `{infer_shape(field_name)}` | `yes` | form field | {label} |"
            )
        if not data_rows:
            data_rows.append("| `DATA-NONE` | `n/a` | `n/a` | `no` | derived | 当前页面未识别出表单字段 |")

        rule_rows = [
            f"| `{item['id']}` | {item['rule']} | {item['scope']} | `{item['related_capability']}` |"
            for item in business_rules
        ] or ["| `RULE-NONE` | 当前页面未自动识别到额外业务规则 | n/a | `n/a` |"]

        exception_rows = [
            f"| `{item['id']}` | {item['scenario']} | {item['expected_feedback']} | {item['recovery']} |"
            for item in exceptions
        ] or ["| `EX-NONE` | 当前页面未自动识别到异常流 | - | - |"]

        page_fr_rows = [
            f"| `{item['id']}` | `{fr}` | `full` |"
            for item in capabilities
            for fr in semantic_frs
        ]
        fr_mapping_rows.extend(page_fr_rows)

        page_index_rows.append(
            f"| `{page_id}` | {title} | `{page_boundary}` | `{filename}` | {len(capabilities)} | {', '.join(semantic_frs)} |"
        )

        page_goal = infer_page_goal(
            page_name=title,
            semantic_page=semantic_page,
            capabilities=capabilities,
            actions=actions,
        )
        primary_flows = infer_primary_user_flows(
            page_name=title,
            semantic_page=semantic_page,
            actions=actions,
            capabilities=capabilities,
        )

        page_sections.append(
            f"""## Page: {page_id}

```yaml
page_id: {page_id}
page_name: {title}
page_boundary: {page_boundary}
goal: {page_goal}
route_or_entry: {filename}
parent_page: {parent_page}
```

### primary_user_flows

{chr(10).join(f"- {flow}" for flow in primary_flows)}

### visible_ui

| ui_id | type | label | purpose | source |
|------|------|-------|---------|--------|
{chr(10).join(visible_ui_rows)}

### hidden_interactions

| hidden_id | container | classification | entry | purpose |
|-----------|-----------|----------------|-------|---------|
{chr(10).join(hidden_rows)}

### capabilities

| capability_id | title | type | priority | done_signal |
|---------------|-------|------|----------|-------------|
{chr(10).join(capability_rows)}

### action_contracts

| action_id | action | preconditions | success_signal | failure_feedback | state_change |
|-----------|--------|---------------|----------------|------------------|--------------|
{chr(10).join(action_rows)}

### data_contracts

| data_id | field_or_column | shape | required | source | notes |
|---------|-----------------|-------|----------|--------|-------|
{chr(10).join(data_rows)}

### business_rules

| rule_id | rule | scope | related_capability |
|---------|------|-------|--------------------|
{chr(10).join(rule_rows)}

### exception_flows

| exception_id | scenario | expected_feedback | recovery |
|--------------|----------|-------------------|----------|
{chr(10).join(exception_rows)}
"""
        )
        review_pages.append(
            {
                "page_id": page_id,
                "page_name": title,
                "page_boundary": page_boundary,
                "route_or_entry": filename,
                "parent_page": parent_page,
                "capability_count": len(capabilities),
                "has_hidden_interactions": bool(hidden_interactions),
            }
        )

    unique_fr_mapping_rows = list(dict.fromkeys(fr_mapping_rows))

    final_out_of_scope_items = list(out_of_scope_items)
    scaffold_notice = "当前脚本不会从 HumanPD 自动恢复完整业务后端契约，只生成 AI-PD scaffold。"
    if scaffold_notice not in final_out_of_scope_items:
        final_out_of_scope_items.append(scaffold_notice)

    markdown = f"""# AI-PD: {module_key}

```yaml
module_key: {module_key}
based_on:
  - spec.md
  - pd-all/pd-index.md
  - pd-all/{source_dir.name}/README.md
{chr(10).join(f"  - pd-all/{source_dir.name}/{name}" for name in html_pages)}
status: pilot
```

## 模块摘要

- **模块目标**: {success_standard}
- **来源 HumanPD**: `pd-all/{source_dir.name}/`
- **覆盖 FR**: {", ".join(frs) if frs else "FR-UNKNOWN"}
- **转换口径**: 本文件由半自动脚本生成，用作 AI-PD scaffold，允许后续人工精修

## 页面索引

| page_id | page_name | page_boundary | route_or_entry | capability_count | related_fr |
|---------|-----------|---------------|----------------|------------------|------------|
{chr(10).join(page_index_rows)}

{chr(10).join(page_sections)}

## acceptance_signals

- 页面关键结果必须能真实回读，不能只依赖 toast、静态 mock 或本地状态假更新。
- 隐藏交互只有在 AI-PD 中被标为 `instructional / non-actionable-note` 时才能排除出实现闭环。
- 当前输出为半自动 scaffold；若发现能力、契约或异常流缺项，必须继续人工补全。

## fr_mapping

| capability_id | fr_id | status |
|---------------|------|--------|
{chr(10).join(unique_fr_mapping_rows)}

## out_of_scope

{chr(10).join(f"- {item}" for item in final_out_of_scope_items)}
- 若 HumanPD 未显式表达真实路由、异常反馈或数据字段，生成结果会保留保守默认值，需后续人工精修。
"""

    review_index_rows = "\n".join(
        f"| `{item['page_id']}` | {item['page_name']} | `{item['page_boundary']}` | `{item['route_or_entry']}` | `{item['parent_page']}` | {item['capability_count']} | {'是' if item['has_hidden_interactions'] else '否'} |"
        for item in review_pages
    )
    review_sections = "\n".join(
        f"""### {item['page_id']}

- [ ] `page_boundary` / `parent_page` 正确，未把跨模块跳转误记为当前模块父子页
- [ ] `hidden_interactions` 分类准确；若本页含 Drawer / Modal / Tabs / Collapse 中的真实产品能力，未被误标为 `instructional`
- [ ] `capabilities` 粒度正确：没有关键能力遗漏，也没有把多个能力错误合并
- [ ] `action_contracts` 的 `success_signal` 可用于验收，不是 toast、前端本地状态或静态 mock 假成功
- [ ] 若本页 `business_rules / exception_flows` 明显缺失，已直接回写到 `ai-{module_key}.md`
"""
        for item in review_pages
    )
    checklist = f"""# AI-PD 人工校对清单: {module_key}

## 使用方式

- 本清单只覆盖高风险语义点，不要求对 `ai-{module_key}.md` 做全文重审
- 校对时必须直接修改 `ai-{module_key}.md`
- 本清单只作为审核辅助，不是第二份语义真相，也不是“是否已修改完成”的状态记录
- `visible_ui`、显性表格列、显性按钮、显性表单字段默认按“自动可信项”处理，除非你发现明显抽取错误

## 模块级必查项

- [ ] 模块 `覆盖 FR` 只包含当前模块真实覆盖范围，不含跨模块引用或 `out_of_scope`
- [ ] `out_of_scope` 已显式写清 Deferred / Blocked By / 跨模块引用 / AD-DD 范围项
- [ ] 页面索引完整，页面数量与 `pd-all/{source_dir.name}/` 中 HTML 文件一致
- [ ] 所有页面都有稳定 `page_id`，且主页面的 `parent_page` 为 `none`
- [ ] 若模块存在隐藏交互承载真实产品能力，相关项已在 `hidden_interactions / capabilities / action_contracts` 中显式落地

## 页面快速校对索引

| page_id | page_name | boundary | route_or_entry | parent_page | capability_count | 含隐藏交互 |
|---------|-----------|----------|----------------|-------------|------------------|------------|
{review_index_rows}

## 页面级高风险校对

{review_sections}
"""
    return markdown, checklist


def render_index(entries: list[dict[str, str]]) -> str:
    entries = sorted(entries, key=lambda item: item["module_key"])
    rows = "\n".join(
        f"| `{entry['module_key']}` | `{entry['file_name']}` | `{entry['checklist_file']}` | `{entry['source_dir']}` | pilot | semi-auto generated |"
        for entry in entries
    )
    return f"""# AI-PD 索引

## 定位

`ai-pd/` 是给 AI、harness 和下游命令消费的主语义输入层。

## 当前模块

| 模块 | AI-PD 文件 | 人工校对清单 | 来源 HumanPD | 状态 | 说明 |
|------|-------------|----------------|-------------|------|------|
{rows}
"""


def discover_modules(feature_dir: Path, requested_module: str | None) -> list[str]:
    pd_all_dir = feature_dir / "pd-all"
    if requested_module:
        return [requested_module]
    return sorted(path.name for path in pd_all_dir.iterdir() if path.is_dir() and path.name.startswith("pd-"))


def generate_for_module(feature_dir: Path, module_name: str) -> tuple[str, str, str]:
    module_dir = feature_dir / "pd-all" / module_name
    if not module_dir.exists():
        raise FileNotFoundError(f"Module directory not found: {module_dir}")

    readme_path = module_dir / "README.md"
    if not readme_path.exists():
        raise FileNotFoundError(f"README not found: {readme_path}")

    html_pages = {path.name: read_text(path) for path in sorted(module_dir.glob("*.html"))}
    if not html_pages:
        raise FileNotFoundError(f"No HTML files found in: {module_dir}")

    readme_text = read_text(readme_path)
    missing_semantic_anchors = find_missing_page_semantic_anchors(readme_text, html_pages)
    if missing_semantic_anchors:
        raise ValueError(format_missing_page_semantic_anchors(module_dir, missing_semantic_anchors))

    module_key = normalize_module_key(module_name)
    markdown, checklist = render_module_markdown(
        module_key=module_key,
        readme_text=readme_text,
        html_pages=html_pages,
        source_dir=module_dir,
    )
    return module_key, markdown, checklist


def main() -> int:
    parser = argparse.ArgumentParser(description="Transform HumanPD into AI-PD scaffolds.")
    parser.add_argument("--feature", default="master", help="Feature/spec workspace name")
    parser.add_argument("--module", help="Target module key, e.g. pd-user-mgmt")
    parser.add_argument("--output-dir", help="Custom ai-pd output directory")
    parser.add_argument("--stdout", action="store_true", help="Print generated module markdown to stdout")
    args = parser.parse_args()

    feature_dir = REPO_ROOT / "specs" / args.feature
    if not feature_dir.exists():
        raise SystemExit(f"Feature directory not found: {feature_dir}")

    module_names = discover_modules(feature_dir, args.module)
    output_dir = Path(args.output_dir) if args.output_dir else feature_dir / "ai-pd"
    output_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    rendered_outputs = []
    for module_name in module_names:
        try:
            module_key, markdown, checklist = generate_for_module(feature_dir, module_name)
        except ValueError as exc:
            sys.stderr.write(f"{exc}\n")
            return 1
        file_name = f"ai-{module_key}.md"
        checklist_file = f"ai-{module_key}.checklist.md"
        (output_dir / file_name).write_text(markdown, encoding="utf-8")
        (output_dir / checklist_file).write_text(checklist, encoding="utf-8")
        entries.append(
            {
                "module_key": module_key,
                "file_name": file_name,
                "checklist_file": checklist_file,
                "source_dir": f"pd-all/{module_name}/",
            }
        )
        rendered_outputs.append(markdown)

    merged_entries: dict[str, dict[str, str]] = {}
    for existing_path in output_dir.glob("ai-*.md"):
        if existing_path.name.endswith(".checklist.md"):
            continue
        existing_module_key = existing_path.stem.replace("ai-", "", 1)
        merged_entries[existing_module_key] = {
            "module_key": existing_module_key,
            "file_name": existing_path.name,
            "checklist_file": f"ai-{existing_module_key}.checklist.md",
            "source_dir": f"pd-all/pd-{existing_module_key}/",
        }
    for entry in entries:
        merged_entries[entry["module_key"]] = entry

    (output_dir / "README.md").write_text(
        render_index(list(merged_entries.values())),
        encoding="utf-8",
    )

    if args.stdout:
        sys.stdout.write("\n\n".join(rendered_outputs))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
