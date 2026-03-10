"""跨域切换集成测试 (US7)。

覆盖指令/知识/闲聊三域之间的切换场景，
验证路由正确性、上下文保持与清除、会话状态一致性。
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.nlu.pipeline import run_pipeline, PipelineConfig


# ---------------------------------------------------------------------------
# Fixtures（复用 test_nlu_pipeline 风格）
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
    """AsyncSession 替身，由 mock 接管知识检索等 DB 调用。"""
    return AsyncMock()


# 代表性意图注册（含暂停、停止、开始等）
REGISTERED_INTENTS = [
    {"intent_key": "voice_cmd_start_cooking", "display_name": "开始烹饪", "slots": []},
    {"intent_key": "voice_cmd_stop_cooking", "display_name": "停止烹饪", "slots": []},
    {"intent_key": "voice_cmd_pause_cooking", "display_name": "暂停烹饪", "slots": []},
    {"intent_key": "voice_cmd_cancel", "display_name": "取消操作", "slots": []},
    {"intent_key": "set_cooking_temp", "display_name": "设置温度", "slots": [
        {"slot_key": "number", "entity_type": "number", "is_required": True},
    ]},
    {"intent_key": "search_recipe", "display_name": "搜索菜谱", "slots": []},
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
# 场景 1：闲聊中检测到指令意图 → 切换到指令域
# ---------------------------------------------------------------------------

class TestChitchatToCommand:
    """闲聊中检测到指令意图，应正确切换到指令域。"""

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_chitchat_then_pause_command_switches_to_command(
        self, mock_chat, mock_db, fake_redis
    ):
        """闲聊中说「暂停烹饪」→ 应路由到指令域并识别 voice_cmd_pause_cooking。"""
        mock_chat.return_value = "今天天气不错哦！"
        config = _make_config(routing_strategy="balanced")

        # 第一轮：闲聊（如用户先寒暄）
        r1 = await run_pipeline(
            mock_db, fake_redis, "你好", device_id="dev-x01", config=config,
        )
        assert r1.domain == "chitchat"

        # 第二轮：在闲聊上下文中突然说指令
        r2 = await run_pipeline(
            mock_db, fake_redis, "暂停烹饪", device_id="dev-x01", config=config,
        )
        assert r2.domain == "command"
        assert r2.intent == "voice_cmd_pause_cooking"
        assert r2.session_id == r1.session_id

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_chitchat_then_stop_command_switches_to_command(
        self, mock_chat, mock_db, fake_redis
    ):
        """闲聊后说「停止烹饪」→ 切换到指令域。"""
        mock_chat.return_value = "不客气！"
        config = _make_config(routing_strategy="balanced")

        r1 = await run_pipeline(
            mock_db, fake_redis, "谢谢", device_id="dev-x02", config=config,
        )
        r2 = await run_pipeline(
            mock_db, fake_redis, "停止烹饪", device_id="dev-x02", config=config,
        )
        assert r1.domain == "chitchat"
        assert r2.domain == "command"
        assert r2.intent == "voice_cmd_stop_cooking"


# ---------------------------------------------------------------------------
# 场景 2：指令域完成后 → 回到之前域
# ---------------------------------------------------------------------------

class TestCommandCompleteThenReturnToPrevious:
    """指令执行完成后，下一轮应能根据用户输入路由回闲聊或知识域。"""

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_command_complete_then_chitchat_returns_to_chitchat(
        self, mock_chat, mock_db, fake_redis
    ):
        """指令完成后用户说「谢谢」→ 应路由到闲聊域。"""
        mock_chat.return_value = "好的，已暂停！有什么需要再说。"

        config = _make_config(routing_strategy="balanced")

        # 闲聊
        r1 = await run_pipeline(
            mock_db, fake_redis, "你好", device_id="dev-x03", config=config,
        )
        # 指令
        r2 = await run_pipeline(
            mock_db, fake_redis, "暂停烹饪", device_id="dev-x03", config=config,
        )
        # 指令完成后回到闲聊
        r3 = await run_pipeline(
            mock_db, fake_redis, "谢谢", device_id="dev-x03", config=config,
        )

        assert r1.domain == "chitchat"
        assert r2.domain == "command"
        assert r3.domain == "chitchat"
        assert r1.session_id == r2.session_id == r3.session_id

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_command_complete_then_knowledge_returns_to_knowledge(
        self, mock_chat, mock_db, fake_redis
    ):
        """指令完成后用户问知识类问题 → 应路由到知识域。"""
        mock_chat.return_value = "不客气！"
        config = _make_config(routing_strategy="balanced")

        with patch("app.services.nlu.pipeline.generate_knowledge_answer") as mock_gen:
            mock_gen.return_value = ("红烧肉需要五花肉、冰糖、酱油等。", [{"score": 0.9}])

            r1 = await run_pipeline(
                mock_db, fake_redis, "开始烹饪", device_id="dev-x04", config=config,
            )
            r2 = await run_pipeline(
                mock_db, fake_redis, "红烧肉需要什么食材", device_id="dev-x04", config=config,
            )

        assert r1.domain == "command"
        assert r2.domain == "knowledge"
        assert "红烧肉" in r2.response_text or "食材" in r2.response_text


# ---------------------------------------------------------------------------
# 场景 3：知识域 → 闲聊域切换
# ---------------------------------------------------------------------------

class TestKnowledgeToChitchat:
    """知识域到闲聊域的切换。"""

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    @patch("app.services.nlu.pipeline.generate_knowledge_answer")
    async def test_knowledge_miss_fallbacks_to_chitchat(
        self, mock_gen, mock_chat, mock_db, fake_redis
    ):
        """知识库未命中时自动降级到闲聊域（知识→闲聊切换）。"""
        mock_gen.return_value = (None, [])
        mock_chat.return_value = "这道菜我不太了解，你可以试试在网上搜索哦。"

        config = _make_config(routing_strategy="balanced")
        result = await run_pipeline(
            mock_db, fake_redis, "红烧肉怎么做", device_id="dev-x05", config=config,
        )

        assert result.domain == "chitchat"
        assert len(result.response_text) > 0
        mock_chat.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    @patch("app.services.nlu.pipeline.generate_knowledge_answer")
    async def test_knowledge_hit_then_chitchat_switch(
        self, mock_gen, mock_chat, mock_db, fake_redis
    ):
        """先知识问答命中，再问闲聊问题 → 应切换到闲聊域。"""
        mock_gen.return_value = ("红烧肉做法：…", [{"score": 0.9}])
        mock_chat.return_value = "今天天气不错！"

        config = _make_config(routing_strategy="balanced")

        r1 = await run_pipeline(
            mock_db, fake_redis, "红烧肉怎么做", device_id="dev-x06", config=config,
        )
        r2 = await run_pipeline(
            mock_db, fake_redis, "今天天气怎么样", device_id="dev-x06", config=config,
        )

        assert r1.domain == "knowledge"
        assert r2.domain == "chitchat"


# ---------------------------------------------------------------------------
# 场景 4：闲聊域 → 知识域切换
# ---------------------------------------------------------------------------

class TestChitchatToKnowledge:
    """闲聊域到知识域的切换。"""

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    @patch("app.services.nlu.pipeline.generate_knowledge_answer")
    async def test_chitchat_then_knowledge_query(
        self, mock_gen, mock_chat, mock_db, fake_redis
    ):
        """先闲聊，再问知识类问题 → 应切换到知识域。"""
        mock_chat.return_value = "你好呀！"
        mock_gen.return_value = ("鸡蛋约 70 大卡热量。", [{"score": 0.85}])

        config = _make_config(routing_strategy="balanced")

        r1 = await run_pipeline(
            mock_db, fake_redis, "你好", device_id="dev-x07", config=config,
        )
        r2 = await run_pipeline(
            mock_db, fake_redis, "鸡蛋的热量是多少", device_id="dev-x07", config=config,
        )

        assert r1.domain == "chitchat"
        assert r2.domain == "knowledge"
        assert r1.session_id == r2.session_id


# ---------------------------------------------------------------------------
# 场景 5：连续跨域切换（指令→闲聊→指令）
# ---------------------------------------------------------------------------

class TestSequentialCrossDomain:
    """连续跨域切换。"""

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_command_chitchat_command_sequence(self, mock_chat, mock_db, fake_redis):
        """指令→闲聊→指令 连续切换，每轮路由正确。"""
        mock_chat.return_value = "不客气！有需要再说。"
        config = _make_config(routing_strategy="balanced")

        r1 = await run_pipeline(
            mock_db, fake_redis, "开始烹饪", device_id="dev-x08", config=config,
        )
        r2 = await run_pipeline(
            mock_db, fake_redis, "谢谢", device_id="dev-x08", config=config,
        )
        r3 = await run_pipeline(
            mock_db, fake_redis, "暂停烹饪", device_id="dev-x08", config=config,
        )

        assert r1.domain == "command"
        assert r1.intent == "voice_cmd_start_cooking"
        assert r2.domain == "chitchat"
        assert r3.domain == "command"
        assert r3.intent == "voice_cmd_pause_cooking"
        assert r1.session_id == r2.session_id == r3.session_id


# ---------------------------------------------------------------------------
# 场景 6：域切换时上下文正确保持/清除
# ---------------------------------------------------------------------------

class TestContextOnDomainSwitch:
    """域切换时会话上下文的保持与清除。"""

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_dialog_history_preserved_across_domains(
        self, mock_chat, mock_db, fake_redis
    ):
        """跨域切换时 dialog_history 应正确累积。"""
        mock_chat.return_value = "你好！"  # 闲聊回复
        config = _make_config(routing_strategy="balanced")

        await run_pipeline(
            mock_db, fake_redis, "你好", device_id="dev-x09", config=config,
        )
        await run_pipeline(
            mock_db, fake_redis, "暂停烹饪", device_id="dev-x09", config=config,
        )
        await run_pipeline(
            mock_db, fake_redis, "谢谢", device_id="dev-x09", config=config,
        )

        raw = await fake_redis.get("session:dev-x09")
        assert raw is not None
        session = json.loads(raw)
        hist = session["dialog_history"]
        assert len(hist) == 3
        assert hist[0]["route"] == "chitchat"
        assert hist[1]["route"] == "command"
        assert hist[1]["intent"] == "voice_cmd_pause_cooking"
        assert hist[2]["route"] == "chitchat"

    @pytest.mark.asyncio
    async def test_command_complete_clears_slot_state(self, mock_db, fake_redis):
        """指令完成后 active_intent、filled_slots 应清除。"""
        config = _make_config()

        # 完整执行一个带槽位的指令
        r1 = await run_pipeline(
            mock_db, fake_redis, "设置温度180度", device_id="dev-x10", config=config,
        )
        assert r1.domain == "command"
        assert r1.intent == "set_cooking_temp"

        raw = await fake_redis.get("session:dev-x10")
        session = json.loads(raw)
        assert session.get("state") == "IDLE"
        assert session.get("active_intent") is None
        assert session.get("pending_slots") is None
        # 指令完成后 filled_slots 应被清空，为下一轮做准备
        assert session.get("filled_slots") == {}

    @pytest.mark.asyncio
    @patch("app.services.nlu.pipeline.chat_completion", new_callable=AsyncMock)
    async def test_chitchat_after_command_gets_history_context(
        self, mock_chat, mock_db, fake_redis
    ):
        """指令完成后切换到闲聊，闲聊 LLM 应收到历史上下文。"""
        mock_chat.return_value = "好的，不客气！"
        config = _make_config(routing_strategy="balanced")

        await run_pipeline(
            mock_db, fake_redis, "开始烹饪", device_id="dev-x11", config=config,
        )
        await run_pipeline(
            mock_db, fake_redis, "谢谢", device_id="dev-x11", config=config,
        )

        # 验证 chat_completion 收到的 messages 包含历史
        call_args = mock_chat.call_args
        messages = call_args[0][0]
        assert len(messages) >= 3  # system + user(开始烹饪) + asst + user(谢谢)
        user_contents = [m["content"] for m in messages if m["role"] == "user"]
        assert "开始烹饪" in user_contents
        assert "谢谢" in user_contents
