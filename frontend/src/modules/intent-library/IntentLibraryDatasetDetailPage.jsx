import { Button, Card, Empty, Space, Table, Tag } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { fetchIntentDatasetDetail } from '../../services/api'

export function IntentLibraryDatasetDetailPage({ token }) {
  const navigate = useNavigate()
  const { libraryId, datasetId } = useParams()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)

  async function loadDetail() {
    setLoading(true)
    try {
      const nextDetail = await fetchIntentDatasetDetail(token, libraryId, datasetId)
      setDetail(nextDetail)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDetail()
  }, [token, libraryId, datasetId])

  const samples = detail?.samples ?? []
  const dataset = detail?.dataset

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless" loading={loading}>
        {dataset ? (
          <div className="page-stack">
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
              <div>
                <div className="hero-eyebrow">Dataset Detail</div>
                <h2 className="page-title">{dataset.name}</h2>
                <Space wrap>
                  <Tag color={dataset.dataset_type === 'training' ? 'blue' : 'purple'}>{dataset.dataset_type}</Tag>
                  <Tag>{dataset.sample_count} 样本</Tag>
                  <Tag>{dataset.schema_version}</Tag>
                </Space>
              </div>
              <Space wrap>
                <Button onClick={() => navigate(`/intent-library/${libraryId}/datasets`)}>返回数据集列表</Button>
              </Space>
            </div>

            <Card title="意图样本" variant="borderless">
              {samples.length > 0 ? (
                <Table
                  pagination={{ pageSize: 8 }}
                  rowKey={(record) => record.intent_key}
                  dataSource={samples}
                  columns={[
                    { title: 'intent_key', dataIndex: 'intent_key' },
                    { title: '显示名称', dataIndex: 'display_name' },
                    {
                      title: '必填槽位',
                      dataIndex: 'required_slots',
                      render: (value) => (value?.length ? value.map((item) => item.name).join(' / ') : '无'),
                    },
                    {
                      title: '追问样例',
                      dataIndex: 'prompt_samples',
                      render: (value) => (value?.length ? value.join(' / ') : '无'),
                    },
                  ]}
                />
              ) : (
                <Empty description="当前数据集暂无样本" />
              )}
            </Card>
          </div>
        ) : null}
      </Card>
    </div>
  )
}
