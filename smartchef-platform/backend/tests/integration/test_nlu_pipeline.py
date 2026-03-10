"""NLU Pipeline 端到端集成测试。

覆盖指令域、知识域、闲聊域的路由和处理，
mock 外部依赖（Redis、LLM API、知识检索），保持组件间真实交互。
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.nlu.pipeline import run_pipeline, PipelineConfig, PipelineResult


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
    """AsyncSession 替身，知识域测试中由 generate_knowledge_answer mock 接管。"""
    return AsyncMock()


# 代表性意图注册列表（来自 spec.md 39 个意图中的典型子集）
REGISTERED_INTENTS = [
    {
        "intent_key": "voice_cmd_start_cooking",
        "display_name": "开始烹饪",
        "category": "烹饪控制",
        "training_texts": ["开始烹饪", "开始加热", "启动烹饪"],
        "slots": [],
    },
    {
        "intent_key": "voice_cmd_stop_cooking",
        "display_name": "停止烹饪",
        "category": "烹饪控制",
        "training_texts": ["停止烹饪", "关火", "熄火", "把火关了", "停止加热"],
        "slots": [],
    },
    {
        "intent_key": "voice_cmd_pause_cooking",
        "display_name": "暂停烹饪",
        "category": "烹饪控制",
        "training_texts": ["暂停烹饪", "暂停一下", "暂停加热"],
        "slots": [],
    },
    {
        "intent_key": "set_cooking_temp",
        "display_name": "设置温度",
        "category": "烹饪控制",
        "training_texts": ["设置温度", "加热到", "调温度", "温度设为"],
        "slots": [
            {"slot_key": "number", "entity_type": "number", "is_required": True,
             "display_name": "温度", "prompt_text": "请问您要设置多少度？"},
        ],
    },
    {
        "intent_key": "set_cooking_time",
        "display_name": "设置烹饪时间",
        "category": "烹饪控制",
        "training_texts": ["设置时间", "定时", "烹饪时间", "加热时间"],
        "slots": [
            {"slot_key": "duration", "entity_type": "time", "is_required": True,
             "display_name": "时长", "prompt_text": "请问您要加热多长时间？"},
        ],
    },
    {
        "intent_key": "voice_cmd_cancel",
        "display_name": "取消操作",
        "category": "系统控制",
        "training_texts": ["取消", "取消操作", "算了", "不要了"],
        "slots": [],
    },
    {
        "intent_key": "search_recipe",
        "display_name": "搜索菜谱",
        "category": "菜谱管理",
        "training_texts": ["搜索菜谱", "搜个菜谱", "搜一下", "查找菜谱"],
        "slots": [
            {"slot_key": "food_name", "entity_type": "food_name", "is_required": False,
             "display_name": "菜名"},
        ],
    },
    {
        "intent_key": "set_volume",
        "display_name": "音量",
        "category": "系统控制",
        "training_texts": ["音量调高", "调大音量", "音量设置", "声音大一点"],
        "slots": [
            {"slot_key": "number", "entity_type": "number", "is_required": False,
             "display_name": "音量值"},
        ],
    },
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
# 一、指令域测试
# ---------------------------------------------------------------------------

class TestCommandDomain:
    """指令域：路由 → 意图分类 → 槽位提取 → 结构化返回。"""

    @pytest.mark.asyncio
    async def test_start_cooking_command(self, mock_db, fake_redis):
        """'开始烹饪' → 路由到指令域，识别 voice_cmd_start_cooking。"""
        result = await run_pipeline(
            mock_db, fake_redis, "开始烹饪", device_id="dev-001", config=_make_config(),
        )

        assert result.domain == "command"
        assert result.intent == "voice_cmd_start_cooking"
        assert result.route_confidence > 0.5
        assert result.intent_confidence > 0
        assert "烹饪" in result.response_text or "开始" in result.response_text
        assert result.session_id is not None

    @pytest.mark.asyncio
    async def test_set_temperature_with_slot(self, mock_db, fake_redis):
        """'设置温度180度' → 指令域 + 槽位 number=180。"""
        result = await run_pipeline(
            mock_db, fake_redis, "设置温度180度", device_id="dev-002", config=_make_config(),
        )

        assert result.domain == "command"
        assert result.intent == "set_cooking_temp"
        assert "number" in result.slots
        assert result.slots["number"] == "180"
        assert not result.needs_followup

    @pytest.mark.asyncio
    async def test_set_cooking_time_with_duration(self, mock_db, fake_redis):
        """'定时5分钟' → 指令域 + 槽位 duration=5。"""
        result = await run_pipeline(
            mock_db, fake_redis, "定时5分钟", device_id="dev-003", config=_make_config(),
        )

        assert result.domain == "command"
        assert result.intent == "set_cooking_time"
        assert "duration" in result.slots
        assert result.slots["duration"] == "5"

    @pytest.mark.asyncio
    async def test_stop_cooking_synonyms(self, mock_db, fake_redis):
        """'关火' / '停止烹饪' 等同义表达均路由到 voice_cmd_stop_cooking。"""
        for text in ["关火", "停止烹饪", "停止加热"]:
            result = await run_pipeline(
                mock_db, fake_redis, text, device_id="dev-004", config=_make_config(),
            )
            assert result.domain == "command", f"'{text}' 应路由到 command"
            assert result.intent == "voice_cmd_stop_cooking", f"'{text}' 应识别为 stop_cooking"

    @pytest.mark.asyncio
    async def test_pause_cooking(self, mock_db, fake_redis):
        """'暂停烹饪' → 指令域，识别 voice_cmd_pause_cooking。"""
        result = await run_pipeline(
            mock_db, fake_redis, "暂停烹饪", device_id="dev-005", config=_make_config(),
        )

        assert result.domain == "command"
        assert result.intent == "voice_cmd_pause_cooking"

    @pytest.mark.asyncio
    async def test_cancel_operation(self, mock_db, fake_redis):
        """'取消操作' → 指令域，识别 voice_cmd_cancel。"""
        result = await run_pipeline(
            mock_db, fake_redis, "取消操作", device_id="dev-006", config=_make_config(),
        )

        assert result.domain == "command"
        assert result.intent == "voice_cmd_cancel"

    @pytest.mark.asyncio
    async def test_search_recipe_with_food_name(self, mock_db, fake_redis):
        """'搜索红烧肉菜谱' → 指令域 + 槽位 food_name 提取。"""
        result = await run_pipeline(
            mock_db, fake_redis, "搜索红烧肉菜谱", device_id="dev-007", config=_make_config(),
        )

        assert result.domain == "command"
        assert result.intent == "search_recipe"

    @pytest.mark.asyncio
    async def test_set_volume(self, mock_db, fake_redis):
        """'音量调高' → 指令域，识别 set_volume。"""
        result = await run_pipeline(
            mock_db, fake_redis, "音量调高", device_id="dev-008", config=_make_config(),
        )

        assert result.domain == "command"
        assert result.intent == "set_volume"

    @pytest.mark.asyncio
    async def test_high_risk_temperature_warning(self, mock_db, fake_redis):
        """设置温度超过 200℃ 触发高风险二次确认。"""
        result = await run_pipeline(
            mock_db, fake_redis, "设置温度250度", device_id="dev-009", config=_make_config(),
        )

        assert result.domain == "command"
        assert result.intent == "set_cooking_temp"
        assert result.needs_followup  # 高风险时为 truthy（字符串描述）
        assert "高风险" in result.response_text or "确认" in result.response_text

    @pytest.mark.asyncio
    async def test_command_response_contains_debug_info(self, mock_db, fake_redis):
        """指令域返回结果应包含完整 debug_info。"""
        result = await run_pipeline(
            mock_db, fake_redis, "开始烹饪", device_id="dev-010", config=_make_config(),
        )

        assert "preprocessed" in result.debug_info
        assert "routing" in result.debug_info
        assert result.debug_info["routing"]["domain"] == "command"
        assert "intent" in result.debug_info
        assert "slots" in result.debug_info

    @pytest.mark.asyncio
    async def test_english_start_cooking(self, mock_db, fake_redis):
        """英文 'Start cooking' → 指令域，英文回复。"""
        config = _make_config(registered_intents=[
            {
                "intent_key": "voice_cmd_start_cooking",
                "display_name": "start cooking",
                "category": "cooking_control",
                "training_texts": ["start cooking", "begin cooking", "cook now"],
                "slots": [],
            },
        ])
        result = await run_pipeline(
            mock_db, fake_redis, "Start cooking", device_id="dev-011", config=config,
        )

        assert result.domain == "command"
        assert result.language == "en"


# ---------------------------------------------------------------------------
# 二、知识域测试
# ---------------------------------------------------------------------------

class TestKnowledgeDomain:
    """知识域：路由 → 知识检索 → 生成回答。"""

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.generate_knowledge_answer")
    async def test_knowledge_query_hit(self, mock_gen, mock_db, fake_redis):
        """'红烧肉怎么做' → 知识域，知识库命中时返回回答。"""
        mock_gen.return_value = (
            "红烧肉做法：五花肉切块焯水，冰糖炒色后加入调料慢炖一小时。",
            [{"document_title": "红烧肉", "chunk_text": "...", "score": 0.85}],
        )

        config = _make_config(routing_strategy="balanced")
        result = await run_pipeline(
            mock_db, fake_redis, "红烧肉怎么做", device_id="dev-020", config=config,
        )

        assert result.domain == "knowledge"
        assert "红烧肉" in result.response_text
        assert result.route_confidence > 0.5
        assert result.session_id is not None
        mock_gen.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    @patch("app.services.nlu.pipeline.generate_knowledge_answer")
    async def test_knowledge_miss_fallback_to_chitchat(self, mock_gen, mock_chat, mock_db, fake_redis):
        """知识库未命中时降级到闲聊域。"""
        mock_gen.return_value = (None, [])
        mock_chat.return_value = "这道菜我不太了解，你可以试试在网上搜索哦。"

        config = _make_config(routing_strategy="balanced")
        result = await run_pipeline(
            mock_db, fake_redis, "红烧肉怎么做", device_id="dev-021", config=config,
        )

        assert result.domain == "chitchat"
        assert len(result.response_text) > 0
        mock_chat.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.generate_knowledge_answer")
    async def test_knowledge_nutrition_query(self, mock_gen, mock_db, fake_redis):
        """'鸡蛋的热量是多少' → 知识域，营养相关查询。"""
        mock_gen.return_value = (
            "一个中等大小的鸡蛋约含 70 大卡热量。",
            [{"document_title": "鸡蛋营养", "chunk_text": "...", "score": 0.78}],
        )

        config = _make_config(routing_strategy="balanced")
        result = await run_pipeline(
            mock_db, fake_redis, "鸡蛋的热量是多少", device_id="dev-022", config=config,
        )

        assert result.domain == "knowledge"
        assert "热量" in result.response_text or "卡" in result.response_text


# ---------------------------------------------------------------------------
# 三、闲聊域测试
# ---------------------------------------------------------------------------

class TestChitchatDomain:
    """闲聊域：路由 → LLM 生成回复，含 web search 增强。"""

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.brave_search", new_callable=AsyncMock)
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_weather_chitchat_with_web_search(self, mock_chat, mock_brave, mock_db, fake_redis):
        """'今天天气怎么样' → 闲聊域，触发 web search 增强。"""
        mock_brave.return_value = [
            {"title": "今日天气", "description": "晴转多云，25℃", "url": "https://example.com"},
        ]
        mock_chat.return_value = "今天天气不错，晴转多云，大概25度左右。"

        config = _make_config(routing_strategy="balanced")
        result = await run_pipeline(
            mock_db, fake_redis, "今天天气怎么样", device_id="dev-030", config=config,
        )

        assert result.domain == "chitchat"
        assert len(result.response_text) > 0
        mock_brave.assert_awaited_once()
        mock_chat.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_greeting_chitchat(self, mock_chat, mock_db, fake_redis):
        """'你好' → 闲聊域，简单寒暄。"""
        mock_chat.return_value = "你好呀！我是 SmartChef 智能厨房助手，有什么可以帮你的吗？"

        config = _make_config(routing_strategy="balanced")
        result = await run_pipeline(
            mock_db, fake_redis, "你好", device_id="dev-031", config=config,
        )

        assert result.domain == "chitchat"
        assert "你好" in result.response_text or "SmartChef" in result.response_text

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_joke_chitchat(self, mock_chat, mock_db, fake_redis):
        """'讲个笑话' → 闲聊域。"""
        mock_chat.return_value = "好的，来一个：为什么厨师总是迟到？因为他们总在'加班'（加热）！"

        config = _make_config(routing_strategy="balanced")
        result = await run_pipeline(
            mock_db, fake_redis, "讲个笑话", device_id="dev-032", config=config,
        )

        assert result.domain == "chitchat"
        assert len(result.response_text) > 0

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_chitchat_persona_prompt(self, mock_chat, mock_db, fake_redis):
        """验证闲聊域传递自定义 persona 到 LLM system prompt。"""
        mock_chat.return_value = "我是小厨，很高兴为你服务！"

        config = _make_config(
            routing_strategy="balanced",
            persona_data={"name": "小厨", "personality": "活泼可爱", "tone_style": "亲切随和"},
        )
        result = await run_pipeline(
            mock_db, fake_redis, "你好", device_id="dev-033", config=config,
        )

        assert result.domain == "chitchat"
        call_args = mock_chat.call_args
        messages = call_args[0][0] if call_args[0] else call_args[1]["messages"]
        system_msg = messages[0]["content"]
        assert "小厨" in system_msg


# ---------------------------------------------------------------------------
# 四、多轮对话测试
# ---------------------------------------------------------------------------

class TestMultiTurnDialog:
    """多轮对话：连续发送消息，验证上下文保持和状态转换。"""

    @pytest.mark.asyncio
    async def test_slot_filling_multi_turn(self, mock_db, fake_redis):
        """缺少必填槽位时发起追问，下一轮补全槽位完成指令。"""
        config = _make_config()

        # 第一轮：缺少时间槽位 → 追问
        r1 = await run_pipeline(
            mock_db, fake_redis, "设置烹饪时间", device_id="dev-040", config=config,
        )

        assert r1.domain == "command"
        assert r1.intent == "set_cooking_time"
        assert r1.needs_followup is True
        assert "时" in r1.response_text or "多长" in r1.response_text

        # 第二轮：补全时间槽位
        r2 = await run_pipeline(
            mock_db, fake_redis, "5分钟", device_id="dev-040", config=config,
        )

        assert r2.domain == "command"
        assert r2.intent == "set_cooking_time"
        assert "duration" in r2.slots
        assert r2.slots["duration"] == "5"
        assert r2.needs_followup is False

    @pytest.mark.asyncio
    async def test_session_continuity(self, mock_db, fake_redis):
        """同一设备多次请求应复用 session_id。"""
        config = _make_config()

        r1 = await run_pipeline(
            mock_db, fake_redis, "开始烹饪", device_id="dev-041", config=config,
        )
        r2 = await run_pipeline(
            mock_db, fake_redis, "暂停烹饪", device_id="dev-041", config=config,
        )

        assert r1.session_id is not None
        assert r1.session_id == r2.session_id

    @pytest.mark.asyncio
    async def test_session_isolation_between_devices(self, mock_db, fake_redis):
        """不同设备 ID 的会话应完全隔离。"""
        config = _make_config()

        r_a = await run_pipeline(
            mock_db, fake_redis, "开始烹饪", device_id="device-A", config=config,
        )
        r_b = await run_pipeline(
            mock_db, fake_redis, "停止烹饪", device_id="device-B", config=config,
        )

        assert r_a.session_id != r_b.session_id

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_cross_domain_switch(self, mock_chat, mock_db, fake_redis):
        """从闲聊域切换到指令域，验证跨域切换正确性。"""
        mock_chat.return_value = "今天天气不错哦！"
        config = _make_config(routing_strategy="balanced")

        # 第一轮：闲聊
        r1 = await run_pipeline(
            mock_db, fake_redis, "你好", device_id="dev-042", config=config,
        )
        assert r1.domain == "chitchat"

        # 第二轮：切换到指令
        r2 = await run_pipeline(
            mock_db, fake_redis, "暂停烹饪", device_id="dev-042", config=config,
        )
        assert r2.domain == "command"
        assert r2.intent == "voice_cmd_pause_cooking"

    @pytest.mark.asyncio
    async def test_dialog_history_accumulates(self, mock_db, fake_redis):
        """验证对话历史在 session 中累积。"""
        config = _make_config()

        await run_pipeline(mock_db, fake_redis, "开始烹饪", device_id="dev-043", config=config)
        await run_pipeline(mock_db, fake_redis, "暂停烹饪", device_id="dev-043", config=config)
        await run_pipeline(mock_db, fake_redis, "停止烹饪", device_id="dev-043", config=config)

        raw = await fake_redis.get("session:dev-043")
        session = json.loads(raw)
        assert len(session["dialog_history"]) == 3
        assert session["dialog_history"][0]["intent"] == "voice_cmd_start_cooking"
        assert session["dialog_history"][1]["intent"] == "voice_cmd_pause_cooking"
        assert session["dialog_history"][2]["intent"] == "voice_cmd_stop_cooking"


# ---------------------------------------------------------------------------
# 五、边界情况测试
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """空输入、超长文本等边界情况。"""

    @pytest.mark.asyncio
    async def test_empty_input(self, mock_db, fake_redis):
        """空字符串 → domain='error'，提示用户说点什么。"""
        result = await run_pipeline(
            mock_db, fake_redis, "", device_id="dev-050", config=_make_config(),
        )

        assert result.domain == "error"
        assert "请说点什么" in result.response_text

    @pytest.mark.asyncio
    async def test_whitespace_only_input(self, mock_db, fake_redis):
        """纯空白字符 → domain='error'。"""
        result = await run_pipeline(
            mock_db, fake_redis, "   \t\n  ", device_id="dev-051", config=_make_config(),
        )

        assert result.domain == "error"

    @pytest.mark.asyncio
    async def test_overlong_input_truncation(self, mock_db, fake_redis):
        """超长文本（>500字符）应被截断后正常处理。"""
        long_text = "开始烹饪" + "啊" * 600
        result = await run_pipeline(
            mock_db, fake_redis, long_text, device_id="dev-052", config=_make_config(),
        )

        assert result.domain != "error"
        assert result.debug_info["preprocessed"]["truncated"] is True
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_special_characters_cleaned(self, mock_db, fake_redis):
        """含特殊字符的文本应被清洗后正常处理。"""
        result = await run_pipeline(
            mock_db, fake_redis, "开始###烹饪!!!", device_id="dev-053", config=_make_config(),
        )

        assert result.domain == "command"

    @pytest.mark.asyncio
    async def test_latency_ms_positive(self, mock_db, fake_redis):
        """返回的 latency_ms 应为非负整数。"""
        result = await run_pipeline(
            mock_db, fake_redis, "开始烹饪", device_id="dev-054", config=_make_config(),
        )

        assert isinstance(result.latency_ms, int)
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_pipeline_result_structure(self, mock_db, fake_redis):
        """验证 PipelineResult 所有字段类型正确。"""
        result = await run_pipeline(
            mock_db, fake_redis, "开始烹饪", device_id="dev-055", config=_make_config(),
        )

        assert isinstance(result, PipelineResult)
        assert isinstance(result.domain, str)
        assert isinstance(result.route_confidence, float)
        assert isinstance(result.slots, dict)
        assert isinstance(result.response_text, str)
        assert result.needs_followup is None or isinstance(result.needs_followup, (bool, str))
        assert isinstance(result.debug_info, dict)
        assert isinstance(result.language, str)
