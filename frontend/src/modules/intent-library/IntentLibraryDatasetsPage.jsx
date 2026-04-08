import { Button, Card, Form, Input, Modal, Select, Space, Statistic, Table, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { createIntentDataset, fetchIntentLibraryDetail } from '../../services/api'

export function IntentLibraryDatasetsPage({ token }) {
  const navigate = useNavigate()
  const { libraryId } = useParams()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [createSource, setCreateSource] = useState('manual')
  const [form] = Form.useForm()

  async function loadDetail() {
    setLoading(true)
    try {
      const nextDetail = await fetchIntentLibraryDetail(token, libraryId)
      setDetail(nextDetail)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDetail()
  }, [token, libraryId])

  async function handleCreateDataset(values) {
    try {
      const entries = createSource === 'import'
        ? (values.import_entries || '')
          .split(/\r?\n/)
          .map((item) => item.trim())
          .filter(Boolean)
        : []
      await createIntentDataset(token, libraryId, {
        ...values,
        source: createSource,
        sample_count: createSource === 'llm' ? 12 : entries.length,
        entries,
      })
      setCreateOpen(false)
      form.resetFields()
      await loadDetail()
      message.success('数据集已创建')
    } catch (error) {
      message.error(error.message || '数据集创建失败')
    }
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless" loading={loading}>
        {detail?.library ? (
          <div className="page-stack">
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
              <div>
                <div className="hero-eyebrow">Intent Datasets</div>
                <h2 className="page-title">数据集管理</h2>
                <p className="page-lede">围绕当前指令库查看训练集、评估集和绑定关系。</p>
              </div>
              <Space wrap>
                <Button onClick={() => navigate(`/intent-library/${libraryId}`)}>返回指令库详情</Button>
                <Button
                  type="primary"
                  onClick={() => {
                    setCreateSource('manual')
                    setCreateOpen(true)
                  }}
                >
                  新建数据集
                </Button>
                <Button
                  onClick={() => {
                    setCreateSource('llm')
                    setCreateOpen(true)
                  }}
                >
                  LLM 合成
                </Button>
                <Button
                  onClick={() => {
                    setCreateSource('import')
                    setCreateOpen(true)
                  }}
                >
                  导入数据集
                </Button>
              </Space>
            </div>

            <Space wrap size="large">
              <Statistic title="所属指令库" value={detail.library.name} />
              <Statistic title="训练集" value={detail.datasets.filter((item) => item.dataset_type === 'training').length} />
              <Statistic title="评估集" value={detail.datasets.filter((item) => item.dataset_type === 'evaluation').length} />
            </Space>

            <Table
              rowKey="id"
              pagination={false}
              dataSource={detail.datasets}
              columns={[
                {
                  title: '数据集名称',
                  dataIndex: 'name',
                },
                {
                  title: '类型',
                  dataIndex: 'dataset_type',
                  render: (value) => <Tag color={value === 'training' ? 'blue' : 'purple'}>{value}</Tag>,
                },
                {
                  title: '样本数',
                  dataIndex: 'sample_count',
                  render: (value) => `${value} 样本`,
                },
                {
                  title: '绑定状态',
                  dataIndex: 'bound_model_id',
                  render: (value) => (value ? <Tag color="gold">绑定模型</Tag> : <Tag>未绑定模型</Tag>),
                },
                {
                  title: '操作',
                  key: 'actions',
                  render: (_, item) => (
                    <Button onClick={() => navigate(`/intent-library/${libraryId}/datasets/${item.id}`)}>
                      管理数据
                    </Button>
                  ),
                },
              ]}
            />
          </div>
        ) : null}
      </Card>

      <Modal
        title={createSource === 'llm' ? 'LLM 合成数据集' : createSource === 'import' ? '导入数据集' : '新建数据集'}
        open={createOpen}
        onCancel={() => {
          setCreateOpen(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        okText="保存数据集"
      >
        <Form form={form} layout="vertical" onFinish={handleCreateDataset}>
          <Form.Item name="name" label="数据集名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="dataset_type" label="数据集类型" rules={[{ required: true }]} initialValue="training">
            <Select
              options={[
                { value: 'training', label: '训练集' },
                { value: 'evaluation', label: '评估集' },
              ]}
            />
          </Form.Item>
          {createSource === 'import' ? (
            <Form.Item
              name="import_entries"
              label="导入样本"
              rules={[{ required: true, message: '请输入至少一条导入样本' }]}
            >
              <Input.TextArea rows={5} placeholder={'每行一条样本，例如:\n打开烤箱\n关闭烤箱'} />
            </Form.Item>
          ) : null}
        </Form>
      </Modal>
    </div>
  )
}
