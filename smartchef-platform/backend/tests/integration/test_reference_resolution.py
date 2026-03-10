"""指代消解 / 省略恢复集成测试。

覆盖场景（US7/FR-023）：
1. 代词消解："搜个红烧肉" → "收藏它" → "它"正确消解为"红烧肉"
2. 省略恢复："设置温度180度" → "再高一点" → 温度调高（依赖上下文）
3. 省略恢复："暂停烹饪" → "继续" → 继续烹饪（依赖上下文）
4. 多实体："它"指向最近实体
5. 无上下文时指代消解返回原文
6. 实体栈溢出/清除场景
"""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.nlu.reference_resolver import resolve_references
from app.services.nlu.pipeline import run_pipeline, PipelineConfig
from app.services.session.device_session import create_session, update_session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class FakeRedis:
    """内存版 Redis 替身，支持 get / set / delete 基本操作。"""

    def __init__(self):
        self._store: dict[str, tuple[str, int | None]] = {}

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        return entry[0] if entry else None

    async def set(self, key: str, value: str, *, ex: int | None = None) -> None:
        self._store[key] = (value, ex)

    async def delete(self, *keys: str) -> None:
        for k in keys:
            self._store.pop(k, None)

    async def scan(self, cursor: int, *, match: str = "*", count: int = 100):
        return 0, []


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest.fixture
def mock_db():
    """AsyncSession 替身，外部依赖由 mock 接管。"""
    return AsyncMock()


# 意图列表：含 search_recipe（food_name）、set_cooking_temp（number）、voice_cmd_continue_cooking
REGISTERED_INTENTS = [
    {"intent_key": "voice_cmd_start_cooking", "display_name": "开始烹饪", "category": "烹饪控制",
     "training_texts": ["开始烹饪", "开始加热"], "slots": []},
    {"intent_key": "voice_cmd_stop_cooking", "display_name": "停止烹饪", "category": "烹饪控制",
     "training_texts": ["停止烹饪", "关火", "熄火"], "slots": []},
    {"intent_key": "voice_cmd_pause_cooking", "display_name": "暂停烹饪", "category": "烹饪控制",
     "training_texts": ["暂停烹饪", "暂停一下"], "slots": []},
    {"intent_key": "voice_cmd_continue_cooking", "display_name": "继续烹饪", "category": "烹饪控制",
     "training_texts": ["继续", "继续烹饪", "继续加热"], "slots": []},
    {"intent_key": "set_cooking_temp", "display_name": "设置温度", "category": "烹饪控制",
     "training_texts": ["设置温度", "加热到", "调温度"],
     "slots": [{"slot_key": "number", "entity_type": "number", "is_required": True,
               "display_name": "温度", "prompt_text": "请问您要设置多少度？"}]},
    {"intent_key": "search_recipe", "display_name": "搜索菜谱", "category": "菜谱管理",
     "training_texts": ["搜索菜谱", "搜个菜谱", "搜个红烧肉", "搜一下", "查找菜谱"],
     "slots": [{"slot_key": "food_name", "entity_type": "food_name", "is_required": False,
               "display_name": "菜名"}]},
]


def _make_config(**overrides) -> PipelineConfig:
    defaults = dict(
        registered_intents=REGISTERED_INTENTS,
        has_knowledge_base=True,
        routing_strategy="command_first",
        knowledge_base_ids=[uuid4()],
    )
    defaults.update(overrides)
    return PipelineConfig(**defaults)


# ---------------------------------------------------------------------------
# 一、指代消解（resolve_references）单元级测试
# ---------------------------------------------------------------------------

