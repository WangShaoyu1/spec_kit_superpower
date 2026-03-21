import { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Breadcrumb,
  Card,
  Descriptions,
  Tag,
  Button,
  Table,
  Space,
  Select,
  Modal,
  Skeleton,
  Empty,
  Timeline,
  message,
  Row,
  Col,
  Badge,
  Checkbox,
  Form,
  Input,
} from 'antd';
import {
  ArrowLeftOutlined,
  PlusOutlined,
  CheckCircleOutlined,
  CloudUploadOutlined,
  InboxOutlined,
  DeleteOutlined,
  EditOutlined,
  LinkOutlined,
  ClockCircleOutlined,
  SwapOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useProfileStore from '../../stores/profileStore';
import { intentLibraryApi } from '../../services/intentLibraryApi';
import PersonaEditor from './PersonaEditor';
import DangerConfirmModal from '../../components/DangerConfirmModal';

const { Title, Text, Paragraph } = Typography;

const ROUTE_LABELS = {
  intent_first: '指令优先',
  knowledge_first: '知识优先',
  auto: '自动',
};

const LLM_PROVIDER_OPTIONS = [
  { value: 'GPT-4o', label: 'GPT-4o' },
  { value: 'GPT-4o-mini', label: 'GPT-4o-mini' },
  { value: 'Qwen-Max', label: 'Qwen-Max' },
  { value: 'Qwen-Plus', label: 'Qwen-Plus' },
  { value: 'GLM-4', label: 'GLM-4' },
  { value: 'GLM-4-Flash', label: 'GLM-4-Flash' },
];

const cardSurface = {
  borderRadius: 12,
  boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
};

function personaTraitTags(persona) {
  const raw = persona.personality_traits;
  if (Array.isArray(raw) && raw.length) return raw.filter(Boolean);
  const p = persona.personality;
  if (!p || typeof p !== 'string') return [];
  return p.split(/[,，;；、\s]+/).map((s) => s.trim()).filter(Boolean).slice(0, 8);
}

function greetingPreview(persona) {
  if (persona.greeting && String(persona.greeting).trim()) {
    const g = String(persona.greeting).trim();
    return g.length > 80 ? `${g.slice(0, 80)}…` : g;
  }
  const sp = persona.system_prompt;
  if (!sp) return '—';
  const t = String(sp).trim();
  return t.length > 80 ? `${t.slice(0, 80)}…` : t;
}

export default function DialogProfileDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const {
    currentProfile: profile,
    detailLoading,
    personas,
    bindings,
    versions,
    fetchDetail,
    createPersona,
    updatePersona,
    deletePersona,
    activatePersona,
    syncBindings,
    publish,
    archiveVersion,
    clearDetail,
    updateProfile,
  } = useProfileStore();

  const [profileSettingsOpen, setProfileSettingsOpen] = useState(false);
  const [profileSettingsLoading, setProfileSettingsLoading] = useState(false);
  const [profileForm] = Form.useForm();

  const [personaModalOpen, setPersonaModalOpen] = useState(false);
  const [editingPersona, setEditingPersona] = useState(null);
  const [personaLoading, setPersonaLoading] = useState(false);
  const [deletePersonaTarget, setDeletePersonaTarget] = useState(null);
  const [deletePersonaLoading, setDeletePersonaLoading] = useState(false);

  const [bindModalOpen, setBindModalOpen] = useState(false);
  const [availableLibraries, setAvailableLibraries] = useState([]);
  const [selectedLibId, setSelectedLibId] = useState(null);
  const [bindLoading, setBindLoading] = useState(false);

  const [publishLoading, setPublishLoading] = useState(false);
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [publishCountdown, setPublishCountdown] = useState(5);
  const [publishConfirmChecked, setPublishConfirmChecked] = useState(false);
  const [personaSwitchOpen, setPersonaSwitchOpen] = useState(false);

  useEffect(() => {
    fetchDetail(id);
    return () => clearDetail();
  }, [id, fetchDetail, clearDetail]);

  useEffect(() => {
    if (!publishModalOpen) {
      setPublishConfirmChecked(false);
      setPublishCountdown(5);
    }
  }, [publishModalOpen]);

  useEffect(() => {
    if (!publishConfirmChecked) {
      setPublishCountdown(5);
    }
  }, [publishConfirmChecked]);

  useEffect(() => {
    if (!publishModalOpen || !publishConfirmChecked) return undefined;
    setPublishCountdown(5);
    const timer = setInterval(() => {
      setPublishCountdown((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [publishModalOpen, publishConfirmChecked]);

  // Persona handlers
  const openCreatePersona = useCallback(() => {
    setEditingPersona(null);
    setPersonaModalOpen(true);
  }, []);

  const openEditPersona = useCallback((p) => {
    setEditingPersona(p);
    setPersonaModalOpen(true);
  }, []);

  const handleSavePersona = useCallback(
    async (values) => {
      setPersonaLoading(true);
      try {
        if (editingPersona) {
          await updatePersona(id, editingPersona.id, values);
          message.success('更新成功');
        } else {
          await createPersona(id, values);
          message.success('创建成功');
        }
        setPersonaModalOpen(false);
      } catch (err) {
        message.error(err?.message || '操作失败');
      } finally {
        setPersonaLoading(false);
      }
    },
    [id, editingPersona, createPersona, updatePersona],
  );

  const handleDeletePersona = useCallback(async () => {
    if (!deletePersonaTarget) return;
    setDeletePersonaLoading(true);
    try {
      await deletePersona(id, deletePersonaTarget.id);
      message.success('删除成功');
      setDeletePersonaTarget(null);
    } catch (err) {
      message.error(err?.message || '删除失败');
    } finally {
      setDeletePersonaLoading(false);
    }
  }, [id, deletePersonaTarget, deletePersona]);

  const handleActivatePersona = useCallback(
    async (personaId) => {
      try {
        await activatePersona(id, personaId);
        message.success('已激活');
        setPersonaSwitchOpen(false);
      } catch (err) {
        message.error(err?.message || '操作失败');
      }
    },
    [id, activatePersona],
  );

  // Binding handlers
  const openBindModal = useCallback(async () => {
    try {
      const res = await intentLibraryApi.listLibraries({ page: 1, page_size: 100 });
      const libs = res.data?.items || res.data || [];
      setAvailableLibraries(libs);
    } catch {
      setAvailableLibraries([]);
    }
    setSelectedLibId(null);
    setBindModalOpen(true);
  }, []);

  const handleAddBinding = useCallback(async () => {
    if (!selectedLibId) return;
    setBindLoading(true);
    try {
      const newBindings = [
        ...bindings.map((b) => ({
          library_id: b.library_id,
          priority: b.priority,
          confidence_threshold: b.confidence_threshold,
        })),
        { library_id: selectedLibId, priority: bindings.length, confidence_threshold: 0.7 },
      ];
      await syncBindings(id, newBindings);
      message.success('绑定成功');
      setBindModalOpen(false);
    } catch (err) {
      message.error(err?.message || '绑定失败');
    } finally {
      setBindLoading(false);
    }
  }, [id, selectedLibId, bindings, syncBindings]);

  const handleRemoveBinding = useCallback(
    async (libraryId) => {
      try {
        const newBindings = bindings
          .filter((b) => b.library_id !== libraryId)
          .map((b, i) => ({
            library_id: b.library_id,
            priority: i,
            confidence_threshold: b.confidence_threshold,
          }));
        await syncBindings(id, newBindings);
        message.success('已解绑');
      } catch (err) {
        message.error(err?.message || '操作失败');
      }
    },
    [id, bindings, syncBindings],
  );

  const handlePublish = useCallback(() => {
    setPublishModalOpen(true);
  }, []);

  const confirmPublish = useCallback(async () => {
    if (!publishConfirmChecked || publishCountdown > 0) return;
    setPublishLoading(true);
    try {
      await publish(id);
      message.success('发布成功');
      setPublishModalOpen(false);
      setPublishConfirmChecked(false);
    } catch (err) {
      message.error(err?.message || '发布失败');
    } finally {
      setPublishLoading(false);
    }
  }, [id, publish, publishConfirmChecked, publishCountdown]);

  const openProfileSettings = useCallback(() => {
    if (!profile) return;
    profileForm.setFieldsValue({
      llm_provider: profile.llm_provider || undefined,
      llm_model: profile.llm_model || '',
    });
    setProfileSettingsOpen(true);
  }, [profile, profileForm]);

  const saveProfileSettings = useCallback(async () => {
    try {
      const values = await profileForm.validateFields();
      setProfileSettingsLoading(true);
      await updateProfile(id, values);
      message.success('已保存');
      setProfileSettingsOpen(false);
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '保存失败');
    } finally {
      setProfileSettingsLoading(false);
    }
  }, [id, profileForm, updateProfile]);

  const handleArchive = useCallback(
    async (versionId) => {
      try {
        await archiveVersion(versionId);
        message.success('已归档');
      } catch (err) {
        message.error(err?.message || '归档失败');
      }
    },
    [archiveVersion],
  );

  const activePublishedVersion = useMemo(
    () => versions.find((v) => v.status === 'active') || null,
    [versions],
  );

  const activePersonaName = useMemo(
    () => personas.find((p) => p.is_active)?.name || '未激活',
    [personas],
  );

  const bindingColumns = useMemo(
    () => [
      {
        title: '优先级',
        dataIndex: 'priority',
        key: 'priority',
        width: 80,
        align: 'center',
        render: (val) => (
          <Text style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{val}</Text>
        ),
      },
      {
        title: '指令库',
        dataIndex: 'library_name',
        key: 'library_name',
        render: (text, record) => (
          <Space>
            <Text strong>{text}</Text>
            <Text code style={{ fontSize: 'var(--font-size-xs)' }}>
              {record.library_key}
            </Text>
          </Space>
        ),
      },
      {
        title: '置信度阈值',
        dataIndex: 'confidence_threshold',
        key: 'confidence_threshold',
        width: 120,
        render: (val) => (
          <Text style={{ fontFamily: 'var(--font-mono)' }}>{val?.toFixed(2)}</Text>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        width: 100,
        render: (_, record) => (
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleRemoveBinding(record.library_id)}
          >
            解绑
          </Button>
        ),
      },
    ],
    [handleRemoveBinding],
  );

  const versionColumns = useMemo(
    () => [
      {
        title: '版本号',
        dataIndex: 'version_number',
        key: 'version_number',
        width: 120,
        render: (val) => (
          <Tag color="geekblue" style={{ fontFamily: 'var(--font-mono)' }}>
            {val}
          </Tag>
        ),
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        render: (status) =>
          status === 'active' ? (
            <Tag color="success">活跃</Tag>
          ) : (
            <Tag color="default">已归档</Tag>
          ),
      },
      {
        title: '发布时间',
        dataIndex: 'published_at',
        key: 'published_at',
        width: 170,
        render: (val) => (
          <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
            {val ? dayjs(val).format('YYYY-MM-DD HH:mm') : '-'}
          </Text>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        width: 100,
        render: (_, record) =>
          record.status === 'active' ? (
            <Button
              type="link"
              size="small"
              icon={<InboxOutlined />}
              onClick={() => handleArchive(record.id)}
            >
              归档
            </Button>
          ) : (
            <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
              已归档
            </Text>
          ),
      },
    ],
    [handleArchive],
  );

  if (detailLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        <Skeleton active paragraph={{ rows: 1 }} />
        <Card><Skeleton active paragraph={{ rows: 4 }} /></Card>
        <Card><Skeleton active paragraph={{ rows: 6 }} /></Card>
      </div>
    );
  }

  if (!profile) {
    return (
      <Empty description="对话方案不存在或加载失败">
        <Button type="primary" onClick={() => navigate('/dialog-profile')}>
          返回列表
        </Button>
      </Empty>
    );
  }

  const boundLibIds = new Set(bindings.map((b) => b.library_id));
  const unboundLibs = availableLibraries.filter((lib) => !boundLibIds.has(lib.id));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          {
            title: (
              <a onClick={() => navigate('/dialog-profile')} style={{ cursor: 'pointer' }}>
                对话方案管理
              </a>
            ),
          },
          { title: profile.name },
        ]}
      />

      {/* Back + Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/dialog-profile')}
          />
          <div>
            <Title level={4} style={{ marginBottom: 0 }}>{profile.name}</Title>
          </div>
          {profile.status === 'active' ? (
            <Tag color="success">已激活</Tag>
          ) : (
            <Tag color="default">草稿</Tag>
          )}
        </div>
        <Space>
          <Button
            icon={<SettingOutlined />}
            onClick={openProfileSettings}
          >
            LLM 配置
          </Button>
          <Button
            onClick={() => navigate(`/test-chat?profileId=${id}`)}
          >
            测试对话
          </Button>
          <Button
            type="primary"
            icon={<CloudUploadOutlined />}
            loading={publishLoading}
            onClick={handlePublish}
          >
            发布版本
          </Button>
        </Space>
      </div>

      {/* Info card */}
      <Card variant="borderless" style={cardSurface}>
        <Descriptions
          column={3}
          size="small"
          styles={{ label: { color: 'var(--color-text-secondary)', fontWeight: 500 } }}
        >
          <Descriptions.Item label="路由策略">
            <Tag color="blue">{ROUTE_LABELS[profile.route_strategy] || profile.route_strategy}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="指令阈值">
            <Text style={{ fontFamily: 'var(--font-mono)' }}>
              {profile.command_threshold?.toFixed(2) ?? '-'}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="会话超时">
            <Text style={{ fontFamily: 'var(--font-mono)' }}>
              {profile.session_timeout_min} 分钟
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="LLM 提供商">
            <Space size={8}>
              {profile.llm_provider || <Text type="secondary">未配置</Text>}
              <Button type="link" size="small" icon={<EditOutlined />} onClick={openProfileSettings} style={{ padding: 0 }}>
                编辑
              </Button>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="LLM 模型">
            {profile.llm_model || <Text type="secondary">未配置</Text>}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {profile.created_at ? dayjs(profile.created_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={3}>
            {profile.description || <Text type="secondary">暂无描述</Text>}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Personas */}
      <Card
        variant="borderless"
        style={cardSurface}
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <Text strong style={{ fontSize: 'var(--font-size-lg)' }}>人设管理</Text>
            <Space wrap>
              <Button
                size="small"
                icon={<SwapOutlined />}
                onClick={() => setPersonaSwitchOpen(true)}
                disabled={!personas.length}
              >
                切换人设
              </Button>
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                onClick={openCreatePersona}
              >
                新建人设
              </Button>
            </Space>
          </div>
        }
        styles={{ body: { padding: 'var(--space-6)' } }}
      >
        {personas.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无人设"
            style={{ padding: '32px 0' }}
          />
        ) : (
          <Row gutter={[16, 16]}>
            {personas.map((p) => {
              const traits = personaTraitTags(p);
              const active = !!p.is_active;
              const tone = p.tone_style || '—';
              const personaCard = (
                <Card
                  variant="borderless"
                  style={{
                    ...cardSurface,
                    borderLeft: `4px solid ${active ? 'var(--color-primary)' : 'var(--color-border)'}`,
                    height: '100%',
                  }}
                  actions={[
                    <Button key="edit" type="link" size="small" icon={<EditOutlined />} onClick={() => openEditPersona(p)}>
                      编辑
                    </Button>,
                    <Button
                      key="del"
                      type="link"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => setDeletePersonaTarget(p)}
                    >
                      删除
                    </Button>,
                  ]}
                >
                  <div style={{ marginBottom: 8 }}>
                    <Text strong style={{ fontSize: 'var(--font-size-lg)' }}>{p.name}</Text>
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>口吻风格</Text>
                    <div style={{ marginTop: 4 }}>
                      <Tag color="purple">{tone}</Tag>
                    </div>
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>性格特点</Text>
                    <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {traits.length ? traits.map((t) => (
                        <Tag key={t}>{t}</Tag>
                      )) : (
                        <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>—</Text>
                      )}
                    </div>
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>开场 / 提示预览</Text>
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      style={{ marginBottom: 0, marginTop: 6, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}
                    >
                      {greetingPreview(p)}
                    </Paragraph>
                  </div>
                  {!active && (
                    <Button type="primary" block icon={<CheckCircleOutlined />} onClick={() => handleActivatePersona(p.id)}>
                      激活
                    </Button>
                  )}
                </Card>
              );
              return (
                <Col xs={24} sm={12} lg={8} key={p.id}>
                  {active ? (
                    <Badge.Ribbon text="当前激活" color="blue">
                      {personaCard}
                    </Badge.Ribbon>
                  ) : (
                    personaCard
                  )}
                </Col>
              );
            })}
          </Row>
        )}
      </Card>

      {/* Library Bindings */}
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text strong style={{ fontSize: 'var(--font-size-lg)' }}>意图库绑定</Text>
            <Button
              type="primary"
              size="small"
              icon={<LinkOutlined />}
              onClick={openBindModal}
            >
              绑定意图库
            </Button>
          </div>
        }
        styles={{ body: { padding: 0 } }}
      >
        <Table
          rowKey="id"
          columns={bindingColumns}
          dataSource={bindings}
          pagination={false}
          scroll={{ x: 800 }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂未绑定意图库"
                style={{ padding: '32px 0' }}
              />
            ),
          }}
        />
      </Card>

      {/* Version History */}
      <Card
        title={
          <Text strong style={{ fontSize: 'var(--font-size-lg)' }}>发布版本历史</Text>
        }
        styles={{ body: { padding: 0 } }}
      >
        {versions.length > 0 && (
          <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border-light)' }}>
            <Timeline
              items={versions.map((v) => ({
                color: v.status === 'active' ? 'green' : 'gray',
                dot: v.status === 'active' ? <CheckCircleOutlined /> : <ClockCircleOutlined />,
                children: (
                  <div>
                    <Space size={8}>
                      <Text strong style={{ fontFamily: 'var(--font-mono)' }}>{v.version_number}</Text>
                      <Tag color={v.status === 'active' ? 'success' : 'default'}>
                        {v.status === 'active' ? '活跃' : '已归档'}
                      </Tag>
                    </Space>
                    <br />
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
                      {v.published_at ? dayjs(v.published_at).format('YYYY-MM-DD HH:mm') : '-'}
                    </Text>
                  </div>
                ),
              }))}
            />
          </div>
        )}
        <Table
          rowKey="id"
          columns={versionColumns}
          dataSource={versions}
          pagination={false}
          scroll={{ x: 800 }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无发布版本"
                style={{ padding: '32px 0' }}
              />
            ),
          }}
        />
      </Card>

      {/* Persona Editor Modal */}
      <PersonaEditor
        open={personaModalOpen}
        persona={editingPersona}
        onSave={handleSavePersona}
        onCancel={() => setPersonaModalOpen(false)}
        loading={personaLoading}
      />

      {/* Delete persona confirmation */}
      <DangerConfirmModal
        open={!!deletePersonaTarget}
        title="删除人设"
        description={`确定删除人设「${deletePersonaTarget?.name}」？`}
        onConfirm={handleDeletePersona}
        onCancel={() => setDeletePersonaTarget(null)}
        confirmLoading={deletePersonaLoading}
      />

      {/* Profile LLM settings */}
      <Modal
        open={profileSettingsOpen}
        title="LLM 配置"
        onCancel={() => setProfileSettingsOpen(false)}
        onOk={saveProfileSettings}
        confirmLoading={profileSettingsLoading}
        okText="保存"
        cancelText="取消"
        width={480}
        centered
        destroyOnHidden
      >
        <Form form={profileForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="llm_provider" label="LLM 提供商">
            <Select allowClear placeholder="选择提供商" options={LLM_PROVIDER_OPTIONS} />
          </Form.Item>
          <Form.Item name="llm_model" label="LLM 模型">
            <Input placeholder="例如部署名或模型 ID" maxLength={128} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Persona switch */}
      <Modal
        open={personaSwitchOpen}
        title="切换人设"
        onCancel={() => setPersonaSwitchOpen(false)}
        footer={null}
        width={920}
        centered
        destroyOnHidden
      >
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          {personas.map((p) => {
            const active = !!p.is_active;
            const traits = personaTraitTags(p);
            return (
              <Col xs={24} sm={12} md={8} key={p.id}>
                <Card
                  variant="borderless"
                  style={{
                    ...cardSurface,
                    border: active ? '2px solid var(--color-primary)' : '1px solid var(--color-border-light)',
                    height: '100%',
                  }}
                >
                  <Text strong style={{ fontSize: 'var(--font-size-base)' }}>{p.name}</Text>
                  <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {traits.slice(0, 4).map((t) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
                  </div>
                  <Button
                    type={active ? 'default' : 'primary'}
                    block
                    style={{ marginTop: 12 }}
                    disabled={active}
                    onClick={() => handleActivatePersona(p.id)}
                  >
                    {active ? '当前使用中' : '选择此人设'}
                  </Button>
                </Card>
              </Col>
            );
          })}
        </Row>
      </Modal>

      {/* Publish confirmation modal */}
      <Modal
        open={publishModalOpen}
        title="发布确认"
        onCancel={() => setPublishModalOpen(false)}
        footer={
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'flex-end', gap: 12 }}>
            <Checkbox
              checked={publishConfirmChecked}
              onChange={(e) => setPublishConfirmChecked(e.target.checked)}
              style={{ marginRight: 'auto' }}
            >
              我已确认以上变更
            </Checkbox>
            <Button onClick={() => setPublishModalOpen(false)}>取消</Button>
            <Button
              type="primary"
              loading={publishLoading}
              disabled={!publishConfirmChecked || publishCountdown > 0}
              onClick={confirmPublish}
            >
              {publishConfirmChecked && publishCountdown > 0 ? `发布 (${publishCountdown}s)` : '确认发布'}
            </Button>
          </div>
        }
        width={720}
        centered
        destroyOnHidden
      >
        <div style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Card
                variant="borderless"
                style={{
                  ...cardSurface,
                  background: '#f5f5f5',
                  border: '1px solid var(--color-border)',
                }}
                title={<Text strong>当前版本</Text>}
              >
                {activePublishedVersion ? (
                  <Space direction="vertical" size={6} style={{ width: '100%' }}>
                    <Text>版本号: <Text code style={{ fontFamily: 'var(--font-mono)' }}>{activePublishedVersion.version_number}</Text></Text>
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                      发布时间: {activePublishedVersion.published_at ? dayjs(activePublishedVersion.published_at).format('YYYY-MM-DD HH:mm') : '-'}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                      当时绑定指令库、人设等以该快照为准；下方右侧为当前草稿相对变更摘要。
                    </Text>
                  </Space>
                ) : (
                  <Text type="secondary">尚无已发布版本，本次将为首次发布。</Text>
                )}
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card
                variant="borderless"
                style={{
                  ...cardSurface,
                  background: '#f6ffed',
                  border: '1px solid #b7eb8f',
                }}
                title={<Text strong style={{ color: '#389e0d' }}>新版本（草稿摘要）</Text>}
              >
                <Space direction="vertical" size={8} style={{ width: '100%' }}>
                  <Text style={{ fontSize: 'var(--font-size-sm)' }}>
                    路由: <Tag>{ROUTE_LABELS[profile.route_strategy] || profile.route_strategy}</Tag>
                    {' · '}
                    指令阈值 <Text code>{profile.command_threshold?.toFixed(2) ?? '—'}</Text>
                  </Text>
                  <Text style={{ fontSize: 'var(--font-size-sm)' }}>
                    LLM: {profile.llm_provider || '—'} / {profile.llm_model || '—'}
                  </Text>
                  <Text style={{ fontSize: 'var(--font-size-sm)' }}>
                    已绑定指令库: <Text strong>{bindings.length}</Text> 个
                  </Text>
                  <Text style={{ fontSize: 'var(--font-size-sm)' }}>
                    人设: <Text strong>{personas.length}</Text> 个 · 当前激活 <Text strong>{activePersonaName}</Text>
                  </Text>
                </Space>
              </Card>
            </Col>
          </Row>
          <div style={{ marginTop: 'var(--space-6)' }}>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>发布前检查</Text>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <Text style={{ fontSize: 'var(--font-size-sm)' }}>
                {bindings.length > 0 ? '✅' : '⚠️'} 已绑定指令库 ({bindings.length} 个)
              </Text>
              <Text style={{ fontSize: 'var(--font-size-sm)' }}>
                {personas.some((p) => p.is_active) ? '✅' : '⚠️'} 已激活人设
              </Text>
              <Text style={{ fontSize: 'var(--font-size-sm)' }}>
                {profile?.llm_provider ? '✅' : '⚠️'} LLM 提供商
              </Text>
            </div>
          </div>
          <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginTop: 12 }}>
            勾选确认后需等待 5 秒方可点击「确认发布」，以防误操作。
          </Text>
        </div>
      </Modal>

      {/* Add binding modal */}
      <Modal
        open={bindModalOpen}
        title="绑定意图库"
        onCancel={() => setBindModalOpen(false)}
        onOk={handleAddBinding}
        confirmLoading={bindLoading}
        okText="绑定"
        cancelText="取消"
        okButtonProps={{ disabled: !selectedLibId }}
        width={480}
        centered
        destroyOnHidden
      >
        <div style={{ marginTop: 16 }}>
          <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
            选择一个尚未绑定的意图库
          </Text>
          <Select
            placeholder="选择意图库"
            value={selectedLibId}
            onChange={setSelectedLibId}
            style={{ width: '100%' }}
            showSearch
            optionFilterProp="label"
            options={unboundLibs.map((lib) => ({
              value: lib.id,
              label: `${lib.name} (${lib.library_key})`,
            }))}
            notFoundContent="无可绑定的意图库"
          />
        </div>
      </Modal>
    </div>
  );
}
