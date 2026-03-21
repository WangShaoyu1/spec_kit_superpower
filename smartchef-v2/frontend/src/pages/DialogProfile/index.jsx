import { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Button,
  Input,
  Select,
  Table,
  Tag,
  Card,
  Row,
  Col,
  Space,
  Modal,
  Form,
  InputNumber,
  Slider,
  Tooltip,
  message,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  MessageOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useProfileStore from '../../stores/profileStore';
import DangerConfirmModal from '../../components/DangerConfirmModal';

const { Title, Text } = Typography;

const STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'testing', label: '测试中' },
  { value: 'published', label: '已发布' },
  { value: 'archived', label: '已归档' },
];

const ROUTE_STRATEGY_LABELS = {
  intent_first: '指令优先',
  command_first: '指令优先',
  knowledge_first: '知识优先',
  auto: '均衡',
  balanced: '均衡',
};

const STRATEGY_OPTIONS = [
  { value: '', label: '全部策略' },
  { value: 'command_first', label: '指令优先' },
  { value: 'knowledge_first', label: '知识优先' },
  { value: 'balanced', label: '均衡' },
];

const LLM_PROVIDER_OPTIONS = [
  { value: 'GPT-4o', label: 'GPT-4o' },
  { value: 'GPT-4o-mini', label: 'GPT-4o-mini' },
  { value: 'Qwen-Max', label: 'Qwen-Max' },
  { value: 'Qwen-Plus', label: 'Qwen-Plus' },
  { value: 'GLM-4', label: 'GLM-4' },
  { value: 'GLM-4-Flash', label: 'GLM-4-Flash' },
];