class TestResolveReferences:
    """直接测试 reference_resolver 模块，不依赖 pipeline。"""

    @pytest.mark.asyncio
    async def test_resolve_ta_to_entity(self):
        """「它」正确消解为 entity_stack 中最远实体。"""
        entity_stack = [{"type": "food_name", "value": "红烧肉", "turn": 1}]
        resolved_text, resolved_entities = resolve_references("收藏它", entity_stack)
        assert resolved_text == "收藏红烧肉"
        assert len(resolved_entities) == 1
        assert resolved_entities[0]["pronoun"] == "它"
        assert resolved_entities[0]["resolved_to"] == "红烧肉"

    @pytest.mark.asyncio
    async def test_resolve_zhege_nage(self):
        """「这个」「那个」等代词可消解。"""
        entity_stack = [{"type": "food_name", "value": "红烧肉", "turn": 1}]
        for pronoun in ["这个", "那个"]:
            text = f"收藏{pronoun}"
            resolved_text, resolved_entities = resolve_references(text, entity_stack)
            assert "红烧肉" in resolved_text
            assert resolved_entities[0]["pronoun"] == pronoun

    @pytest.mark.asyncio
    async def test_multiple_entities_ta_points_to_most_recent(self):
        """多个实体存在时，「它」指向最近（栈顶）实体。"""
        entity_stack = [
            {"type": "food_name", "value": "红烧肉", "turn": 1},
            {"type": "food_name", "value": "糖醋排骨", "turn": 2},
        ]
        resolved_text, resolved_entities = resolve_references("收藏它", entity_stack)
        assert resolved_text == "收藏糖醋排骨"
        assert resolved_entities[0]["resolved_to"] == "糖醋排骨"

    @pytest.mark.asyncio
    async def test_no_context_returns_original(self):
        """无 entity_stack 时，返回原文，resolved_entities 为空。"""
        resolved_text, resolved_entities = resolve_references("收藏它", [])
        assert resolved_text == "收藏它"
        assert resolved_entities == []

    @pytest.mark.asyncio
    async def test_no_pronoun_returns_original(self):
        """无代词时，原文不变。"""
        entity_stack = [{"type": "food_name", "value": "红烧肉", "turn": 1}]
        resolved_text, resolved_entities = resolve_references("收藏红烧肉", entity_stack)
        assert resolved_text == "收藏红烧肉"
        assert resolved_entities == []

    @pytest.mark.asyncio
    async def test_resolve_gangcai_nage(self):
        """「刚才那个」可消解为栈顶实体。"""
        entity_stack = [{"type": "food_name", "value": "糖醋排骨", "turn": 2}]
        resolved_text, resolved_entities = resolve_references("收藏刚才那个", entity_stack)
        assert resolved_text == "收藏糖醋排骨"
        assert resolved_entities[0]["pronoun"] == "刚才那个"

    @pytest.mark.asyncio
    async def test_resolve_shangyige_points_to_second(self):
        """多个实体时，「上一个」指向倒数第二。"""
        entity_stack = [
            {"type": "food_name", "value": "红烧肉", "turn": 1},
            {"type": "food_name", "value": "糖醋排骨", "turn": 2},
        ]
        resolved_text, resolved_entities = resolve_references("收藏上一个", entity_stack)
        assert resolved_text == "收藏红烧肉"
        assert resolved_entities[0]["resolved_to"] == "红烧肉"

    @pytest.mark.asyncio
    async def test_resolve_partial_zhege_caipu(self):
        """部分指代「这个菜谱」→ 实体值 + 类别词（代词消解或部分指代均可达成）。"""
        entity_stack = [{"type": "food_name", "value": "红烧肉", "turn": 1}]
        resolved_text, resolved_entities = resolve_references("收藏这个菜谱", entity_stack)
        assert resolved_text == "收藏红烧肉菜谱"
        assert resolved_entities[0]["resolved_to"] == "红烧肉"

    @pytest.mark.asyncio
    async def test_ellipsis_recovery_short_input(self):
        """输入短（<5字）且有实体时，省略恢复拼接上下文。"""
        entity_stack = [{"type": "number", "value": "180", "turn": 1}]
        resolved_text, resolved_entities = resolve_references("再高一点", entity_stack)
        assert "温度180" in resolved_text
        assert "再高一点" in resolved_text
        assert any(rr.get("ellipsis_recovery") for rr in resolved_entities)

    @pytest.mark.asyncio
    async def test_ellipsis_recovery_not_triggered_when_long(self):
        """输入 >=5 字时，不触发省略恢复。"""
        entity_stack = [{"type": "number", "value": "180", "turn": 1}]
        resolved_text, resolved_entities = resolve_references("把温度再调高一点", entity_stack)
        assert resolved_text == "把温度再调高一点"
        assert not any(rr.get("ellipsis_recovery", False) for rr in resolved_entities)


# ---------------------------------------------------------------------------
# 二、Pipeline 集成测试：指代消解
# ---------------------------------------------------------------------------

