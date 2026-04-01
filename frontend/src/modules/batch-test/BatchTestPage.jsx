import { Badge, Button, Card, Col, Empty, Form, Input, Modal, Row, Select, Space, Statistic, Tag, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { createBatchTest, fetchBatchTests, fetchDialogProfiles } from '../../services/api'


const STATUS_META = {
  draft: { color: 'default', label: '草稿' },
  ready: { color: 'processing', label: '待执行' },
  running: { color: 'warning', label: '执行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '执行失败' },
}


export function BatchTestPage({ token }) {
  const navigate = useNavigate()
  const [directory, setDirectory] = useState({
    items: [],
    summary: { total: 0, draft_count: 0, ready_count: 0, running_count: 0, completed_count: 0 },
  })
  const [profiles, setProfiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm] = Form.useForm()

  const profileOptions = useMemo(
    () => profiles.map((item) => ({ value: item.id, label: item.name })),
    [profiles],
  )

  async function loadDirectory() {
    setLoading(true)
    try {
      const [batchPayload, profilePayload] = await Promise.all([
        fetchBatchTests(token),
        fetchDialogProfiles(token),
      ])
      setDirectory(batchPayload)
      setProfiles(profilePayload.items ?? [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDirectory()
  }, [token])

  async function handleCreate(values) {
    await createBatchTest(token, {
      name: values.name,
      profile_id: values.profile_id,
      baseline_thresholds: {
        accuracy_min: Number(values.accuracy_min),
        command_response_p95_ms: Number(values.command_response_p95_ms),
        knowledge_response_p95_ms: Number(values.knowledge_response_p95_ms),
      },
    })
    setCreateOpen(false)
    createForm.resetFields()
    await loadDirectory()
    message.success(`批次 ${values.name} 创建成功`)
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
          <div>
            <div className="hero-eyebrow">Batch Regression Console</div>
            <h2 style={{ color: '#fff', marginBottom: 8 }}>批量测试</h2>
            <p style={{ margin: 0, color: 'rgba(214, 224, 236, 0.78)' }}>
              统一管理对话方案回归批次，跟踪用例数量、执行状态、准确率与响应时延。
            </p>
          </div>
          <Space>
            <Tag color="gold">真实回读 accuracy / p95</Tag>
            <Button type="primary" size="large" onClick={() => setCreateOpen(true)}>
              新建批次
            </Button>
          </Space>
        </div>
      </Card>

      <Row gutter={18}>
        <Col span={6}>
          <Card className="module-card" variant="borderless">
            <Statistic title="批次总数" value={directory.summary.total ?? 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="module-card" variant="borderless">
            <Statistic title="草稿批次" value={directory.summary.draft_count ?? 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="module-card" variant="borderless">
            <Statistic title="执行中批次" value={directory.summary.running_count ?? 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="module-card" variant="borderless">
            <Statistic title="已完成批次" value={directory.summary.completed_count ?? 0} />
          </Card>
        </Col>
      </Row>

      <Card className="module-card" variant="borderless" loading={loading}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <strong style={{ color: '#fff' }}>批次目录</strong>
          <Badge count={directory.items.length} />
        </div>

        {directory.items.length > 0 ? (
          <div className="module-grid">
            {directory.items.map((item) => (
              <Card
                key={item.id}
                variant="borderless"
                style={{
                  background: item.status === 'completed'
                    ? 'linear-gradient(135deg, rgba(22, 52, 74, 0.88), rgba(13, 21, 34, 0.94))'
                    : 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <div className="page-stack">
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                    <div>
                      <div style={{ color: '#fff', fontSize: 18, fontWeight: 700 }}>{item.name}</div>
                      <div style={{ color: 'rgba(214, 224, 236, 0.72)', marginTop: 6 }}>
                        被测方案: {item.profile_name}
                      </div>
                    </div>
                    <Tag color={STATUS_META[item.status]?.color}>{STATUS_META[item.status]?.label ?? item.status}</Tag>
                  </div>
                  <Space wrap>
                    <Tag color="blue">用例 {item.case_count ?? 0}</Tag>
                    <Tag color="green">通过 {item.pass_count ?? 0}</Tag>
                    <Tag color="purple">accuracy {(item.accuracy ?? 0).toFixed(2)}</Tag>
                    <Tag color="orange">p95 {item.response_p95_ms ?? 0}ms</Tag>
                  </Space>
                  <Button onClick={() => navigate(`/batch-tests/${item.id}`)}>查看详情</Button>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Empty description="暂无批次，请先为某个对话方案创建回归批次" />
        )}
      </Card>

      <Modal
        title="新建批量测试"
        open={createOpen}
        destroyOnHidden
        onCancel={() => {
          setCreateOpen(false)
          createForm.resetFields()
        }}
        onOk={() => createForm.submit()}
        okText="创建批次"
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{
            accuracy_min: 0.95,
            command_response_p95_ms: 200,
            knowledge_response_p95_ms: 2000,
          }}
        >
          <Form.Item name="name" label="批次名称" rules={[{ required: true }]}>
            <Input aria-label="批次名称" />
          </Form.Item>
          <Form.Item name="profile_id" label="被测方案" rules={[{ required: true }]}>
            <Select options={profileOptions} placeholder="选择对话方案" />
          </Form.Item>
          <Form.Item name="accuracy_min" label="准确率阈值" rules={[{ required: true }]}>
            <Input aria-label="准确率阈值" />
          </Form.Item>
          <Form.Item name="command_response_p95_ms" label="指令 P95 阈值" rules={[{ required: true }]}>
            <Input aria-label="指令 P95 阈值" />
          </Form.Item>
          <Form.Item name="knowledge_response_p95_ms" label="知识/闲聊 P95 阈值" rules={[{ required: true }]}>
            <Input aria-label="知识/闲聊 P95 阈值" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
