#!/usr/bin/env python3
"""缺陷规则扫描脚本（手动触发）。

扫描 specs/master/defects/*.md，执行规则检查与联动分析。
每次扫描会更新 defects/INDEX.md 状态表，便于快速查看，无需全量解析。
用法：python scripts/scan_defects.py [--auto]
  --auto: 自动将分析结果写入缺陷的 related 字段
"""
from pathlib import Path
import re
import argparse

DEFECTS_DIR = Path(__file__).resolve().parent.parent / "specs" / "master" / "defects"
SPECS_DIR = Path(__file__).resolve().parent.parent / "specs" / "master"
VALID_STATUS = {"新建", "待理解", "已理解", "修复中", "修复完成", "待确认", "重新打开", "已确认", "已关闭", "已解决"}
VALID_CATEGORY = {"接口", "UI", "业务", "规范", "需求", "Code Bug", "PD 功能缺失"}
VALID_PRIORITY = {"P1", "P2", "P3", ""}
REQUIRED_FIELDS = ("id", "status", "created", "category")

CATEGORY_ROUTE = {
    "接口": "代码修复",
    "UI": "代码修复",
    "业务": "设计补充",
    "规范": "设计补充",
    "需求": "需求回溯",
    "Code Bug": "代码修复",
    "PD 功能缺失": "需求回溯",
}

# 用户故事关键词（用于自动匹配）
US_KEYWORDS = {
    "US1": ["指令配置", "意图", "槽位", "训练数据", "Intent", "intent", "指令列表", "分类筛选"],
    "US2": ["知识库", "菜谱", "文档上传", "索引", "knowledge", "知识"],
    "US3": ["对话方案", "人设", "大模型", "路由策略", "profile", "方案", "发布"],
    "US4": ["手动测试", "测试会话", "调试面板", "test/chat", "test/sessions"],
    "US5": ["设备端", "dialog/chat", "设备调用"],
    "US6": ["知识问答", "闲聊", "chitchat", "联网"],
    "US7": ["路由", "指代", "上下文", "router"],
    "US8": ["批量测试", "batch-test", "batch_test"],
    "US9": ["监控", "仪表盘", "日志", "告警", "monitoring"],
    "US10": ["用户管理", "角色", "权限", "auth", "RBAC"],
}


def parse_defect(path: Path) -> dict | None:
    """解析单个缺陷文件，返回 frontmatter + body + 文件名。"""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        return None
    fm_raw, body = match.groups()
    fm = {}
    for line in fm_raw.strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    fm["_file"] = path.name
    fm["_body"] = body
    fm["_path"] = path
    return fm


def collect_defects() -> list[dict]:
    """收集所有缺陷文件（排除模板和 README）。"""
    defects = []
    for f in DEFECTS_DIR.glob("*.md"):
        if f.name in ("_template.md", "README.md"):
            continue
        d = parse_defect(f)
        if d:
            defects.append(d)
    return defects


def r1_status_check(defects: list[dict]) -> list[str]:
    """R1: 状态不在枚举内。"""
    out = []
    for d in defects:
        s = d.get("status", "")
        if s and s not in VALID_STATUS:
            out.append(f"  {d.get('_file', '?')} id={d.get('id')} status='{s}' 不在枚举内")
    return out


def r2_required_check(defects: list[dict]) -> list[str]:
    """R2: 必填字段缺失。"""
    out = []
    for d in defects:
        for f in REQUIRED_FIELDS:
            v = d.get(f)
            if not v or (isinstance(v, str) and v.strip() == ""):
                out.append(f"  {d.get('_file', '?')} id={d.get('id')} 缺少或为空: {f}")
    return out


def r4_fix_ref_status(defects: list[dict]) -> list[str]:
    """R4: 有 fix_ref 但 status 仍为修复中。"""
    out = []
    for d in defects:
        if d.get("fix_ref") and d.get("status") == "修复中":
            out.append(f"  {d.get('_file', '?')} id={d.get('id')} 已填 fix_ref，建议改为「修复完成」")
    return out


