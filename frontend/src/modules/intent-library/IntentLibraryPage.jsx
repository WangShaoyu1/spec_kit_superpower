import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  List,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Tag,
  message,
} from 'antd'
import { useEffect, useMemo, useState } from 'react'

import {
  createIntentLibrary,
  downloadIntentModel,
  evaluateIntentModel,
  fetchIntentLibraries,
  fetchIntentLibraryDetail,
  publishIntentModel,
  runIntentModelSingleTest,
  trainIntentLibraryModel,
} from '../../services/api'


const DEFAULT_THRESHOLDS = {
  command_intent_accuracy_min: 0.95,
  slot_f1_min: 0.9,
  response_p95_ms: 2000,
}


export function IntentLibraryPage({ token }) {
  const [libraries, setLibraries] = useState([])
  const [selectedLibraryId, setSelectedLibraryId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm] = Form.useForm()
  const [singleTestText, setSingleTestText] = useState('')
  const [singleTestResult, setSingleTestResult] = useState(null)
  const [downloadMeta, setDownloadMeta] = useState(null)

  const firstTrainingDataset = useMemo(
    () => detail?.datasets?.find((item) => item.dataset_type === 'training'),
    [detail],
  )
  const firstEvaluationDataset = useMemo(
    () => detail?.datasets?.find((item) => item.dataset_type === 'evaluation'),
    [detail],
  )
  const primaryModel = useMemo(() => detail?.models?.[0] ?? null, [detail])

  async function loadDirectory(targetLibraryId) {
    setLoading(true)
    try {
      const directory = await fetchIntentLibraries(token)
      setLibraries(directory.items)
      const nextLibraryId = targetLibraryId ?? directory.items[0]?.id ?? null
      setSelectedLibraryId(nextLibraryId)
      if (nextLibraryId) {
        const nextDetail = await fetchIntentLibraryDetail(token, nextLibraryId)
        setDetail(nextDetail)
      } else {
        setDetail(null)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDirectory()
  }, [token])

  async function selectLibrary(libraryId) {
    setSelectedLibraryId(libraryId)
    setLoading(true)
    try {
      const nextDetail = await fetchIntentLibraryDetail(token, libraryId)
      setDetail(nextDetail)
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(values) {
    const result = await createIntentLibrary(token, {
      ...values,
      default_thresholds: DEFAULT_THRESHOLDS,
    })
    setCreateOpen(false)
    createForm.resetFields()
    await loadDirectory(result.library.id)
    message.success(`指令库 ${values.name} 创建成功`)
  }

  async function handleTrain() {
    if (!detail?.library || !firstTrainingDataset) return
    await trainIntentLibraryModel(token, detail.library.id, {
      training_dataset_id: firstTrainingDataset.id,
      version_name: `v${(detail.models?.length ?? 0) + 1}.0.0`,
    })
    await loadDirectory(detail.library.id)
    message.success('训练任务已创建')
  }

  async function handleEvaluate() {
    if (!primaryModel || !firstEvaluationDataset || !detail?.library) return
    await evaluateIntentModel(token, primaryModel.id, {
      evaluation_dataset_id: firstEvaluationDataset.id,
      threshold_override: { slot_f1_min: 0.91 },
    })
    await loadDirectory(detail.library.id)
    message.success('评估任务已创建')
  }

  async function handlePublish() {
    if (!primaryModel || !detail?.library) return
    await publishIntentModel(token, primaryModel.id, { note: 'ready' })
    await loadDirectory(detail.library.id)
    message.success('模型已发布')
  }

  async function handleDownload() {
    if (!primaryModel) return
    const result = await downloadIntentModel(token, primaryModel.id)
    setDownloadMeta(result)
  }

  async function handleSingleTest() {
    if (!primaryModel || !singleTestText.trim()) return
    const result = await runIntentModelSingleTest(token, primaryModel.id, {
      utterance: singleTestText.trim(),
    })
    setSingleTestResult(result)
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
          <div>
            <div className="hero-eyebrow">Intent Library</div>
            <h2 style={{ color: '#fff', marginBottom: 8 }}>指令库管理</h2>
            <p style={{ margin: 0, color: 'rgba(214, 224, 236, 0.78)' }}>
              管理指令库、训练集、评估任务、模型发布和单条测试。
            </p>
          </div>
          <Button type="primary" size="large" onClick={() => setCreateOpen(true)}>
            新建指令库
          </Button>
        </div>
      </Card>

      <Row gutter={18}>
        <Col span={8}>
          <Card className="module-card" variant="borderless" loading={loading}>
            <Statistic title="指令库数量" value={libraries.length} />
            <List
              style={{ marginTop: 16 }}
              dataSource={libraries}
              renderItem={(item) => (
                <List.Item
                  key={item.id}
                  style={{
                    cursor: 'pointer',
                    borderRadius: 16,
                    padding: '14px 12px',
                    background: item.id === selectedLibraryId ? 'rgba(255, 176, 77, 0.12)' : 'transparent',
                  }}
                  onClick={() => selectLibrary(item.id)}
                >
                  <List.Item.Meta
                    title={<span style={{ color: '#fff' }}>{item.name}</span>}
                    description={
                      <Space wrap>
                        <Tag color="blue">{item.library_key}</Tag>
                        <Tag color="gold">{item.language}</Tag>
                        <Tag>{item.model_count} 个模型</Tag>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col span={16}>
          <Card className="module-card" variant="borderless" loading={loading}>
            {detail?.library ? (
              <div className="page-stack">
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ color: '#fff', marginBottom: 8 }}>{detail.library.name}</h3>
                    <Space wrap>
                      <Tag color="blue">{detail.library.library_key}</Tag>
                      <Tag color="purple">{detail.library.language}</Tag>
                      <Tag color="gold">阈值冻结</Tag>
                    </Space>
                  </div>
                  <Space wrap>
                    <Button onClick={handleTrain}>发起训练</Button>
                    <Button onClick={handleEvaluate} disabled={!primaryModel}>发起评估</Button>
                    <Button onClick={handlePublish} disabled={!primaryModel}>发布模型</Button>
                    <Button onClick={handleDownload} disabled={!primaryModel}>下载元数据</Button>
                  </Space>
                </div>

                <Row gutter={16}>
                  <Col span={8}>
                    <Card variant="borderless">
                      <Statistic title="训练集数" value={detail.datasets.filter((item) => item.dataset_type === 'training').length} />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card variant="borderless">
                      <Statistic title="评估集数" value={detail.datasets.filter((item) => item.dataset_type === 'evaluation').length} />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card variant="borderless">
                      <Statistic title="模型版本数" value={detail.models.length} />
                    </Card>
                  </Col>
                </Row>

                <Alert
                  type="warning"
                  showIcon
                  message="条件准入口径"
                  description={(detail.partial_requirements ?? []).join(' / ')}
                />

                <Row gutter={16}>
                  <Col span={12}>
                    <Card title="数据集" variant="borderless">
                      <List
                        dataSource={detail.datasets}
                        renderItem={(item) => (
                          <List.Item key={item.id}>
                            <List.Item.Meta
                              title={item.name}
                              description={`${item.dataset_type} · ${item.sample_count} 样本`}
                            />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card title="模型版本" variant="borderless">
                      <List
                        dataSource={detail.models}
                        renderItem={(item) => (
                          <List.Item key={item.id}>
                            <List.Item.Meta
                              title={<span style={{ color: '#fff' }}>{item.version_name}</span>}
                              description={
                                <Space wrap>
                                  <Tag color="blue">{item.status}</Tag>
                                  {item.is_testable ? <Tag color="green">testable</Tag> : null}
                                  {item.is_published ? <Tag color="gold">published</Tag> : null}
                                </Space>
                              }
                            />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Col>
                </Row>

                <Card title="单条测试" variant="borderless">
                  <Form layout="vertical">
                    <Form.Item label="单条测试">
                      <Input.TextArea
                        aria-label="单条测试"
                        value={singleTestText}
                        onChange={(event) => setSingleTestText(event.target.value)}
                        rows={3}
                      />
                    </Form.Item>
                    <Button type="primary" onClick={handleSingleTest} disabled={!primaryModel}>
                      执行测试
                    </Button>
                  </Form>
                  {singleTestResult ? (
                    <div style={{ marginTop: 16 }}>
                      <Space wrap>
                        <Tag color="blue">{singleTestResult.intent}</Tag>
                        <Tag color="green">置信度 {singleTestResult.confidence}</Tag>
                        <Tag color="purple">{singleTestResult.latency_ms} ms</Tag>
                      </Space>
                    </div>
                  ) : null}
                </Card>

                {downloadMeta ? (
                  <Alert
                    type="info"
                    showIcon
                    message={`下载格式: ${downloadMeta.artifact_format}`}
                    description={downloadMeta.artifact_uri}
                  />
                ) : null}
              </div>
            ) : (
              <Alert type="info" showIcon message="暂无指令库" description="先创建一个指令库以开始训练与评估。" />
            )}
          </Card>
        </Col>
      </Row>

      <Modal
        title="创建指令库"
        open={createOpen}
        onCancel={() => {
          setCreateOpen(false)
          createForm.resetFields()
        }}
        onOk={() => createForm.submit()}
        okText="创建"
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{ language: 'zh' }}
        >
          <Form.Item name="library_key" label="唯一 Key" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="language" label="语种" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'zh', label: '中文' },
                { value: 'en', label: '英文' },
              ]}
            />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
