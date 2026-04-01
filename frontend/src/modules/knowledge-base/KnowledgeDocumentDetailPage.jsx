import { Alert, Button, Card, Col, Empty, Form, Input, Modal, Row, Space, Table, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  deleteKnowledgeDocument,
  fetchKnowledgeDocumentDetail,
  reindexKnowledgeDocument,
  runKnowledgeRetrieveTest,
} from '../../services/api'


export function KnowledgeDocumentDetailPage({ token }) {
  const navigate = useNavigate()
  const { documentId } = useParams()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [result, setResult] = useState(null)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [retrieveForm] = Form.useForm()

  async function loadDetail() {
    setLoading(true)
    try {
      const nextDetail = await fetchKnowledgeDocumentDetail(token, documentId)
      setDetail(nextDetail)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDetail()
  }, [token, documentId])

  async function handleReindex() {
    await reindexKnowledgeDocument(token, documentId, { reason: 'manual_refresh' })
    await loadDetail()
    message.success('已提交重新索引')
  }

  async function handleRetrieve(values) {
    const nextResult = await runKnowledgeRetrieveTest(token, documentId, values)
    setResult(nextResult)
    await loadDetail()
  }

  async function handleDelete() {
    await deleteKnowledgeDocument(token, documentId)
    setDeleteOpen(false)
    message.success('文档已删除')
    navigate('/knowledge-base')
  }

  const document = detail?.document

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless" loading={loading}>
        {document ? (
          <div className="page-stack">
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
              <div>
                <div className="hero-eyebrow">Knowledge Detail</div>
                <h2 className="page-title">{document.name}</h2>
                <Space wrap>
                  <Tag color={document.format === 'json' ? 'blue' : 'green'}>{document.format}</Tag>
                  <Tag color="gold">索引版本 v{document.index_version}</Tag>
                  <Tag color={document.status === 'ready' ? 'green' : 'processing'}>{document.status}</Tag>
                </Space>
              </div>
              <Space>
                <Button onClick={() => navigate('/knowledge-base')}>返回列表</Button>
                <Button onClick={handleReindex}>重新索引</Button>
                <Button danger onClick={() => setDeleteOpen(true)}>删除文档</Button>
              </Space>
            </div>

            <Row gutter={18}>
              <Col span={12}>
                <Card title="有效字段" variant="borderless">
                  <Table
                    pagination={false}
                    rowKey="field"
                    dataSource={detail.valid_content}
                    columns={[
                      { title: '字段', dataIndex: 'field' },
                      { title: '值', dataIndex: 'value', render: (value) => Array.isArray(value) ? value.join(' / ') : String(value) },
                    ]}
                  />
                </Card>
              </Col>
              <Col span={12}>
                <Card title="过滤字段" variant="borderless">
                  {detail.filtered_fields.length > 0 ? (
                    <Table
                      pagination={false}
                      rowKey="field"
                      dataSource={detail.filtered_fields}
                      columns={[
                        { title: '字段', dataIndex: 'field' },
                        { title: '原因', dataIndex: 'reason' },
                      ]}
                    />
                  ) : (
                    <Empty description="当前文档没有被过滤字段" />
                  )}
                </Card>
              </Col>
            </Row>

            <Card title="检索测试" variant="borderless">
              <Form form={retrieveForm} layout="vertical" onFinish={handleRetrieve}>
                <Form.Item name="query" label="检索语句" rules={[{ required: true }]}>
                  <Input aria-label="检索语句" />
                </Form.Item>
                <Button type="primary" onClick={() => retrieveForm.submit()}>
                  执行检索验证
                </Button>
              </Form>

              {result ? (
                <Alert
                  style={{ marginTop: 16 }}
                  type={result.hit ? 'success' : 'warning'}
                  showIcon
                  message={result.hit ? `命中，得分 ${result.score}` : '未命中'}
                  description={result.hit ? `${result.snippet} | ${result.response_preview}` : result.response_preview}
                />
              ) : null}
            </Card>
          </div>
        ) : (
          <Empty description="文档不存在或已删除" />
        )}
      </Card>

      <Modal
        title="确认删除文档"
        open={deleteOpen}
        onCancel={() => setDeleteOpen(false)}
        onOk={handleDelete}
        okText="确认删除"
        okButtonProps={{ danger: true }}
      >
        <Alert
          type="warning"
          showIcon
          message="删除后文档内容与检索记录都会被移除"
        />
      </Modal>
    </div>
  )
}
