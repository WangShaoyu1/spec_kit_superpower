import { Button, Card, Empty, Form, Input, Modal, Select, Space, Table, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import {
  createIntentLibrary,
  deleteIntentLibrary,
  fetchIntentLibraries,
} from '../../services/api'
import { DEFAULT_THRESHOLDS } from './intentLibraryShared'


export function IntentLibraryPage({ token }) {
  const navigate = useNavigate()
  const [libraries, setLibraries] = useState([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [createForm] = Form.useForm()

  async function loadDirectory() {
    setLoading(true)
    try {
      const directory = await fetchIntentLibraries(token)
      setLibraries(directory.items)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDirectory()
  }, [token])

  async function handleCreate(values) {
    try {
      const result = await createIntentLibrary(token, {
        ...values,
        default_thresholds: DEFAULT_THRESHOLDS,
      })
      setCreateOpen(false)
      createForm.resetFields()
      await loadDirectory()
      message.success(`指令库 ${values.name} 创建成功`)
      navigate(`/intent-library/${result.library.id}`)
    } catch (error) {
      const nextMessage = error.message || '指令库创建失败'
      createForm.setFields([{ name: 'library_key', errors: [nextMessage] }])
    }
  }

  async function handleDelete(libraryId) {
    if (!window.confirm('删除后将移除该指令库及其关联模型、数据集和评估记录，是否继续？')) {
      return
    }
    try {
      await deleteIntentLibrary(token, libraryId)
      await loadDirectory()
      message.success('指令库已删除')
    } catch (error) {
      message.error(error.message || '指令库删除失败')
    }
  }

  const filteredLibraries = libraries.filter((item) => {
    const normalizedQuery = query.trim().toLowerCase()
    if (!normalizedQuery) {
      return true
    }
    return item.name.toLowerCase().includes(normalizedQuery) || item.library_key.toLowerCase().includes(normalizedQuery)
  })

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <div className="page-header-row">
          <div>
            <div className="hero-eyebrow">Intent Library</div>
            <h2 className="page-title">指令库管理</h2>
            <p className="page-lede">
              按指令库列表进入详情、数据集管理和模型测试，恢复 PD 定义的主流程边界。
            </p>
          </div>
          <Button type="primary" size="large" onClick={() => setCreateOpen(true)}>
            新建指令库
          </Button>
        </div>
      </Card>

      <Card className="module-card" variant="borderless" loading={loading}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Input
            placeholder="按名称或 Key 筛选"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          {filteredLibraries.length > 0 ? (
          <Table
            rowKey="id"
            pagination={false}
            dataSource={filteredLibraries}
            columns={[
              {
                title: '指令库名称',
                dataIndex: 'name',
                render: (_, item) => <Link to={`/intent-library/${item.id}`}>{item.name}</Link>,
              },
              {
                title: '唯一 Key',
                dataIndex: 'library_key',
                render: (value) => <Tag color="blue">{value}</Tag>,
              },
              {
                title: '语种',
                dataIndex: 'language',
                render: (value) => <Tag color="gold">{value}</Tag>,
              },
              {
                title: '模型数',
                dataIndex: 'model_count',
                render: (value) => `${value} 个模型`,
              },
              {
                title: '发布状态',
                key: 'published',
                render: (_, item) => (
                  item.published_model_id ? <Tag color="green">已发布模型</Tag> : <Tag>未发布</Tag>
                ),
              },
              {
                title: '操作',
                key: 'actions',
                render: (_, item) => (
                  <Space>
                    <Button type="link" onClick={() => navigate(`/intent-library/${item.id}`)}>
                      进入详情
                    </Button>
                    <Button
                      danger
                      type="link"
                      disabled={Boolean(item.published_model_id)}
                      onClick={() => void handleDelete(item.id)}
                    >
                      删除
                    </Button>
                  </Space>
                ),
              },
            ]}
          />
        ) : (
          <Empty description="暂无指令库，先创建一个开始配置主流程" />
        )}
        </Space>
      </Card>

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
