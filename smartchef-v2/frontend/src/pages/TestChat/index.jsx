import { useEffect, useState, useCallback, useRef, memo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Button,
  Input,
  InputNumber,
  List,
  Select,
  Switch,
  Space,
  Tooltip,
  Empty,
  Spin,
  Modal,
  Drawer,
  Form,
  Collapse,
  Tag,
  Divider,
  message,
} from 'antd';
import {
  PlusOutlined,
  SendOutlined,
  DeleteOutlined,
  EditOutlined,
  MessageOutlined,
  BugOutlined,
  ClockCircleOutlined,
  AimOutlined,
  RobotOutlined,
  UserOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import useProfileStore from '../../stores/profileStore';
import { profileApi } from '../../services/profileApi';

const { Text, Title } = Typography;

const SIDEBAR_WIDTH = 280;
const DEBUG_PANEL_WIDTH = 300;

const COOKING_STATUS_OPTIONS = [
  { value: 'idle', label: '空闲 (idle)' },
  { value: 'cooking', label: '烹饪中 (cooking)' },
  { value: 'warming', label: '保温中 (warming)' },
];

const CURRENT_PAGE_OPTIONS = [
  { value: 'home', label: '主页 (home)' },
  { value: 'recipe_browser', label: '菜谱浏览 (recipe_browser)' },
  { value: 'cooking_progress', label: '烹饪进度 (cooking_progress)' },
  { value: 'settings', label: '设置 (settings)' },
];

const COOKING_STATUS_LABELS = {
  idle: '空闲',
  cooking: '正在烹饪',
  warming: '保温中',
};

const PAGE_LABELS = {
  home: '主页',
  recipe_browser: '菜谱浏览',
  cooking_progress: '烹饪进度',
  settings: '设置',
};

const DEVICE_CONTEXT_DEFAULT = {
  cooking_status: 'idle',
  door_closed: true,
  current_temp: 25,
  current_page: 'home',
  screen_info: '',
};

const CONTEXT_PRESETS = [
  {
    key: 'idle_home',
    label: '空闲 - 主页',
    values: {
      cooking_status: 'idle',
      door_closed: true,
      current_temp: 25,
      current_page: 'home',
      screen_info: '',
    },
  },
  {
    key: 'cooking',
    label: '正在烹饪',
    values: {
      cooking_status: 'cooking',
      door_closed: true,
      current_temp: 180,
      current_page: 'cooking_progress',
      screen_info: '',
    },
  },
  {
    key: 'recipe',
    label: '菜谱浏览',
    values: {
      cooking_status: 'idle',
      door_closed: true,
      current_temp: 25,
      current_page: 'recipe_browser',
      screen_info: '',
    },
  },
];

function deviceContextMeaningful(ctx) {
  const screen = (ctx.screen_info || '').trim();
  return (
    ctx.cooking_status !== DEVICE_CONTEXT_DEFAULT.cooking_status ||
    ctx.door_closed !== DEVICE_CONTEXT_DEFAULT.door_closed ||
    ctx.current_temp !== DEVICE_CONTEXT_DEFAULT.current_temp ||
    (ctx.current_page && ctx.current_page !== DEVICE_CONTEXT_DEFAULT.current_page) ||
    !!screen
  );
}

function buildDeviceContextPayload(ctx) {
  const payload = {
    cooking_status: ctx.cooking_status,
    door_closed: ctx.door_closed,
    current_temp: ctx.current_temp,
    current_page: ctx.current_page || 'home',
  };
  const si = (ctx.screen_info || '').trim();
  if (si) payload.screen_info = si;
  return payload;
}

const ChatBubble = memo(function ChatBubble({ msg }) {
  const isUser = msg.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: 10,
        padding: '8px 0',
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          background: isUser
            ? 'linear-gradient(135deg, #1677ff, #4096ff)'
            : 'linear-gradient(135deg, #52c41a, #95de64)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 16,
          flexShrink: 0,
        }}
      >
        {isUser ? <UserOutlined /> : <RobotOutlined />}
      </div>
      <div
        style={{
          maxWidth: '70%',
          padding: '10px 16px',
          borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
          background: isUser ? 'var(--color-primary)' : 'var(--color-bg-elevated)',
          color: isUser ? '#fff' : 'var(--color-text)',
          boxShadow: 'var(--shadow-sm)',
          lineHeight: 1.6,
          fontSize: 'var(--font-size-sm)',
          wordBreak: 'break-word',
          border: isUser ? 'none' : '1px solid var(--color-border-light)',
        }}
      >
        {msg.content}
      </div>
    </div>
  );
});

