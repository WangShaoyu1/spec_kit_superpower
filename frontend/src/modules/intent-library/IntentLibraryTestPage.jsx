import { Alert, Button, Card, Form, Input, List, Space, Tabs, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  evaluateIntentModel,
  fetchIntentLibraryDetail,
  runIntentModelSingleTest,
} from '../../services/api'
import { getFirstEvaluationDataset, getPrimaryModel, getTestableModel } from './intentLibraryShared'

export function IntentLibraryTestPage({ token }) {
  const navigate = useNavigate()
  const { libraryId } = useParams()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [singleTestText, setSingleTestText] = useState('')
  const [singleTestResult, setSingleTestResult] = useState(null)

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

  const firstEvaluationDataset = getFirstEvaluationDataset(detail)
  const primaryModel = getPrimaryModel(detail)
  const testableModel = getTestableModel(detail)

  async function handleSingleTest() {
    if (!testableModel || !singleTestText.trim()) return
    try {
      const result = await runIntentModelSingleTest(token, testableModel.id, {
        utterance: singleTestText.trim(),
      })
      setSingleTestResult(result)
    } catch (error) {
      message.error(error.message || '单条测试执行失败')
    }
  }

  async function handleEvaluate() {
    if (!primaryModel || !firstEvaluationDataset) return
    await evaluateIntentModel(token, primaryModel.id, {
      evaluation_dataset_id: firstEvaluationDataset.id,
      threshold_override: { slot_f1_min: 0.91 },
    })
    await loadDetail()
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless" loading={loading}>
        {detail?.library ? (
          <div className="page-stack">
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
              <div>
                <div className="hero-eyebrow">Intent Testing</div>
                <h2 className="page-title">模型测试</h2>
                <p className="page-lede">当前页面同时承接单条测试与库内批量评估，不再跳到其他模块。</p>
              </div>
              <Space wrap>
                <Button onClick={() => navigate(`/intent-library/${libraryId}`)}>返回指令库详情</Button>
              </Space>
            </div>

            <Tabs
              items={[
                {
                  key: 'single',
                  label: '单条测试',
                  children: (
                    <Card title="单条测试" variant="borderless">
                      <Alert
                        type={testableModel ? 'info' : 'warning'}
                        showIcon
                        message="执行口径"
                        description={
                          testableModel
                            ? `当前单条测试命中的是规则引擎兜底结果，执行模型 ${testableModel.version_name}（${testableModel.status}）。`
                            : '当前没有可测试模型，请先完成训练与评估，让模型进入 testable 状态。'
                        }
                      />
                      <Form layout="vertical">
                        <Form.Item label="单条测试">
                          <Input.TextArea
                            aria-label="单条测试"
                            value={singleTestText}
                            onChange={(event) => setSingleTestText(event.target.value)}
                            rows={3}
                          />
                        </Form.Item>
                        <Button type="primary" onClick={handleSingleTest} disabled={!testableModel}>
                          执行测试
                        </Button>
                      </Form>
                      {singleTestResult ? (
                        <div className="page-stack" style={{ marginTop: 16 }}>
                          <Space wrap>
                            <Tag color="blue">{singleTestResult.intent}</Tag>
                            <Tag color="green">置信度 {singleTestResult.confidence}</Tag>
                            <Tag color="purple">{singleTestResult.latency_ms} ms</Tag>
                          </Space>
                          <Space wrap>
                            <Tag>模型版本 {singleTestResult.model_version}</Tag>
                            <Tag>当前状态 {singleTestResult.model_status}</Tag>
                            <Tag color="orange">规则引擎结果</Tag>
                          </Space>
                          {singleTestResult.response ? (
                            <Alert type="success" showIcon message="响应草案" description={singleTestResult.response} />
                          ) : null}
                        </div>
                      ) : null}
                    </Card>
                  ),
                },
                {
                  key: 'batch',
                  label: '批量测试',
                  children: (
                    <div className="page-stack">
                      <Alert
                        type="info"
                        showIcon
                        message="指令库内批量评估"
                        description="当前页展示的是当前指令库模型的评估任务与结果，不再跳转到对话方案批量测试模块。"
                      />
                      <Space>
                        <Button onClick={handleEvaluate} disabled={!primaryModel || !firstEvaluationDataset}>
                          发起批量评估
                        </Button>
                      </Space>
                      <Card title="评估记录" variant="borderless">
                        <List
                          locale={{ emptyText: '暂无批量评估记录' }}
                          dataSource={detail.evaluation_runs}
                          renderItem={(item) => (
                            <List.Item key={item.id}>
                              <List.Item.Meta
                                title={item.id}
                                description={
                                  <div className="page-stack">
                                    <Space wrap>
                                      <Tag color={item.status === 'succeeded' ? 'green' : 'processing'}>{item.status}</Tag>
                                      <Tag>准确率 {item.metrics.command_intent_accuracy ?? '--'}</Tag>
                                      <Tag>Slot F1 {item.metrics.slot_f1 ?? '--'}</Tag>
                                    </Space>
                                    {item.analysis?.summary ? (
                                      <Alert
                                        type="success"
                                        showIcon
                                        message={item.analysis.summary}
                                        description={(item.analysis.recommendations ?? []).join(' / ')}
                                      />
                                    ) : null}
                                  </div>
                                }
                              />
                            </List.Item>
                          )}
                        />
                      </Card>
                    </div>
                  ),
                },
              ]}
            />
          </div>
        ) : null}
      </Card>
    </div>
  )
}
