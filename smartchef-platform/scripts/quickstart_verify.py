"""
SmartChef 快速启动端到端验证脚本
按 quickstart.md 中的步骤依次执行，验证核心流程是否通畅。

用法：
    python scripts/quickstart_verify.py
    python scripts/quickstart_verify.py --base-url http://localhost:8000
    python scripts/quickstart_verify.py --username admin --password admin123456
"""

import argparse
import sys
import time
import io

import httpx

# 默认配置
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_API_PREFIX = "/api/v1"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123456"

# 用于记录创建的资源 ID，方便后续步骤引用
created_resources: dict[str, str] = {}


class StepResult:
    """单步验证结果"""

    def __init__(self, name: str, success: bool, detail: str = ""):
        self.name = name
        self.success = success
        self.detail = detail


def print_step(index: int, name: str):
    print(f"\n{'='*60}")
    print(f"  步骤 {index}: {name}")
    print(f"{'='*60}")


def print_result(result: StepResult):
    icon = "[OK]" if result.success else "[FAIL]"
    print(f"\n  {icon} {result.name}")
    if result.detail:
        for line in result.detail.strip().split("\n"):
            print(f"     {line}")


def api_url(base_url: str, path: str) -> str:
    return f"{base_url}{DEFAULT_API_PREFIX}{path}"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ────────────────────────────────────────────────────────────
# 步骤 1：健康检查
# ────────────────────────────────────────────────────────────
def step_health_check(client: httpx.Client, base_url: str) -> StepResult:
    print_step(1, "健康检查 (GET /health)")
    try:
        resp = client.get(api_url(base_url, "/health"), timeout=10)
        data = resp.json()
        if resp.status_code == 200 and data.get("status") == "healthy":
            db_ms = data["components"]["database"]["response_ms"]
            redis_ms = data["components"]["redis"]["response_ms"]
            return StepResult(
                "健康检查",
                True,
                f"PostgreSQL: {db_ms}ms, Redis: {redis_ms}ms",
            )
        return StepResult(
            "健康检查",
            False,
            f"状态: {data.get('status')}, HTTP {resp.status_code}\n{data}",
        )
    except httpx.ConnectError:
        return StepResult(
            "健康检查",
            False,
            f"无法连接到 {base_url}，请确认后端服务已启动",
        )
    except Exception as e:
        return StepResult("健康检查", False, str(e))


