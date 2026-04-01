import { Button, Card, List, Space, Statistic, Tag } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { fetchIntentLibraryDetail } from '../../services/api'

export function IntentLibraryDatasetsPage({ token }) {
  const navigate = useNavigate()
  const { libraryId } = useParams()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)

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
              </Space>
            </div>

            <Space wrap size="large">
              <Statistic title="所属指令库" value={detail.library.name} />
              <Statistic title="训练集" value={detail.datasets.filter((item) => item.dataset_type === 'training').length} />
              <Statistic title="评估集" value={detail.datasets.filter((item) => item.dataset_type === 'evaluation').length} />
            </Space>

            <List
              dataSource={detail.datasets}
              renderItem={(item) => (
                <List.Item
                  key={item.id}
                  actions={[
                    <Button key="manage" onClick={() => navigate(`/intent-library/${libraryId}/datasets/${item.id}`)}>
                      管理数据
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={item.name}
                    description={
                      <Space wrap>
                        <Tag color={item.dataset_type === 'training' ? 'blue' : 'purple'}>{item.dataset_type}</Tag>
                        <Tag>{item.sample_count} 样本</Tag>
                        {item.bound_model_id ? <Tag color="gold">绑定模型</Tag> : <Tag>未绑定模型</Tag>}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        ) : null}
      </Card>
    </div>
  )
}