def build_task_index() -> dict[str, list[str]]:
    """从 tasks.md 解析任务 ID 与描述关键词。"""
    tasks_path = SPECS_DIR / "tasks.md"
    if not tasks_path.exists():
        return {}
    text = tasks_path.read_text(encoding="utf-8")
    # 匹配 "- [ ] T001 描述" 或 "- [x] T001 描述"
    pattern = r"-\s*\[\s*[ x]\s*\]\s+(T\d+)\s+(.+)"
    index = {}
    for m in re.finditer(pattern, text):
        tid, desc = m.groups()
        # 提取描述中的有意义词（长度>=2，排除纯数字）
        words = re.findall(r"[\u4e00-\u9fff\w]{2,}", desc)
        index[tid] = list(set(words))[:10]  # 最多10个关键词
    return index


def analyze_related(defect: dict, task_index: dict[str, list[str]]) -> list[str]:
    """分析缺陷正文，自动匹配 spec/task/plan，返回建议的 related 列表。"""
    body = defect.get("_body", "") or ""
    title = ""
    for line in body.split("\n"):
        if line.strip().startswith("# "):
            title = line.strip().lstrip("# ").strip()
            break
    text = (title + "\n" + body).lower()
    body_raw = title + "\n" + body

    related = set()

    # 1. 直接提及 US1, T026 等（在原文中查找以保留大小写）
    for m in re.finditer(r"US\d+", body_raw, re.IGNORECASE):
        related.add(m.group().upper())
    for m in re.finditer(r"T\d+", body_raw):
        related.add(m.group())

    # 2. 用户故事关键词匹配
    for us, keywords in US_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text or kw in body_raw:
                related.add(us)
                break

    # 3. 任务关键词匹配（仅匹配 4 字及以上且非通用词，降低误匹配）
    stopwords = {"创建", "测试", "编写", "api", "backend", "frontend", "添加", "配置", "模块", "路由"}
    for tid, keywords in task_index.items():
        for kw in keywords:
            if len(kw) >= 4 and kw not in stopwords and (kw.lower() in text or kw in body_raw):
                related.add(tid)
                break

    return sorted(related, key=lambda x: (0 if x.startswith("US") else 1, 0 if x.startswith("T") else 1, x))


def _extract_title(body: str) -> str:
    """从正文提取首个 # 标题。"""
    for line in body.split("\n"):
        if line.strip().startswith("# "):
            return line.strip().lstrip("# ").strip()
    return ""


