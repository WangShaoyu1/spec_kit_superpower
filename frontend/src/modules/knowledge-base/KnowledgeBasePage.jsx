import { Alert, Badge, Button, Card, Col, Empty, Form, Input, Modal, Row, Select, Space, Statistic, Tag, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  createKnowledgeCategory,
  fetchKnowledgeBases,
  uploadKnowledgeDocument,
} from '../../services/api'


const STATUS_META = {
  empty: { color: 'default', label: '空分类' },
  indexing: { color: 'processing', label: '处理中' },
  ready: { color: 'success', label: '就绪' },
  uploading: { color: 'processing', label: '上传中' },
  parsing: { color: 'processing', label: '解析中' },
  failed: { color: 'error', label: '失败' },
}


export function KnowledgeBasePage({ token }) {
  const navigate = useNavigate()
  const [directory, setDirectory] = useState({ categories: [], documents: [] })
  const [selectedCategoryId, setSelectedCategoryId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [categoryOpen, setCategoryOpen] = useState(false)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [categoryForm] = Form.useForm()
  const [uploadForm] = Form.useForm()

  const selectedCategory = useMemo(
    () => directory.categories.find((item) => item.id === selectedCategoryId) ?? null,
    [directory.categories, selectedCategoryId],
  )

  async function loadDirectory(targetCategoryId) {
    setLoading(true)
    try {
      const baseDirectory = await fetchKnowledgeBases(token)
      const nextCategoryId = targetCategoryId ?? selectedCategoryId ?? baseDirectory.categories[0]?.id ?? null
      const scoped = nextCategoryId
        ? await fetchKnowledgeBases(token, { category_id: nextCategoryId })
        : { categories: baseDirectory.categories, documents: [] }
      setDirectory({
        categories: baseDirectory.categories,
        documents: scoped.documents,
      })
      setSelectedCategoryId(nextCategoryId)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDirectory()
  }, [token])

  async function handleCreateCategory(values) {
    await createKnowledgeCategory(token, values)
    setCategoryOpen(false)
    categoryForm.resetFields()
    await loadDirectory()
    message.success(`分类 ${values.name} 创建成功`)
  }

  async function handleUpload(values) {
    await uploadKnowledgeDocument(token, selectedCategoryId, values)
    setUploadOpen(false)
    uploadForm.resetFields()
    await loadDirectory(selectedCategoryId)
    message.success(`文档 ${values.name} 已提交索引`)
  }

  const totalDocuments = directory.categories.reduce((sum, item) => sum + item.document_count, 0)
  const totalReady = directory.categories.reduce((sum, item) => sum + item.ready_document_count, 0)

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
          <div>
            <div className="hero-eyebrow">Knowledge Base</div>
            <h2 style={{ color: '#fff', marginBottom: 8 }}>知识库管理</h2>
            <p style={{ margin: 0, color: 'rgba(214, 224, 236, 0.78)' }}>
              管理知识分类、上传文档、查看过滤结果，并验证检索是否真实命中。
            </p>
          </div>
          <Space>
            <Button size="large" onClick={() => setCategoryOpen(true)}>
              新建分类
            </Button>
            <Button type="primary" size="large" disabled={!selectedCategoryId} onClick={() => setUploadOpen(true)}>
              上传文档
            </Button>
          </Space>
        </div>
      </Card>

      <Row gutter={18}>
        <Col span={8}>
          <Card className="module-card" variant="borderless">
            <Statistic title="分类数" value={directory.categories.length} />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="module-card" variant="borderless">
            <Statistic title="文档总数" value={totalDocuments} />
          </Card>
        </Col>
        <Col span={8}>
          <Card className="module-card" variant="borderless">
            <Statistic title="已索引" value={totalReady} />
          </Card>
        </Col>
      </Row>

      <Row gutter={18}>
        <Col span={8}>
          <Card className="module-card" variant="borderless" loading={loading}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <strong style={{ color: '#fff' }}>知识分类</strong>
              <Badge count={directory.categories.length} />
            </div>
            <div className="page-stack">
              {directory.categories.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => void loadDirectory(item.id)}
                  style={{
                    textAlign: 'left',
                    width: '100%',
                    borderRadius: 16,
                    border: item.id === selectedCategoryId ? '1px solid rgba(255,176,77,0.7)' : '1px solid rgba(255,255,255,0.08)',
                    background: item.id === selectedCategoryId ? 'rgba(255,176,77,0.08)' : 'rgba(255,255,255,0.02)',
                    padding: 14,
                    color: '#fff',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 600 }}>{item.icon} {item.name}</div>
                      <div style={{ marginTop: 6, color: 'rgba(214, 224, 236, 0.76)', fontSize: 13 }}>{item.description}</div>
                    </div>
                    <Tag color={STATUS_META[item.status]?.color}>{STATUS_META[item.status]?.label ?? item.status}</Tag>
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </Col>

        <Col span={16}>
          <Card className="module-card" variant="borderless" loading={loading}>
            {selectedCategory ? (
              <div className="page-stack">
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
                  <div>
                    <h3 style={{ color: '#fff', marginBottom: 8 }}>{selectedCategory.icon} {selectedCategory.name}</h3>
                    <Space wrap>
                      <Tag color={STATUS_META[selectedCategory.status]?.color}>{STATUS_META[selectedCategory.status]?.label ?? selectedCategory.status}</Tag>
                      <Tag>{selectedCategory.document_count} 个文档</Tag>
                      <Tag color="green">{selectedCategory.ready_document_count} 个已索引</Tag>
                    </Space>
                  </div>
                </div>

                <Alert
                  type="info"
                  showIcon
                  message="字段过滤说明"
                  description="JSON 文档会自动过滤图片 URL、OSS 链接、互动计数和审核状态等无效字段；Markdown 文档按标题分段建立索引。"
                />

                {directory.documents.length > 0 ? (
                  <div className="directory-table-wrap">
                    <table className="directory-table">
                      <thead>
                        <tr>
                          <th>文档名称</th>
                          <th>格式</th>
                          <th>状态</th>
                          <th>索引版本</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {directory.documents.map((item) => (
                          <tr key={item.id}>
                            <td>{item.name}</td>
                            <td><Tag color={item.format === 'json' ? 'blue' : 'green'}>{item.format}</Tag></td>
                            <td><Tag color={STATUS_META[item.status]?.color}>{STATUS_META[item.status]?.label ?? item.status}</Tag></td>
                            <td>v{item.index_version}</td>
                            <td>
                              <Button size="small" onClick={() => navigate(`/knowledge-base/${item.id}`)}>
                                查看详情
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <Empty description="当前分类暂无文档" />
                )}
              </div>
            ) : (
              <Empty description="暂无分类，请先创建一个知识分类" />
            )}
          </Card>
        </Col>
      </Row>

      <Modal
        title="新建分类"
        open={categoryOpen}
        destroyOnHidden
        onCancel={() => {
          setCategoryOpen(false)
          categoryForm.resetFields()
        }}
        onOk={() => categoryForm.submit()}
        okText="创建分类"
      >
        <Form form={categoryForm} layout="vertical" onFinish={handleCreateCategory} initialValues={{ icon: '🍳' }}>
          <Form.Item name="name" label="分类名称" rules={[{ required: true }]}>
            <Input aria-label="分类名称" />
          </Form.Item>
          <Form.Item name="icon" label="图标" rules={[{ required: true }]}>
            <Select options={[
              { value: '🍳', label: '🍳 菜谱' },
              { value: '🏢', label: '🏢 公司' },
              { value: '📚', label: '📚 指南' },
            ]} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={selectedCategory ? `上传文档 - ${selectedCategory.name}` : '上传文档'}
        open={uploadOpen}
        destroyOnHidden
        onCancel={() => {
          setUploadOpen(false)
          uploadForm.resetFields()
        }}
        onOk={() => uploadForm.submit()}
        okText="提交文档"
      >
        <Form form={uploadForm} layout="vertical" onFinish={handleUpload} initialValues={{ format: 'json' }}>
          <Form.Item name="name" label="文档名称" rules={[{ required: true }]}>
            <Input aria-label="文档名称" />
          </Form.Item>
          <Form.Item name="format" label="文档格式" rules={[{ required: true }]}>
            <Select options={[
              { value: 'json', label: 'JSON' },
              { value: 'markdown', label: 'Markdown' },
            ]} />
          </Form.Item>
          <Form.Item name="content" label="文档内容" rules={[{ required: true }]}>
            <Input.TextArea aria-label="文档内容" rows={8} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