const DebugPanel = memo(function DebugPanel({ debugInfo }) {
  if (!debugInfo || Object.keys(debugInfo).length === 0) return null;

  const refRes =
    debugInfo.reference_resolution ||
    debugInfo.referenceResolution ||
    debugInfo.resolution;
  const knowledgeHit = debugInfo.knowledge_hit || debugInfo.knowledgeHit;
  const personaApplied =
    debugInfo.persona_applied ||
    debugInfo.personaApplied ||
    (debugInfo.persona && { name: debugInfo.persona.name, traits: debugInfo.persona.traits });
  const dialogState = debugInfo.dialog_state || debugInfo.dialogState;

  return (
    <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
      <Space>
        <AimOutlined style={{ color: 'var(--color-primary)' }} />
        <Text strong style={{ fontSize: 'var(--font-size-sm)' }}>领域分类</Text>
        <Tag
          color={
            debugInfo.domain === 'command'
              ? 'blue'
              : debugInfo.domain === 'knowledge'
                ? 'green'
                : 'default'
          }
        >
          {debugInfo.domain || '-'}
        </Tag>
      </Space>

      {debugInfo.intent && (
        <Space>
          <BugOutlined style={{ color: 'var(--color-warning)' }} />
          <Text style={{ fontSize: 'var(--font-size-sm)' }}>意图:</Text>
          <Text code style={{ fontSize: 'var(--font-size-xs)' }}>{debugInfo.intent}</Text>
        </Space>
      )}

      {debugInfo.confidence != null && (
        <Space>
          <Text style={{ fontSize: 'var(--font-size-sm)' }}>置信度:</Text>
          <Text
            style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-sm)' }}
          >
            {(debugInfo.confidence * 100).toFixed(1)}%
          </Text>
        </Space>
      )}

      {debugInfo.latency_ms != null && (
        <Space>
          <ClockCircleOutlined style={{ color: 'var(--color-text-tertiary)' }} />
          <Text style={{ fontSize: 'var(--font-size-sm)' }}>延迟:</Text>
          <Text
            style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-sm)' }}
          >
            {debugInfo.latency_ms}ms
          </Text>
        </Space>
      )}

      {debugInfo.candidates?.length > 0 && (
        <Collapse
          ghost
          size="small"
          items={[
            {
              key: 'candidates',
              label: (
                <Text style={{ fontSize: 'var(--font-size-xs)' }}>
                  候选意图 ({debugInfo.candidates.length})
                </Text>
              ),
              children: debugInfo.candidates.map((c, i) => (
                <div key={i} style={{ fontSize: 'var(--font-size-xs)', padding: '2px 0' }}>
                  <Text code>{c.intent}</Text>{' '}
                  <Text type="secondary">{(c.confidence * 100).toFixed(1)}%</Text>
                </div>
              )),
            },
          ]}
        />
      )}

      {refRes && (
        <>
          <Divider style={{ margin: '8px 0' }} />
          <Text strong style={{ fontSize: 'var(--font-size-sm)' }}>指代消解</Text>
          <div style={{ fontSize: 'var(--font-size-xs)', fontFamily: 'var(--font-mono)' }}>
            {typeof refRes === 'object' && refRes.pronoun != null && refRes.entity != null && (
              <Text>
                <Text code>{String(refRes.pronoun)}</Text>
                {' → '}
                <Text code>{String(refRes.entity)}</Text>
              </Text>
            )}
            {typeof refRes === 'object' && refRes.from != null && refRes.to != null && !(refRes.pronoun != null) && (
              <Text>
                <Text code>{String(refRes.from)}</Text>
                {' → '}
                <Text code>{String(refRes.to)}</Text>
              </Text>
            )}
            {!(
              typeof refRes === 'object' &&
              ((refRes.pronoun != null && refRes.entity != null) || (refRes.from != null && refRes.to != null))
            ) && (
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 'var(--font-size-xs)' }}>
                {JSON.stringify(refRes, null, 2)}
              </pre>
            )}
          </div>
        </>
      )}

      {knowledgeHit && (
        <>
          <Divider style={{ margin: '8px 0' }} />
          <Text strong style={{ fontSize: 'var(--font-size-sm)' }}>知识命中</Text>
          <div style={{ fontSize: 'var(--font-size-xs)' }}>
            <Text>文档: <Text code>{knowledgeHit.doc_name || knowledgeHit.docName || knowledgeHit.title || '—'}</Text></Text>
            <br />
            <Text type="secondary">
              分类: {knowledgeHit.category ?? '—'}
              {knowledgeHit.score != null && (
                <>
                  {' · 相关度 '}
                  {typeof knowledgeHit.score === 'number' &&
                  knowledgeHit.score >= 0 &&
                  knowledgeHit.score <= 1
                    ? `${(knowledgeHit.score * 100).toFixed(1)}%`
                    : String(knowledgeHit.score)}
                </>
              )}
            </Text>
          </div>
        </>
      )}

      {personaApplied && (
        <>
          <Divider style={{ margin: '8px 0' }} />
          <Text strong style={{ fontSize: 'var(--font-size-sm)' }}>人设应用</Text>
          <div style={{ fontSize: 'var(--font-size-xs)' }}>
            <Text>
              {personaApplied.name || personaApplied.persona_name || '—'}
            </Text>
            {Array.isArray(personaApplied.traits) && personaApplied.traits.length > 0 && (
              <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {personaApplied.traits.map((t) => (
                  <Tag key={t}>{t}</Tag>
                ))}
              </div>
            )}
            {typeof personaApplied === 'object' &&
              !personaApplied.name &&
              !personaApplied.persona_name &&
              !Array.isArray(personaApplied.traits) && (
                <pre style={{ margin: '6px 0 0', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)' }}>
                  {JSON.stringify(personaApplied, null, 2)}
                </pre>
              )}
          </div>
        </>
      )}

      {dialogState && (
        <>
          <Divider style={{ margin: '8px 0' }} />
          <Text strong style={{ fontSize: 'var(--font-size-sm)' }}>对话状态</Text>
          <div style={{ fontSize: 'var(--font-size-xs)', fontFamily: 'var(--font-mono)' }}>
            {dialogState.previous_domain != null && dialogState.current_domain != null && (
              <Text>
                {String(dialogState.previous_domain)}
                {' → '}
                {String(dialogState.current_domain)}
              </Text>
            )}
            {!(dialogState.previous_domain != null && dialogState.current_domain != null) && (
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(dialogState, null, 2)}
              </pre>
            )}
          </div>
        </>
      )}
    </div>
  );
});