# ────────────────────────────────────────────────────────────
# 步骤 2：登录获取 Token
# ────────────────────────────────────────────────────────────
def step_login(client: httpx.Client, base_url: str, username: str, password: str) -> StepResult:
    print_step(2, f"登录获取 Token (POST /auth/login, 用户: {username})")
    try:
        resp = client.post(
            api_url(base_url, "/auth/login"),
            json={"username": username, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            token = resp.json().get("access_token", "")
            created_resources["token"] = token
            masked = token[:20] + "..." if len(token) > 20 else token
            return StepResult("登录", True, f"Token: {masked}")
        return StepResult("登录", False, f"HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        return StepResult("登录", False, str(e))


# ────────────────────────────────────────────────────────────
# 步骤 3：创建示例意图
# ────────────────────────────────────────────────────────────
def step_create_intent(client: httpx.Client, base_url: str) -> StepResult:
    print_step(3, "创建示例意图 (POST /intents)")
    token = created_resources.get("token", "")
    payload = {
        "intent_key": "quickstart_test_cooking",
        "display_name": "启动烹饪（快速验证）",
        "category": "烹饪控制",
        "description": "quickstart 验证脚本自动创建的测试意图",
        "slots": [
            {
                "slot_key": "duration",
                "display_name": "烹饪时长",
                "entity_type": "duration",
                "is_required": True,
                "prompt_text": "请问您要烹饪多长时间？",
                "sort_order": 0,
            }
        ],
    }
    try:
        resp = client.post(
            api_url(base_url, "/intents"),
            json=payload,
            headers=auth_headers(token),
            timeout=15,
        )
        if resp.status_code == 201:
            data = resp.json()
            intent_id = data["id"]
            created_resources["intent_id"] = intent_id
            return StepResult(
                "创建意图",
                True,
                f"意图 ID: {intent_id}\n名称: {data['display_name']}, 槽位数: {len(data.get('slots', []))}",
            )
        if resp.status_code == 409 or "already exists" in resp.text.lower() or "已存在" in resp.text:
            # 幂等处理：重复执行时复用已存在意图，保证后续步骤可继续
            list_resp = client.get(
                api_url(base_url, "/intents"),
                params={"limit": 200, "skip": 0},
                headers=auth_headers(token),
                timeout=15,
            )
            if list_resp.status_code == 200:
                items = list_resp.json().get("items", [])
                existed = next((x for x in items if x.get("intent_key") == payload["intent_key"]), None)
                if existed and existed.get("id"):
                    created_resources["intent_id"] = existed["id"]
                    return StepResult("创建意图", True, f"意图已存在（复用），ID: {existed['id']}")
            return StepResult("创建意图", False, f"意图已存在但未能获取 intent_id，HTTP {resp.status_code}")
        return StepResult("创建意图", False, f"HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        return StepResult("创建意图", False, str(e))


# ────────────────────────────────────────────────────────────
# 步骤 4：添加训练数据
# ────────────────────────────────────────────────────────────
def step_add_training_data(client: httpx.Client, base_url: str) -> StepResult:
    print_step(4, "添加训练数据 (POST /intents/{id}/training-data/batch)")
    token = created_resources.get("token", "")
    intent_id = created_resources.get("intent_id")
    if not intent_id:
        return StepResult("添加训练数据", False, "前置步骤未获取到 intent_id，跳过")

    training_samples = [
        {"text": "开始烹饪", "language": "zh"},
        {"text": "启动烹饪", "language": "zh"},
        {"text": "开始做饭", "language": "zh"},
        {"text": "Start cooking", "language": "en"},
    ]
    try:
        resp = client.post(
            api_url(base_url, f"/intents/{intent_id}/training-data/batch"),
            json=training_samples,
            headers=auth_headers(token),
            timeout=15,
        )
        if resp.status_code == 201:
            data = resp.json()
            return StepResult("添加训练数据", True, f"成功添加 {len(data)} 条训练数据")
        return StepResult("添加训练数据", False, f"HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        return StepResult("添加训练数据", False, str(e))


# ────────────────────────────────────────────────────────────
# 步骤 5：创建知识库并上传文档
# ────────────────────────────────────────────────────────────
def step_create_knowledge_base(client: httpx.Client, base_url: str) -> StepResult:
    print_step(5, "创建知识库并上传文档 (POST /knowledge/bases + /upload)")
    token = created_resources.get("token", "")

    try:
        # 5a: 创建知识库
        resp = client.post(
            api_url(base_url, "/knowledge/bases"),
            json={"name": "快速验证菜谱库", "description": "quickstart 验证脚本创建"},
            headers=auth_headers(token),
            timeout=15,
        )
        if resp.status_code not in (200, 201):
            return StepResult("创建知识库", False, f"创建失败 HTTP {resp.status_code}: {resp.text}")

        kb_id = resp.json()["id"]
        created_resources["kb_id"] = kb_id

        # 5b: 上传 Markdown 菜谱文档
        doc_content = """# 柠香雪梨银耳汤

## 基本描述
清甜可口的养生甜品，适合秋冬季节饮用。

## 食材配料
### 主料
- 银耳 1朵（约15g干品）
- 雪梨 1个

### 辅料
- 枸杞 10粒
- 红枣 5颗
- 冰糖 30g
- 柠檬 2片

## 烹饪步骤
1. 银耳提前泡发4小时，去蒂撕成小朵
2. 雪梨去皮去核，切小块
3. 锅中加水1500ml，放入银耳大火煮开
4. 转小火炖煮40分钟至银耳出胶
5. 加入雪梨、红枣、冰糖继续煮15分钟
6. 关火前加入枸杞和柠檬片
7. 焖5分钟即可食用

## 营养成分
- 热量: 约120kcal/碗
- 富含膳食纤维和维生素C
"""
        file_bytes = doc_content.encode("utf-8")
        resp_upload = client.post(
            api_url(base_url, f"/knowledge/bases/{kb_id}/upload"),
            files={"file": ("柠香雪梨银耳汤.md", io.BytesIO(file_bytes), "text/markdown")},
            headers=auth_headers(token),
            timeout=30,
        )
        if resp_upload.status_code in (200, 201):
            doc_data = resp_upload.json()
            created_resources["doc_id"] = doc_data["id"]
            return StepResult(
                "创建知识库 + 上传文档",
                True,
                f"知识库 ID: {kb_id}\n文档: {doc_data.get('title', '未知')}, 索引状态: {doc_data.get('index_status', '未知')}",
            )
        return StepResult(
            "创建知识库 + 上传文档",
            False,
            f"知识库已创建（ID: {kb_id}），但文档上传失败 HTTP {resp_upload.status_code}: {resp_upload.text}",
        )
    except Exception as e:
        return StepResult("创建知识库 + 上传文档", False, str(e))


# ────────────────────────────────────────────────────────────
# 步骤 6：创建对话方案
# ────────────────────────────────────────────────────────────
def step_create_profile(client: httpx.Client, base_url: str) -> StepResult:
    print_step(6, "创建对话方案 (POST /profiles)")
    token = created_resources.get("token", "")
    intent_id = created_resources.get("intent_id")
    kb_id = created_resources.get("kb_id")

    payload = {
        "name": "快速验证方案",
        "description": "quickstart 验证脚本自动创建的对话方案",
        "llm_provider": "openai/gpt-4o",
        "llm_config": {"temperature": 0.7, "max_tokens": 512},
        "routing_strategy": "command_first",
        "session_timeout_minutes": 10,
    }
    if intent_id:
        payload["intent_ids"] = [intent_id]
    if kb_id:
        payload["knowledge_base_ids"] = [kb_id]

    try:
        resp = client.post(
            api_url(base_url, "/profiles"),
            json=payload,
            headers=auth_headers(token),
            timeout=15,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            profile_id = data["id"]
            created_resources["profile_id"] = profile_id
            return StepResult(
                "创建对话方案",
                True,
                f"方案 ID: {profile_id}\n名称: {data['name']}, 路由策略: {data.get('routing_strategy')}",
            )
        return StepResult("创建对话方案", False, f"HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        return StepResult("创建对话方案", False, str(e))


# ────────────────────────────────────────────────────────────
# 步骤 7：发布版本
# ────────────────────────────────────────────────────────────
def step_publish_version(client: httpx.Client, base_url: str) -> StepResult:
    print_step(7, "发布版本 (POST /versions)")
    token = created_resources.get("token", "")
    profile_id = created_resources.get("profile_id")
    if not profile_id:
        return StepResult("发布版本", False, "前置步骤未获取到 profile_id，跳过")

    version_tag = f"quickstart-verify-{int(time.time())}"
    try:
        resp = client.post(
            api_url(base_url, "/versions"),
            params={
                "profile_id": profile_id,
                "version_tag": version_tag,
                "description": "quickstart 验证脚本发布",
            },
            headers=auth_headers(token),
            timeout=15,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            created_resources["version_id"] = data.get("id", "")
            return StepResult(
                "发布版本",
                True,
                f"版本: {version_tag}\n已清理会话数: {data.get('sessions_cleared', 0)}",
            )
        return StepResult("发布版本", False, f"HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        return StepResult("发布版本", False, str(e))


# ────────────────────────────────────────────────────────────
# 步骤 8：查询当前活跃版本
# ────────────────────────────────────────────────────────────
def step_check_version(client: httpx.Client, base_url: str) -> StepResult:
    print_step(8, "查询活跃版本 (GET /dialog/version)")
    try:
        resp = client.get(api_url(base_url, "/dialog/version"), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("active"):
                return StepResult(
                    "查询活跃版本",
                    True,
                    f"版本: {data.get('version_tag')}, 方案 ID: {data.get('profile_id')}",
                )
            return StepResult("查询活跃版本", False, "无活跃版本")
        return StepResult("查询活跃版本", False, f"HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        return StepResult("查询活跃版本", False, str(e))


# ────────────────────────────────────────────────────────────
# 步骤 9：测试对话 API（设备端）
# ────────────────────────────────────────────────────────────
def step_test_dialog(client: httpx.Client, base_url: str) -> StepResult:
    print_step(9, "测试对话 API (POST /dialog/chat)")

    test_cases = [
        {
            "device_id": "quickstart_test_device",
            "text": "开始烹饪",
            "device_context": {"cooking_status": "idle", "door_closed": True, "current_temp": 25},
        },
        {
            "device_id": "quickstart_test_device",
            "text": "柠香雪梨银耳汤需要哪些食材",
        },
    ]

    results_detail = []
    all_ok = True
    for i, case in enumerate(test_cases, 1):
        try:
            attempt = 0
            while True:
                resp = client.post(
                    api_url(base_url, "/dialog/chat"),
                    json=case,
                    timeout=30,
                )
                if resp.status_code != 429 or attempt >= 2:
                    break
                retry_after = resp.headers.get("Retry-After")
                wait_s = float(retry_after) if retry_after else 0.2
                time.sleep(max(wait_s, 0.2))
                attempt += 1

            if resp.status_code == 200:
                data = resp.json()
                results_detail.append(
                    f"[{i}] \"{case['text']}\" → 域: {data.get('domain')}, "
                    f"意图: {data.get('intent', '-')}, "
                    f"回复: {(data.get('response_text', '') or '')[:60]}..."
                )
            else:
                results_detail.append(
                    f"[{i}] \"{case['text']}\" → HTTP {resp.status_code}: {resp.text[:100]}"
                )
                all_ok = False
        except Exception as e:
            results_detail.append(f"[{i}] \"{case['text']}\" → 异常: {e}")
            all_ok = False

    return StepResult("测试对话 API", all_ok, "\n".join(results_detail))


# ────────────────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="SmartChef 快速启动端到端验证")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="后端服务地址")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="管理员用户名")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="管理员密码")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    print("╔══════════════════════════════════════════════════════════╗")
    print("║     SmartChef 快速启动端到端验证                         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  后端地址: {base_url}")
    print(f"  用户名:   {args.username}")

    steps = [
        lambda c: step_health_check(c, base_url),
        lambda c: step_login(c, base_url, args.username, args.password),
        lambda c: step_create_intent(c, base_url),
        lambda c: step_add_training_data(c, base_url),
        lambda c: step_create_knowledge_base(c, base_url),
        lambda c: step_create_profile(c, base_url),
        lambda c: step_publish_version(c, base_url),
        lambda c: step_check_version(c, base_url),
        lambda c: step_test_dialog(c, base_url),
    ]

    results: list[StepResult] = []
    start_time = time.time()

    with httpx.Client() as client:
        for step_fn in steps:
            result = step_fn(client)
            results.append(result)
            print_result(result)

            # 如果健康检查或登录失败，后续步骤无法继续
            if not result.success and result.name in ("健康检查", "登录"):
                print(f"\n[STOP] 关键步骤「{result.name}」失败，终止后续验证。")
                break

    elapsed = time.time() - start_time

    # 汇总报告
    print(f"\n{'='*60}")
    print("  验证结果汇总")
    print(f"{'='*60}")

    passed = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    for r in results:
        icon = "[OK]" if r.success else "[FAIL]"
        print(f"  {icon} {r.name}")

    print(f"\n  总计: {len(results)} 步 | 通过: {passed} | 失败: {failed} | 耗时: {elapsed:.1f}s")

    if failed == 0:
        print("\n[PASS] 所有验证步骤通过！SmartChef 快速启动流程正常。")
    else:
        print(f"\n[WARN] 有 {failed} 个步骤失败，请检查上述错误信息。")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()




