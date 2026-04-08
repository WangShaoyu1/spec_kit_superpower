import { Alert, Button, Card, Col, List, Row, Space, Statistic, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  downloadIntentModel,
  fetchIntentLibraryDetail,
  publishIntentModel,
  trainIntentLibraryModel,
} from '../../services/api'
import { getFirstTrainingDataset, getPrimaryModel, getPublishableModel } from './intentLibraryShared'

export function IntentLibraryDetailPage({ token }) {
  const navigate = useNavigate()
  const { libraryId } = useParams()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [downloadMeta, setDownloadMeta] = useState(null)

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

  const firstTrainingDataset = getFirstTrainingDataset(detail)
  const primaryModel = getPrimaryModel(detail)
  const publishableModel = getPublishableModel(detail)

  async function handleTrain() {
    if (!detail?.library || !firstTrainingDataset) return

    try {
      await trainIntentLibraryModel(token, detail.library.id, {
        training_dataset_id: firstTrainingDataset.id,
        version_name: `v${(detail.models?.length ?? 0) + 1}.0.0`,
      })
      await loadDetail()
      message.success('训练任务已创建')
    } catch (error) {
      message.error(error.message || '训练任务创建失败')
    }
  }

  async function handlePublish() {
    if (!publishableModel) return

    try {
      await publishIntentModel(token, publishableModel.id, { note: 'ready' })
      await loadDetail()
      message.success('模型已发布')
    } catch (error) {
      message.error(error.message || '模型发布失败，请先完成评估')
    }
  }

  async function handleDownload() {
    if (!primaryModel) return

    const result = await downloadIntentModel(token, primaryModel.id)
    setDownloadMeta(result)
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless" loading={loading}>
        {detail?.library ? (
          <div className="page-stack">
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
              <div>
                <div className="hero-eyebrow">Intent Library Detail</div>
                <h2 className="page-title">{detail.library.name}</h2>
                <Space wrap>
                  <Tag color="blue">{detail.library.library_key}</Tag>
                  <Tag color="gold">{detail.library.language}</Tag>
                  <Tag color="purple">{detail.models.length} 个模型版本</Tag>
                </Space>
              </div>
              <Space wrap>
                <Button onClick={() => navigate('/intent-library')}>返回指令库列表</Button>
                <Button onClick={() => navigate(`/intent-library/${libraryId}/datasets`)}>数据集管理</Button>
                <Button onClick={() => navigate(`/intent-library/${libraryId}/test`)}>模型测试</Button>
                <Button onClick={handleTrain} disabled={!firstTrainingDataset}>
                  发起训练
                </Button>
                <Button onClick={handlePublish} disabled={!publishableModel}>
                  发布模型
                </Button>
                <Button onClick={handleDownload} disabled={!primaryModel}>
                  下载元数据
                </Button>
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

            <Alert
              type={publishableModel ? 'success' : 'warning'}
              showIcon
              message="发布前检查"
              description={
                publishableModel
                  ? `当前可发布模型为 ${publishableModel.version_name}，状态 ${publishableModel.status}。`
                  : '当前没有可直接发布的模型，请先完成评估并进入 testable 状态。'
              }
            />

            <Row gutter={16}>
              <Col span={12}>
                <Card title="数据集摘要" variant="borderless">
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
                          title={item.version_name}
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

            {downloadMeta ? (
              <Alert
                type="info"
                showIcon
                message={`下载格式: ${downloadMeta.artifact_format}`}
                description={downloadMeta.artifact_uri}
              />
            ) : null}
          </div>
        ) : null}
      </Card>
    </div>
  )
}