class TestPipelineReferenceResolution:
    """通过 run_pipeline 验证指代消解在 pipeline 中的调用与 session 一致性。"""

    @pytest.mark.asyncio
    async def test_search_then_save_it_resolves_to_hongshao(self, mock_db, fake_redis):
        """「搜个红烧肉」→「收藏它」：它正确消解为红烧肉。"""
        config = _make_config()

        # 第一轮：搜个红烧肉，槽位 food_name=红烧肉 入 entity_stack
        r1 = await run_pipeline(
            mock_db, fake_redis, "搜个红烧肉", device_id="dev-ref-01", config=config,
        )
        assert r1.domain == "command"
        assert r1.intent == "search_recipe"
        assert r1.slots.get("food_name") == "红烧肉"

        # 第二轮：收藏它 → 指代消解后为「收藏红烧肉」
        r2 = await run_pipeline(
            mock_db, fake_redis, "收藏它", device_id="dev-ref-01", config=config,
        )
        assert "reference_resolution" in r2.debug_info
        refs = r2.debug_info["reference_resolution"]
        assert len(refs) >= 1
        assert any(r["pronoun"] == "它" and r["resolved_to"] == "红烧肉" for r in refs)

    @pytest.mark.asyncio
    async def test_set_temp_then_zai_gao_yidian_ellipsis_recovery(self, mock_db, fake_redis):
        """「设置温度180度」→「再高一点」：无代词，省略恢复从上下文继承温度实体。"""
        config = _make_config()

        r1 = await run_pipeline(
            mock_db, fake_redis, "设置温度180度", device_id="dev-ref-02", config=config,
        )
        assert r1.domain == "command"
        assert r1.intent == "set_cooking_temp"
        assert r1.slots.get("number") == "180"

        # 「再高一点」不含代词，触发省略恢复，继承温度180
        r2 = await run_pipeline(
            mock_db, fake_redis, "再高一点", device_id="dev-ref-02", config=config,
        )
        assert r2.domain is not None
        refs = r2.debug_info.get("reference_resolution", [])
        assert any(rr.get("ellipsis_recovery") and rr.get("entity_value") == "180" for rr in refs)

    @pytest.mark.asyncio
    async def test_pause_then_continue(self, mock_db, fake_redis):
        """「暂停烹饪」→「继续」：继续烹饪意图可被识别。"""
        config = _make_config()

        r1 = await run_pipeline(
            mock_db, fake_redis, "暂停烹饪", device_id="dev-ref-03", config=config,
        )
        assert r1.domain == "command"
        assert r1.intent == "voice_cmd_pause_cooking"

        r2 = await run_pipeline(
            mock_db, fake_redis, "继续", device_id="dev-ref-03", config=config,
        )
        assert r2.domain == "command"
        assert r2.intent == "voice_cmd_continue_cooking"

    @pytest.mark.asyncio
    async def test_prepopulated_entity_stack_resolution(self, mock_db, fake_redis):
        """预置 entity_stack 后，「收藏它」正确消解。"""
        config = _make_config()
        device_id = "dev-ref-04"

        session = await create_session(fake_redis, device_id, timeout_minutes=10)
        session["entity_stack"].append({"type": "food_name", "value": "红烧肉", "turn": 1})
        await update_session(fake_redis, device_id, session, 10)

        r = await run_pipeline(mock_db, fake_redis, "收藏它", device_id=device_id, config=config)

        assert "reference_resolution" in r.debug_info
        refs = r.debug_info["reference_resolution"]
        assert any(rr["resolved_to"] == "红烧肉" for rr in refs)

    @pytest.mark.asyncio
    async def test_no_context_collect_it_unchanged(self, mock_db, fake_redis):
        """无上下文时，「收藏它」无指代消解，原文进入下游。"""
        config = _make_config()
        device_id = "dev-ref-05"

        # 新设备，无历史，entity_stack 为空
        r = await run_pipeline(mock_db, fake_redis, "收藏它", device_id=device_id, config=config)

        assert "reference_resolution" not in r.debug_info or r.debug_info.get("reference_resolution") == []


# ---------------------------------------------------------------------------
# 三、实体栈溢出 / 清除
# ---------------------------------------------------------------------------

class TestEntityStackOverflow:
    """实体栈容量限制及清除场景。"""

    @pytest.mark.asyncio
    async def test_entity_stack_overflow_truncation(self, mock_db, fake_redis):
        """entity_stack 超过 20 项时，保留最近 20 项；「它」仍指向栈顶。"""
        from app.services.session.device_session import add_dialog_turn

        config = _make_config()
        device_id = "dev-ref-06"

        session = await create_session(fake_redis, device_id, timeout_minutes=10)
        for i in range(25):
            session["entity_stack"].append({"type": "food_name", "value": f"菜品{i}", "turn": i + 1})
        if len(session["entity_stack"]) > 20:
            session["entity_stack"] = session["entity_stack"][-20:]
        await update_session(fake_redis, device_id, session, 10)

        # 栈顶应为 菜品24（第 25 个，索引 24）
        r = await run_pipeline(mock_db, fake_redis, "收藏它", device_id=device_id, config=config)

        assert "reference_resolution" in r.debug_info
        refs = r.debug_info["reference_resolution"]
        assert any(rr["resolved_to"] == "菜品24" for rr in refs)

    @pytest.mark.asyncio
    async def test_resolve_references_empty_stack_handling(self):
        """resolve_references 对空栈安全：直接返回原文。"""
        for text in ["收藏它", "这个", "再高一点", "继续"]:
            resolved_text, resolved_entities = resolve_references(text, [])
            assert resolved_text == text
            assert resolved_entities == []