def write_index(defects: list[dict]) -> None:
    """生成 INDEX.md 状态表，供快速查看与系统读取。"""
    lines = [
        "# 缺陷状态表",
        "",
        "> 由 `python scripts/scan_defects.py` 自动生成，勿手动编辑。",
        "",
        "| ID | 标题 | 状态 | 分类 | 优先级 | 创建 | 关联 | 设计引用 | 建议路径 |",
        "|----|------|------|------|--------|------|------|----------|----------|",
    ]
    for d in sorted(defects, key=lambda x: x.get("id", "")):
        title = _extract_title(d.get("_body", "") or "")
        if len(title) > 30:
            title = title[:27] + "..."
        cat = d.get("category", "")
        route = CATEGORY_ROUTE.get(cat, "-")
        design_ref = d.get("design_ref", "") or "-"
        lines.append(
            f"| {d.get('id', '')} | {title} | {d.get('status', '')} | {cat} | "
            f"{d.get('priority', '') or '-'} | {d.get('created', '')} | "
            f"{d.get('related', '') or '-'} | {design_ref} | {route} |"
        )
    lines.extend(["", f"*共 {len(defects)} 条，最后更新：运行 scan_defects.py 时*"])
    (DEFECTS_DIR / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def r5_pending_verify(defects: list[dict]) -> list[dict]:
    """R5: 待确认清单。"""
    return [d for d in defects if d.get("status") == "待确认"]


def r5b_reopened(defects: list[dict]) -> list[dict]:
    """R5b: 重新打开清单（验证未通过，需重新修复）。"""
    return [d for d in defects if d.get("status") == "重新打开"]


def r6_stats(defects: list[dict]) -> dict:
    """R6: 分类、状态、优先级统计。"""
    by_cat = {}
    by_status = {}
    by_priority = {}
    for d in defects:
        c = d.get("category") or "未分类"
        s = d.get("status") or "未知"
        p = d.get("priority") or "未设"
        by_cat[c] = by_cat.get(c, 0) + 1
        by_status[s] = by_status.get(s, 0) + 1
        by_priority[p] = by_priority.get(p, 0) + 1
    return {"by_category": by_cat, "by_status": by_status, "by_priority": by_priority}


def main(args):
    if not DEFECTS_DIR.exists():
        print(f"缺陷目录不存在: {DEFECTS_DIR}")
        return
    defects = collect_defects()
    print(f"共扫描 {len(defects)} 个缺陷文件\n")

    # R1
    r1 = r1_status_check(defects)
    if r1:
        print("【R1 状态检查】状态不在枚举内:")
        print("\n".join(r1))
    else:
        print("【R1 状态检查】通过")

    # R2
    r2 = r2_required_check(defects)
    if r2:
        print("\n【R2 必填检查】缺失字段:")
        print("\n".join(r2))
    else:
        print("\n【R2 必填检查】通过")

    # R4
    r4 = r4_fix_ref_status(defects)
    if r4:
        print("\n【R4 修复完成待确认】建议更新状态:")
        print("\n".join(r4))
    else:
        print("\n【R4 修复完成待确认】无异常")

    # R5
    r5 = r5_pending_verify(defects)
    print(f"\n【R5 待确认清单】共 {len(r5)} 条:")
    for d in r5:
        print(f"  - {d.get('_file')} id={d.get('id')} category={d.get('category')}")

    # R5b
    r5b = r5b_reopened(defects)
    print(f"\n【R5b 重新打开清单】共 {len(r5b)} 条:")
    for d in r5b:
        print(f"  - {d.get('_file')} id={d.get('id')} category={d.get('category')}")

    # R6
    r6 = r6_stats(defects)
    print("\n【R6 统计】")
    print("  按分类:", r6["by_category"])
    print("  按状态:", r6["by_status"])
    print("  按优先级:", r6["by_priority"])

    # R7 联动：自动分析缺陷与 spec/task/plan 的关联
    task_index = build_task_index()
    print("\n【R7 联动】自动分析缺陷关联（基于缺陷正文）:")
    written = 0
    for d in defects:
        suggested = analyze_related(d, task_index)
        did = d.get("id", "?")
        if suggested:
            suggested_str = ", ".join(suggested)
            d["related"] = suggested_str  # 供 INDEX 使用
            print(f"  {did}: {suggested_str}")
            if args.auto and d.get("_path"):
                _write_related(d["_path"], suggested_str)
                written += 1
        else:
            print(f"  {did}: (无匹配)")
    if args.auto and written:
        print(f"\n  已自动写入 {written} 个缺陷的 related 字段")

    # R8 分类路由：根据 category 推荐处置路径
    actionable = [d for d in defects if d.get("status") in ("新建", "待理解", "已理解", "修复中", "重新打开")]
    if actionable:
        print(f"\n【R8 分类路由】待处理缺陷的建议处置路径（共 {len(actionable)} 条）:")
        for d in sorted(actionable, key=lambda x: x.get("id", "")):
            cat = d.get("category", "")
            route = CATEGORY_ROUTE.get(cat, "未知（请补充 category）")
            print(f"  {d.get('id', '?')} [{cat or '?'}] → {route}")
    else:
        print("\n【R8 分类路由】无待处理缺陷")

    # 更新 INDEX.md 状态表
    write_index(defects)
    print(f"\n  已更新 {DEFECTS_DIR / 'INDEX.md'}")


def _write_related(path: Path, related: str) -> None:
    """将 related 写入缺陷文件的 frontmatter。"""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        return
    fm_raw, body = match.groups()
    new_fm = []
    found = False
    for line in fm_raw.split("\n"):
        if line.strip().startswith("related:"):
            new_fm.append(f"related: {related}")
            found = True
        else:
            new_fm.append(line)
    if not found:
        new_fm.append(f"related: {related}")
    new_text = "---\n" + "\n".join(new_fm) + "\n---\n" + body
    path.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="缺陷规则扫描")
    parser.add_argument("--auto", action="store_true", help="自动将分析结果写入缺陷的 related 字段")
    main(parser.parse_args())