const TypingIndicator = memo(function TypingIndicator() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        gap: 10,
        padding: '8px 0',
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #52c41a, #95de64)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 16,
          flexShrink: 0,
        }}
      >
        <RobotOutlined />
      </div>
      <div
        style={{
          padding: '10px 16px',
          borderRadius: '16px 16px 16px 4px',
          background: 'var(--color-bg-elevated)',
          border: '1px solid var(--color-border-light)',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <span className="typing-dots" aria-hidden>
          <span />
          <span />
          <span />
        </span>
      </div>
    </div>
  );
});

export default function TestChat() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const profileId = searchParams.get('profileId');

  const {
    testSessions,
    currentSessionId,
    messages,
    chatLoading,
    fetchTestSessions,
    createTestSession,
    deleteTestSession,
    renameTestSession,
    setCurrentSession,
    fetchMessages,
    sendMessage,
  } = useProfileStore();

  const [profiles, setProfiles] = useState([]);
  const [selectedProfileId, setSelectedProfileId] = useState(profileId || null);
  const [inputValue, setInputValue] = useState('');
  const [selectedMsgDebug, setSelectedMsgDebug] = useState(null);
  const messagesEndRef = useRef(null);
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState('');

  const [deviceDrawerOpen, setDeviceDrawerOpen] = useState(false);
  const [deviceContext, setDeviceContext] = useState({ ...DEVICE_CONTEXT_DEFAULT });
  const [awaitingAssistant, setAwaitingAssistant] = useState(false);

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm] = Form.useForm();
  const [createLoading, setCreateLoading] = useState(false);

  useEffect(() => {
    profileApi.listProfiles({ page: 1, page_size: 100 }).then((res) => {
      const items = res.data?.items || res.data || [];
      setProfiles(items);
      if (!selectedProfileId && items.length > 0) {
        setSelectedProfileId(items[0].id);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedProfileId) {
      fetchTestSessions(selectedProfileId);
    }
  }, [selectedProfileId, fetchTestSessions]);

  useEffect(() => {
    if (currentSessionId) {
      fetchMessages(currentSessionId);
    }
  }, [currentSessionId, fetchMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, awaitingAssistant]);

  const openCreateModal = useCallback(() => {
    createForm.resetFields();
    createForm.setFieldsValue({
      name: '新会话',
      profile_id: selectedProfileId,
      remark: '',
    });
    setCreateModalOpen(true);
  }, [createForm, selectedProfileId]);

  const handleCreateSession = useCallback(async () => {
    try {
      const values = await createForm.validateFields();
      setCreateLoading(true);
      const pid = values.profile_id;
      if (pid !== selectedProfileId) {
        setSelectedProfileId(pid);
      }
      const session = await createTestSession(pid, values.name);
      setCurrentSession(session.id);
      setCreateModalOpen(false);
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '创建失败');
    } finally {
      setCreateLoading(false);
    }
  }, [createForm, selectedProfileId, createTestSession, setCurrentSession]);

  const handleDeleteSession = useCallback(
    async (sid) => {
      try {
        await deleteTestSession(sid, selectedProfileId);
        message.success('已删除');
      } catch (err) {
        message.error(err?.message || '删除失败');
      }
    },
    [selectedProfileId, deleteTestSession],
  );

  const handleRename = useCallback(
    async () => {
      if (!renameTarget || !renameValue.trim()) return;
      try {
        await renameTestSession(renameTarget, renameValue.trim());
        setRenameTarget(null);
      } catch (err) {
        message.error(err?.message || '重命名失败');
      }
    },
    [renameTarget, renameValue, renameTestSession],
  );

  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || !currentSessionId) return;
    const text = inputValue.trim();
    setInputValue('');
    setAwaitingAssistant(true);
    try {
      const extra = {};
      if (deviceContextMeaningful(deviceContext)) {
        extra.device_context = buildDeviceContextPayload(deviceContext);
      }
      const result = await sendMessage(currentSessionId, text, extra);
      if (result?.assistant_message?.debug_info) {
        setSelectedMsgDebug(result.assistant_message.debug_info);
      }
    } catch (err) {
      message.error(err?.message || '发送失败');
    } finally {
      setAwaitingAssistant(false);
    }
  }, [inputValue, currentSessionId, sendMessage, deviceContext]);

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div
      style={{
        display: 'flex',
        height: 'calc(100vh - 56px - 48px)',
        margin: '-24px',
        background: 'var(--color-bg)',
      }}
    >
      {/* Left sidebar: sessions */}
      <div
        style={{
          width: SIDEBAR_WIDTH,
          borderRight: '1px solid var(--color-border-light)',
          background: 'var(--color-bg-elevated)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}
      >
        {/* Profile selector */}
        <div style={{ padding: '16px 16px 8px' }}>
          <Select
            placeholder="选择对话方案"
            value={selectedProfileId}
            onChange={(val) => {
              setSelectedProfileId(val);
              setCurrentSession(null);
            }}
            style={{ width: '100%' }}
            showSearch
            optionFilterProp="label"
            options={profiles.map((p) => ({ value: p.id, label: p.name }))}
          />
        </div>

        {/* New session button */}
        <div style={{ padding: '8px 16px' }}>
          <Button
            type="dashed"
            icon={<PlusOutlined />}
            block
            onClick={openCreateModal}
            disabled={!selectedProfileId}
          >
            新建会话
          </Button>
        </div>

        {/* Session list */}
        <div style={{ flex: 1, overflow: 'auto', padding: '0 8px' }}>
          {testSessions.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无会话"
              style={{ paddingTop: 40 }}
            />
          ) : (
            <List
              dataSource={testSessions}
              split={false}
              renderItem={(session) => (
                <div
                  key={session.id}
                  onClick={() => {
                    setCurrentSession(session.id);
                    setSelectedMsgDebug(null);
                  }}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    background:
                      currentSessionId === session.id
                        ? 'var(--color-primary-bg)'
                        : 'transparent',
                    border:
                      currentSessionId === session.id
                        ? '1px solid var(--color-primary-border)'
                        : '1px solid transparent',
                    marginBottom: 4,
                    transition: 'all var(--duration-fast) var(--easing)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 8,
                  }}
                  onMouseEnter={(e) => {
                    if (currentSessionId !== session.id) {
                      e.currentTarget.style.background = 'var(--color-fill)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (currentSessionId !== session.id) {
                      e.currentTarget.style.background = 'transparent';
                    }
                  }}
                >
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <Text
                      ellipsis
                      style={{
                        display: 'block',
                        fontWeight: currentSessionId === session.id ? 600 : 400,
                        fontSize: 'var(--font-size-sm)',
                      }}
                    >
                      <MessageOutlined style={{ marginRight: 6, opacity: 0.5 }} />
                      {session.name}
                    </Text>
                    <Text
                      type="secondary"
                      style={{ fontSize: 'var(--font-size-xs)' }}
                    >
                      {session.message_count} 条消息
                    </Text>
                  </div>
                  <Space size={0}>
                    <Tooltip title="重命名">
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={(e) => {
                          e.stopPropagation();
                          setRenameTarget(session.id);
                          setRenameValue(session.name);
                        }}
                        style={{ opacity: 0.5 }}
                      />
                    </Tooltip>
                    <Tooltip title="删除">
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSession(session.id);
                        }}
                        style={{ opacity: 0.5 }}
                      />
                    </Tooltip>
                  </Space>
                </div>
              )}
            />
          )}
        </div>
      </div>

      {/* Center: chat messages */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
        }}
      >
        {!currentSessionId ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="选择或创建一个会话开始对话"
            />
          </div>
        ) : (
          <>
            {/* Chat header with device context button */}
            <div
              style={{
                padding: '10px 24px',
                borderBottom: '1px solid var(--color-border-light)',
                background: 'var(--color-bg-elevated)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <Text strong style={{ fontSize: 'var(--font-size-sm)' }}>
                {testSessions.find((s) => s.id === currentSessionId)?.name || '对话'}
              </Text>
              <Button
                size="small"
                icon={<SettingOutlined />}
                onClick={() => setDeviceDrawerOpen(true)}
              >
                设备上下文
              </Button>
            </div>

            {/* Messages area */}
            <div
              style={{
                flex: 1,
                overflow: 'auto',
                padding: '20px 24px',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              {deviceContextMeaningful(deviceContext) && (
                <div
                  style={{
                    flexShrink: 0,
                    marginBottom: 16,
                    background: '#fffbe6',
                    border: '1px solid #ffe58f',
                    borderRadius: 8,
                    padding: '8px 16px',
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  🍳 {COOKING_STATUS_LABELS[deviceContext.cooking_status] || deviceContext.cooking_status}
                  {' '}| 门: {deviceContext.door_closed ? '已关闭' : '已开启'}
                  {' '}| 温度: {deviceContext.current_temp}°C
                  {' '}| 页面: {PAGE_LABELS[deviceContext.current_page] || deviceContext.current_page || '—'}
                  {(deviceContext.screen_info || '').trim()
                    ? ` · 屏幕: ${(deviceContext.screen_info || '').trim()}`
                    : ''}
                </div>
              )}
              {chatLoading && messages.length === 0 ? (
                <div style={{ textAlign: 'center', paddingTop: 60 }}>
                  <Spin size="large" />
                </div>
              ) : messages.length === 0 && !awaitingAssistant ? (
                <div
                  style={{
                    textAlign: 'center',
                    paddingTop: 60,
                    color: 'var(--color-text-tertiary)',
                  }}
                >
                  <RobotOutlined style={{ fontSize: 48, opacity: 0.3 }} />
                  <div style={{ marginTop: 12 }}>发送一条消息开始对话</div>
                </div>
              ) : (
                <>
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      onClick={() => {
                        if (msg.role === 'assistant' && msg.debug_info) {
                          setSelectedMsgDebug(msg.debug_info);
                        }
                      }}
                      style={{
                        cursor: msg.role === 'assistant' ? 'pointer' : 'default',
                      }}
                    >
                      <ChatBubble msg={msg} />
                    </div>
                  ))}
                  {awaitingAssistant && <TypingIndicator />}
                </>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input bar */}
            <div
              style={{
                padding: '12px 24px 16px',
                borderTop: '1px solid var(--color-border-light)',
                background: 'var(--color-bg-elevated)',
              }}
            >
              <div style={{ display: 'flex', gap: 12 }}>
                <Input.TextArea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入消息，按 Enter 发送..."
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  style={{ flex: 1, borderRadius: 'var(--radius-lg)' }}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleSend}
                  loading={chatLoading || awaitingAssistant}
                  disabled={!inputValue.trim() || awaitingAssistant}
                  style={{ height: 'auto', minHeight: 36, borderRadius: 'var(--radius-lg)' }}
                >
                  发送
                </Button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Right panel: debug info */}
      <div
        style={{
          width: DEBUG_PANEL_WIDTH,
          borderLeft: '1px solid var(--color-border-light)',
          background: 'var(--color-bg-elevated)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: '16px',
            borderBottom: '1px solid var(--color-border-light)',
          }}
        >
          <Space>
            <BugOutlined />
            <Text strong>调试信息</Text>
          </Space>
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          {selectedMsgDebug ? (
            <DebugPanel debugInfo={selectedMsgDebug} />
          ) : (
            <div
              style={{
                padding: 24,
                textAlign: 'center',
                color: 'var(--color-text-tertiary)',
              }}
            >
              <BugOutlined style={{ fontSize: 32, opacity: 0.3 }} />
              <div style={{ marginTop: 8, fontSize: 'var(--font-size-sm)' }}>
                点击助手消息查看调试信息
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Rename modal */}
      <Modal
        open={!!renameTarget}
        title="重命名会话"
        onCancel={() => setRenameTarget(null)}
        onOk={handleRename}
        okText="确定"
        cancelText="取消"
        width={360}
        centered
        destroyOnHidden
      >
        <Input
          value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)}
          placeholder="输入新名称"
          maxLength={128}
          style={{ marginTop: 12 }}
          onPressEnter={handleRename}
        />
      </Modal>

      {/* New session modal */}
      <Modal
        open={createModalOpen}
        title="新建会话"
        onCancel={() => setCreateModalOpen(false)}
        onOk={handleCreateSession}
        confirmLoading={createLoading}
        okText="创建"
        cancelText="取消"
        width={480}
        centered
        destroyOnHidden
      >
        <Form form={createForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="会话名称"
            rules={[{ required: true, message: '请输入会话名称' }]}
          >
            <Input placeholder="新会话" maxLength={128} />
          </Form.Item>
          <Form.Item
            name="profile_id"
            label="关联方案"
            rules={[{ required: true, message: '请选择关联方案' }]}
          >
            <Select
              placeholder="选择对话方案"
              showSearch
              optionFilterProp="label"
              options={profiles.map((p) => ({ value: p.id, label: p.name }))}
            />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="可选备注..." maxLength={500} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Device context drawer */}
      <Drawer
        title="设备上下文"
        open={deviceDrawerOpen}
        onClose={() => setDeviceDrawerOpen(false)}
        width={360}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginBottom: 8 }}>
              快速预设
            </Text>
            <Space wrap style={{ width: '100%' }}>
              {CONTEXT_PRESETS.map((p) => (
                <Button key={p.key} size="small" onClick={() => setDeviceContext({ ...DEVICE_CONTEXT_DEFAULT, ...p.values })}>
                  {p.label}
                </Button>
              ))}
            </Space>
          </div>
          <div>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginBottom: 8 }}>
              烹饪状态 (cooking_status)
            </Text>
            <Select
              value={deviceContext.cooking_status}
              onChange={(val) => setDeviceContext((prev) => ({ ...prev, cooking_status: val }))}
              options={COOKING_STATUS_OPTIONS}
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginBottom: 8 }}>
              门关闭状态 (door_closed)
            </Text>
            <Switch
              checked={deviceContext.door_closed}
              onChange={(val) => setDeviceContext((prev) => ({ ...prev, door_closed: val }))}
              checkedChildren="关闭"
              unCheckedChildren="开启"
            />
          </div>
          <div>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginBottom: 8 }}>
              当前温度 (current_temp) °C
            </Text>
            <InputNumber
              value={deviceContext.current_temp}
              onChange={(val) => setDeviceContext((prev) => ({ ...prev, current_temp: val ?? prev.current_temp }))}
              min={-40}
              max={300}
              style={{ width: '100%' }}
              addonAfter="°C"
            />
          </div>
          <div>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginBottom: 8 }}>
              当前页面 (current_page)
            </Text>
            <Select
              value={deviceContext.current_page || 'home'}
              onChange={(val) => setDeviceContext((prev) => ({ ...prev, current_page: val }))}
              options={CURRENT_PAGE_OPTIONS}
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginBottom: 8 }}>
              屏幕信息 (screen_info)
            </Text>
            <Input
              value={deviceContext.screen_info ?? ''}
              onChange={(e) => setDeviceContext((prev) => ({ ...prev, screen_info: e.target.value }))}
              placeholder="可选：副标题、弹窗等元数据"
              maxLength={500}
            />
          </div>
          <Divider style={{ margin: '4px 0' }} />
          <div>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
              当前配置将在发送消息时附带到请求中。
            </Text>
          </div>
          <div
            style={{
              background: 'var(--color-fill)',
              borderRadius: 'var(--radius-md)',
              padding: 12,
              fontSize: 'var(--font-size-xs)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(deviceContext, null, 2)}
            </pre>
          </div>
        </div>
      </Drawer>
    </div>
  );
}
