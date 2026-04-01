import { Alert, Button, Card, Form, Input, Select, Space, Tag, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  fetchDialogProfileDetail,
  fetchIntentLibraries,
  fetchKnowledgeBases,
  publishDialogProfile,
  updateDialogProfile,
} from '../../services/api'


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


export function DialogProfileDetailPage({ token }) {
  const navigate = useNavigate()
  const { profileId } = useParams()
  const [detail, setDetail] = useState(null)
  const [libraries, setLibraries] = useState([])
  const [knowledgeBases, setKnowledgeBases] = useState([])
  const [loading, setLoading] = useState(true)
  const [publishResult, setPublishResult] = useState(null)
  const [form] = Form.useForm()

  const libraryOptions = useMemo(
    () => libraries.map((item) => ({ value: item.id, label: item.name })),
    [libraries],
  )

  async function loadDetail() {
    setLoading(true)
    try {
      const [detailPayload, libraryPayload, knowledgePayload] = await Promise.all([
        fetchDialogProfileDetail(token, profileId),
        fetchIntentLibraries(token),
        fetchKnowledgeBases(token),
      ])
      setDetail(detailPayload)
      setLibraries(libraryPayload.items)
      setKnowledgeBases(knowledgePayload.categories ?? [])
      form.setFieldsValue({
        ...detailPayload.profile,
        library_ids: detailPayload.bindings.map((item) => item.library_id),
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDetail()
  }, [token, profileId])

  async function handleSave(values) {
    await updateDialogProfile(token, profileId, {
      ...values,
      intent_threshold: Number(values.intent_threshold),
      session_timeout_minutes: Number(values.session_timeout_minutes),
      knowledge_base_id: values.knowledge_base_id ?? null,
    })
    setPublishResult(null)
    await loadDetail()
    message.success('方案配置已保存')
  }

  async function handlePublish() {
    try {
      const result = await publishDialogProfile(token, profileId, { note: 'ready' })
      setPublishResult({ type: 'success', items: [], version: result.profile.publish_version })
      await loadDetail()
      message.success('方案已发布')
    } catch (error) {
      const guardItems = error?.payload?.data?.guard_items ?? []
      setPublishResult({ type: 'warning', items: guardItems, version: null })
    }
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless" loading={loading}>
        {detail?.profile ? (
          <div className="page-stack">
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
              <div>
                <div className="hero-eyebrow">Dialog Profile Detail</div>
                <h2 className="page-title">{detail.profile.name}</h2>
                <Space wrap>
                  <Tag color={detail.profile.status === 'published' ? 'green' : 'default'}>{detail.profile.status}</Tag>
                  <Tag color="purple">{detail.profile.llm_model}</Tag>
                  <Tag color="gold">v{detail.profile.publish_version}</Tag>
                </Space>
              </div>
              <Space>
                <Button onClick={() => navigate('/dialog-profiles')}>返回列表</Button>
                <Button onClick={() => navigate('/batch-tests')}>进入平台批量测试</Button>
                <Button onClick={() => navigate(`/dialog-profiles/${profileId}/test`)}>进入手动测试</Button>
                <Button type="primary" onClick={() => form.submit()}>保存配置</Button>
                <Button onClick={handlePublish}>发布方案</Button>
              </Space>
            </div>

            {publishResult ? (
              <Alert
                type={publishResult.type}
                showIcon
                message={publishResult.type === 'success' ? `发布成功，版本 ${publishResult.version}` : '发布门禁未通过'}
                description={publishResult.type === 'success' ? '当前方案已成为最新 published 方案。' : publishResult.items.join(' / ')}
              />
            ) : (
              <Alert
                type="info"
                showIcon
                message="发布前校验"
                description="若绑定指令库没有 published 模型，后端会阻断发布并返回 blocker 列表。"
              />
            )}

            <Form form={form} layout="vertical" onFinish={handleSave}>
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
              <Form.Item name="library_ids" label="绑定指令库">
                <Select
                  mode="multiple"
                  options={libraryOptions}
                  placeholder="选择当前方案绑定的指令库"
                />
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

            <Card title="当前绑定快照" variant="borderless">
              <Space wrap>
                {detail.bindings.length > 0 ? detail.bindings.map((item) => (
                  <Tag key={item.id} color={item.published_model_name ? 'green' : 'red'}>
                    {item.library_name} / {item.published_model_name ?? '无 published 模型'}
                  </Tag>
                )) : <Tag>暂无绑定指令库</Tag>}
              </Space>
            </Card>
          </div>
        ) : null}
      </Card>
    </div>
  )
}