const STAT_CARDS = [
  {
    key: 'total',
    field: 'total',
    label: '方案总数',
    icon: <MessageOutlined />,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  {
    key: 'published',
    field: 'active',
    label: '已发布',
    icon: <CheckCircleOutlined />,
    gradient: 'linear-gradient(135deg, #52c41a 0%, #95de64 100%)',
  },
  {
    key: 'draft',
    field: 'draft',
    label: '草稿',
    icon: <FileTextOutlined />,
    gradient: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
  },
  {
    key: 'testing',
    field: 'testing',
    label: '测试中',
    icon: <ExperimentOutlined />,
    gradient: 'linear-gradient(135deg, #1677ff 0%, #69b1ff 100%)',
  },
];

export default function DialogProfile() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [strategyFilter, setStrategyFilter] = useState('');

  const {
    profiles,
    loading,
    total,
    page,
    pageSize,
    search,
    statusFilter,
    stats,
    fetchProfiles,
    fetchStats,
    createProfile,
    updateProfile,
    deleteProfile,
    setSearch,
    setStatusFilter,
    setPage,
    setPageSize,
  } = useProfileStore();

  useEffect(() => {
    fetchProfiles();
    fetchStats();
  }, [fetchProfiles, fetchStats, page, pageSize, search, statusFilter]);

  const openCreate = useCallback(() => {
    setEditingProfile(null);
    form.resetFields();
    form.setFieldsValue({
      command_threshold: 0.7,
      route_strategy: 'intent_first',
      session_timeout_min: 10,
    });
    setModalOpen(true);
  }, [form]);

  const openEdit = useCallback(
    (record) => {
      setEditingProfile(record);
      form.setFieldsValue({
        name: record.name,
        description: record.description,
        command_threshold: record.command_threshold,
        route_strategy: record.route_strategy,
        llm_provider: record.llm_provider,
        llm_model: record.llm_model,
        session_timeout_min: record.session_timeout_min,
      });
      setModalOpen(true);
    },
    [form],
  );

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      if (editingProfile) {
        await updateProfile(editingProfile.id, values);
        message.success('更新成功');
      } else {
        await createProfile(values);
        message.success('创建成功');
      }
      setModalOpen(false);
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    } finally {
      setSubmitLoading(false);
    }
  }, [form, editingProfile, createProfile, updateProfile]);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await deleteProfile(deleteTarget.id);
      message.success('删除成功');
      setDeleteTarget(null);
    } catch (err) {
      message.error(err?.message || '删除失败');
    } finally {
      setDeleteLoading(false);
    }
  }, [deleteTarget, deleteProfile]);

  const filteredProfiles = useMemo(() => {
    if (!strategyFilter) return profiles;
    const aliasMap = {
      command_first: ['command_first', 'intent_first'],
      balanced: ['balanced', 'auto'],
    };
    const matchValues = aliasMap[strategyFilter] || [strategyFilter];
    return profiles.filter((p) => matchValues.includes(p.route_strategy));
  }, [profiles, strategyFilter]);

  const handleQuery = useCallback(() => {
    setPage(1);
    fetchProfiles();
    fetchStats();
  }, [setPage, fetchProfiles, fetchStats]);

  const handleReset = useCallback(() => {
    setSearch('');
    setStatusFilter('');
    setStrategyFilter('');
    setPage(1);
  }, [setSearch, setStatusFilter, setPage]);

  const columns = useMemo(
    () => [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
        width: 160,
        ellipsis: true,
        render: (text, record) => (
          <Button
            type="link"
            style={{ padding: 0, fontWeight: 500 }}
            onClick={() => navigate(`/dialog-profile/${record.id}`)}
          >
            {text}
          </Button>
        ),
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        render: (status) => {
          const map = {
            draft: { color: 'default', label: '草稿' },
            testing: { color: 'processing', label: '测试中' },
            published: { color: 'success', label: '已发布' },
            active: { color: 'success', label: '已发布' },
            archived: { color: 'default', label: '已归档' },
          };
          const cfg = map[status] || { color: 'default', label: status };
          return <Tag color={cfg.color}>{cfg.label}</Tag>;
        },
      },
      {
        title: '路由策略',
        dataIndex: 'route_strategy',
        key: 'route_strategy',
        width: 100,
        render: (val) => (
          <Tag color="blue">{ROUTE_STRATEGY_LABELS[val] || val}</Tag>
        ),
      },
      {
        title: '大模型',
        key: 'llm',
        width: 150,
        ellipsis: true,
        render: (_, record) => {
          const provider = record.llm_provider;
          const model = record.llm_model;
          if (!provider && !model) return <Text type="secondary">-</Text>;
          return (
            <Tooltip title={[provider, model].filter(Boolean).join(' / ')}>
              <Text style={{ fontSize: 'var(--font-size-xs)' }}>
                {[provider, model].filter(Boolean).join(' / ')}
              </Text>
            </Tooltip>
          );
        },
      },
      {
        title: '指令阈值',
        dataIndex: 'command_threshold',
        key: 'command_threshold',
        width: 100,
        align: 'center',
        render: (val) => (
          <Text style={{ fontFamily: 'var(--font-mono)' }}>
            {val != null ? `${(val * 100).toFixed(0)}%` : '-'}
          </Text>
        ),
      },
      {
        title: '会话超时',
        dataIndex: 'session_timeout_min',
        key: 'session_timeout_min',
        width: 100,
        align: 'center',
        render: (val) => (
          <Text style={{ fontFamily: 'var(--font-mono)' }}>
            {val != null ? `${val} 分钟` : '-'}
          </Text>
        ),
      },
      {
        title: '指令库',
        dataIndex: 'bindings_count',
        key: 'bindings_count',
        width: 110,
        align: 'center',
        render: (count) => {
          const n = count ?? 0;
          return (
            <Tag color={n > 0 ? 'blue' : 'default'} style={{ margin: 0, fontSize: 'var(--font-size-xs)' }}>
              {n} 个指令库
            </Tag>
          );
        },
      },
      {
        title: '最新版本',
        dataIndex: 'latest_version',
        key: 'latest_version',
        width: 100,
        render: (val) =>
          val ? (
            <Tag color="geekblue" style={{ fontFamily: 'var(--font-mono)' }}>
              {val}
            </Tag>
          ) : (
            <Text type="secondary">-</Text>
          ),
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
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
        width: 200,
        render: (_, record) => (
          <Space size={4}>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/dialog-profile/${record.id}`)}
            >
              详情
            </Button>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => openEdit(record)}
            >
              编辑
            </Button>
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => setDeleteTarget(record)}
            >
              删除
            </Button>
          </Space>
        ),
      },
    ],
    [navigate, openEdit],
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>
            对话方案管理
          </Title>
          <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
            配置对话方案，管理人设、绑定意图库并发布版本
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新建方案
        </Button>
      </div>

      {/* Stat cards */}
      <Row gutter={16}>
        {STAT_CARDS.map((card) => (
          <Col span={6} key={card.key}>
            <Card
              style={{ minWidth: 180, borderRadius: 'var(--radius-lg)', border: 'none', overflow: 'hidden' }}
              styles={{ body: { padding: '20px 24px' } }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 'var(--radius-lg)',
                    background: card.gradient,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 22,
                    color: '#fff',
                    flexShrink: 0,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  }}
                >
                  {card.icon}
                </div>
                <div>
                  <Text
                    type="secondary"
                    style={{ fontSize: 'var(--font-size-xs)', display: 'block' }}
                  >
                    {card.label}
                  </Text>
                  <Text
                    strong
                    style={{
                      fontSize: 'var(--font-size-2xl)',
                      fontFamily: 'var(--font-mono)',
                      lineHeight: 1.2,
                    }}
                  >
                    {stats[card.field] ?? 0}
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Filter bar + Table */}
      <Card style={{ minWidth: 0 }} styles={{ body: { padding: 0 } }}>
        <div
          style={{
            padding: '16px 24px',
            display: 'flex',
            gap: 12,
            borderBottom: '1px solid var(--color-border-light)',
          }}
        >
          <Input
            placeholder="搜索方案名称..."
            prefix={<SearchOutlined style={{ color: 'var(--color-text-tertiary)' }} />}
            allowClear
            style={{ width: 320 }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            options={STATUS_OPTIONS}
            style={{ width: 140 }}
          />
          <Select
            value={strategyFilter}
            onChange={setStrategyFilter}
            options={STRATEGY_OPTIONS}
            style={{ width: 140 }}
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={handleQuery}>
            查询
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
        </div>

        <div style={{ minWidth: 0, overflow: 'hidden' }}>
          <Table
            rowKey="id"
            columns={columns}
            dataSource={filteredProfiles}
            loading={loading}
            tableLayout="fixed"
            scroll={{ x: true }}
            pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p, ps) => {
              setPage(p);
              if (ps !== pageSize) setPageSize(ps);
            },
            style: { padding: '0 24px 16px' },
          }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无对话方案"
                style={{ padding: '48px 0' }}
              >
                <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
                  创建第一个方案
                </Button>
              </Empty>
            ),
          }}
          />
        </div>
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        open={modalOpen}
        title={editingProfile ? '编辑方案' : '新建方案'}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitLoading}
        okText={editingProfile ? '保存' : '创建'}
        cancelText="取消"
        width={560}
        centered
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="方案名称"
            rules={[{ required: true, message: '请输入方案名称' }]}
          >
            <Input placeholder="例如: 智能烹饪助手" maxLength={100} />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="方案用途描述..." maxLength={500} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="route_strategy"
                label="路由策略"
                rules={[{ required: true, message: '请选择' }]}
              >
                <Select
                  options={[
                    { value: 'intent_first', label: '指令优先' },
                    { value: 'knowledge_first', label: '知识优先' },
                    { value: 'auto', label: '自动' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="session_timeout_min"
                label="会话超时(分钟)"
                rules={[{ required: true, message: '请输入' }]}
              >
                <InputNumber min={1} max={1440} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="command_threshold" label="指令置信度阈值">
            <Slider min={0} max={1} step={0.05} marks={{ 0: '0', 0.5: '0.5', 1: '1.0' }} />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="llm_provider" label="LLM 提供商">
                <Select allowClear placeholder="选择提供商" options={LLM_PROVIDER_OPTIONS} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="llm_model" label="LLM 模型">
                <Input placeholder="例如: gpt-4o-mini" maxLength={64} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Delete confirmation */}
      <DangerConfirmModal
        open={!!deleteTarget}
        title="删除对话方案"
        description={`确定删除方案「${deleteTarget?.name}」？删除后所有关联的人设、绑定和测试会话也将被删除。`}
        impactText="此操作不可恢复。存在活跃发布版本时无法删除。"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        confirmLoading={deleteLoading}
      />
    </div>
  );
}
