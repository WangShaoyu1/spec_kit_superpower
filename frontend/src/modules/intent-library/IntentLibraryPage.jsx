import { Button, Card, Empty, Form, Input, List, Modal, Select, Space, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import {
  createIntentLibrary,
  fetchIntentLibraries,
} from '../../services/api'
import { DEFAULT_THRESHOLDS } from './intentLibraryShared'


export function IntentLibraryPage({ token }) {
  const navigate = useNavigate()
  const [libraries, setLibraries] = useState([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
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
    const result = await createIntentLibrary(token, {
      ...values,
      default_thresholds: DEFAULT_THRESHOLDS,
    })
    setCreateOpen(false)
    createForm.resetFields()
    await loadDirectory()
    message.success(`指令库 ${values.name} 创建成功`)
    navigate(`/intent-library/${result.library.id}`)
  }

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
        {libraries.length > 0 ? (
          <List
            dataSource={libraries}
            renderItem={(item) => (
              <List.Item
                key={item.id}
                actions={[
                  <Button key="detail" type="link" onClick={() => navigate(`/intent-library/${item.id}`)}>
                    进入详情
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={<Link to={`/intent-library/${item.id}`}>{item.name}</Link>}
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
        ) : (
          <Empty description="暂无指令库，先创建一个开始配置主流程" />
        )}
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
