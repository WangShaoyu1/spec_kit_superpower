import { Badge, Button, Card, Col, Empty, Form, Input, Modal, Row, Select, Space, Statistic, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { createDialogProfile, fetchDialogProfiles, fetchKnowledgeBases } from '../../services/api'


const STATUS_META = {
  draft: { color: 'default', label: '草稿' },
  published: { color: 'success', label: '已发布' },
  archived: { color: 'processing', label: '已归档' },
}

const MODEL_OPTIONS = [
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'qwen-max', label: 'Qwen Max' },
]

const ROUTING_OPTIONS = [
  { value: 'intent_first', label: '指令优先' },
  { value: 'knowledge_first', label: '知识优先' },
  { value: 'hybrid', label: '混合策略' },
]


export function DialogProfilePage({ token }) {
  const navigate = useNavigate()
  const [directory, setDirectory] = useState({ items: [], summary: { total: 0, draft_count: 0, published_count: 0 }, current_published_profile: null })
  const [knowledgeBases, setKnowledgeBases] = useState([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm] = Form.useForm()

  async function loadDirectory() {
    setLoading(true)
    try {
      const [profilesPayload, knowledgePayload] = await Promise.all([
        fetchDialogProfiles(token),
        fetchKnowledgeBases(token),
      ])
      setDirectory(profilesPayload)
      setKnowledgeBases(knowledgePayload.categories ?? [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDirectory()
  }, [token])

  async function handleCreate(values) {
    await createDialogProfile(token, {
      ...values,
      library_ids: [],
      knowledge_base_id: values.knowledge_base_id ?? null,
    })
    setCreateOpen(false)
    createForm.resetFields()
    await loadDirectory()
    message.success(`方案 ${values.name} 创建成功`)
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
          <div>
            <div className="hero-eyebrow">Dialog Profile</div>
            <h2 style={{ color: '#fff', marginBottom: 8 }}>对话方案</h2>
            <p style={{ margin: 0, color: 'rgba(214, 224, 236, 0.78)' }}>
              管理大模型、人设、路由策略、发布门禁与手动测试入口。
            </p>
          </div>
          <Space>
            {directory.current_published_profile ? (
              <Tag color="green">当前发布: {directory.current_published_profile.name}</Tag>
            ) : null}
            <Button type="primary" size="large" onClick={() => setCreateOpen(true)}>
              新建方案
            </Button>
          </Space>
        </div>
      </Card>

      <Row gutter={18}>
        <Col span={8}>
          <Card className="module-card" variant="borderless">
            <Statistic title="方案总数" value={directory.summary.total ?? 0} />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="module-card" variant="borderless">
            <Statistic title="草稿方案" value={directory.summary.draft_count ?? 0} />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="module-card" variant="borderless">
            <Statistic title="已发布方案" value={directory.summary.published_count ?? 0} />
          </Card>
        </Col>
      </Row>

      <Card className="module-card" variant="borderless" loading={loading}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <strong style={{ color: '#fff' }}>方案目录</strong>
          <Badge count={directory.items.length} />
        </div>

        {directory.items.length > 0 ? (
          <div className="module-grid">
            {directory.items.map((item) => (
              <Card
                key={item.id}
                variant="borderless"
                style={{
                  background: item.status === 'published' ? 'linear-gradient(135deg, rgba(35, 69, 53, 0.9), rgba(19, 26, 39, 0.92))' : 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <div className="page-stack">
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                    <div>
                      <div style={{ color: '#fff', fontSize: 18, fontWeight: 700 }}>{item.name}</div>
                      <div style={{ color: 'rgba(214, 224, 236, 0.72)', marginTop: 6 }}>
                        {item.persona_name} · {item.llm_model}
                      </div>
                    </div>
                    <Tag color={STATUS_META[item.status]?.color}>{STATUS_META[item.status]?.label ?? item.status}</Tag>
                  </div>
                  <Space wrap>
                    <Tag color="blue">{item.routing_strategy}</Tag>
                    <Tag color="gold">阈值 {item.intent_threshold}</Tag>
                    <Tag>会话 {item.session_timeout_minutes} 分钟</Tag>
                  </Space>
                  <Button onClick={() => navigate(`/dialog-profiles/${item.id}`)}>查看详情</Button>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Empty description="暂无对话方案，请先创建一个方案" />
        )}
      </Card>

      <Modal
        title="新建对话方案"
        open={createOpen}
        destroyOnHidden
        onCancel={() => {
          setCreateOpen(false)
          createForm.resetFields()
        }}
        onOk={() => createForm.submit()}
        okText="创建方案"
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{
            llm_model: 'gpt-4o-mini',
            routing_strategy: 'intent_first',
            persona_name: '厨房助手',
            persona_prompt: '活泼友好的厨房助手',
            intent_threshold: 0.66,
            session_timeout_minutes: 15,
            knowledge_base_id: undefined,
          }}
        >
          <Form.Item name="name" label="方案名称" rules={[{ required: true }]}>
            <Input aria-label="方案名称" />
          </Form.Item>
          <Form.Item name="llm_model" label="模型" rules={[{ required: true }]}>
            <Select options={MODEL_OPTIONS} />
          </Form.Item>
          <Form.Item name="routing_strategy" label="路由策略" rules={[{ required: true }]}>
            <Select options={ROUTING_OPTIONS} />
          </Form.Item>
          <Form.Item name="persona_name" label="人设名称" rules={[{ required: true }]}>
            <Input aria-label="人设名称" />
          </Form.Item>
          <Form.Item name="persona_prompt" label="人设描述" rules={[{ required: true }]}>
            <Input.TextArea aria-label="人设描述" rows={4} />
          </Form.Item>
          <Form.Item name="intent_threshold" label="指令阈值" rules={[{ required: true }]}>
            <Input aria-label="指令阈值" />
          </Form.Item>
          <Form.Item name="session_timeout_minutes" label="会话超时（分钟）" rules={[{ required: true }]}>
            <Input aria-label="会话超时" />
          </Form.Item>
          <Form.Item name="knowledge_base_id" label="知识库">
            <Select
              aria-label="知识库"
              allowClear
              options={knowledgeBases.map((item) => ({ value: item.id, label: item.name }))}
              placeholder="选择当前方案绑定的知识库"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
