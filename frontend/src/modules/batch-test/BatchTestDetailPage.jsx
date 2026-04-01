import { Alert, Button, Card, Descriptions, Space, Statistic, Table, Tabs, Tag, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { executeBatchTest, fetchBatchTestDetail, generateBatchTestCases } from '../../services/api'


const STATUS_META = {
  draft: { color: 'default', label: '草稿' },
  ready: { color: 'processing', label: '待执行' },
  running: { color: 'warning', label: '执行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '执行失败' },
}

const EXECUTION_POLL_MS = 1000
const EXECUTION_MAX_POLLS = 10


export function BatchTestDetailPage({ token }) {
  const navigate = useNavigate()
  const { batchId } = useParams()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)

  const resultRows = useMemo(() => {
    const cases = detail?.cases ?? []
    const results = detail?.results ?? []
    const caseById = new Map(cases.map((item) => [item.id, item]))
    return results.map((result) => {
      const matchedCase = caseById.get(result.case_id)
      return {
        key: result.id,
        case_no: matchedCase?.case_no ?? '-',
        utterance: matchedCase?.utterance ?? '-',
        expected_route: matchedCase?.expected_route ?? '-',
        expected_intent: matchedCase?.expected_intent ?? '-',
        expected_slots: JSON.stringify(matchedCase?.expected_slots ?? {}),
        actual_route: result.actual_route,
        actual_intent: result.actual_intent,
        actual_slots: JSON.stringify(result.actual_slots ?? {}),
        passed: result.passed,
        score: result.score,
        latency_ms: result.latency_ms,
        failure_reason: result.failure_reason,
      }
    })
  }, [detail])

  async function fetchDetail({ showLoading = true } = {}) {
    if (showLoading) {
      setLoading(true)
    }
    try {
      const payload = await fetchBatchTestDetail(token, batchId)
      setDetail(payload)
      return payload
    } finally {
      if (showLoading) {
        setLoading(false)
      }
    }
  }

  async function loadDetail() {
    return fetchDetail()
  }

  async function pollExecutionResult() {
    setLoading(true)
    try {
      for (let attempt = 0; attempt < EXECUTION_MAX_POLLS; attempt += 1) {
        if (attempt > 0) {
          await new Promise((resolve) => window.setTimeout(resolve, EXECUTION_POLL_MS))
        }
        const payload = await fetchDetail({ showLoading: false })
        if (payload?.batch?.status !== 'running') {
          return payload
        }
      }
      return null
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDetail()
  }, [token, batchId])

  async function handleGenerate() {
    await generateBatchTestCases(token, batchId, { mode: 'auto' })
    await loadDetail()
    message.success('默认用例已生成')
  }

  async function handleExecute() {
    const result = await executeBatchTest(token, batchId, {})
    setDetail((current) => (current ? { ...current, batch: result.batch } : current))
    const settled = await pollExecutionResult()
    if (!settled) {
      message.error('批次仍在执行中，请稍后手动刷新')
      return
    }
    if (settled.batch.status === 'completed') {
      message.success('批次执行完成，结果已刷新')
      return
    }
    message.error('批次执行失败，请查看最新结果')
  }

  const batch = detail?.batch
  const analysis = detail?.analysis
  const thresholdSnapshot = batch?.threshold_snapshot ?? {}

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless" loading={loading}>
        {batch ? (
          <div className="page-stack">
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
              <div>
                <div className="hero-eyebrow">Batch Test Detail</div>
                <h2 style={{ color: '#fff', marginBottom: 8 }}>{batch.name}</h2>
                <Space wrap>
                  <Tag color={STATUS_META[batch.status]?.color}>{STATUS_META[batch.status]?.label ?? batch.status}</Tag>
                  <Tag color="blue">{batch.profile_name}</Tag>
                  <Tag color="gold">用例 {batch.case_count}</Tag>
                </Space>
              </div>
              <Space>
                <Button onClick={() => navigate('/batch-tests')}>返回列表</Button>
                <Button onClick={handleGenerate}>自动生成用例</Button>
                <Button type="primary" onClick={handleExecute}>执行批次</Button>
              </Space>
            </div>

            <Alert
              type={batch.status === 'completed' ? 'success' : 'info'}
              showIcon
              message={batch.status === 'completed' ? '后端指标已回读' : '等待执行'}
              description={
                batch.status === 'completed'
                  ? `accuracy ${detail.metrics.accuracy} / p95 ${detail.metrics.response_p95_ms}ms / command<=${thresholdSnapshot.command_response_p95_ms ?? '-'}ms / knowledge<=${thresholdSnapshot.knowledge_response_p95_ms ?? '-'}ms`
                  : '先生成用例，再执行批次以查看真实指标和分析报告。'
              }
            />

            <Descriptions
              bordered
              column={2}
              items={[
                { key: 'profile', label: '被测方案', children: batch.profile_name },
                { key: 'status', label: '批次状态', children: batch.status },
                { key: 'analysis', label: '分析状态', children: batch.analysis_status ?? '-' },
                { key: 'threshold', label: '阈值快照', children: JSON.stringify(thresholdSnapshot) },
              ]}
            />

            <Space size={16} wrap>
              <Card className="module-card" variant="borderless">
                <Statistic title="用例总数" value={batch.case_count ?? 0} />
              </Card>
              <Card className="module-card" variant="borderless">
                <Statistic title="已执行" value={batch.executed_count ?? 0} />
              </Card>
              <Card className="module-card" variant="borderless">
                <Statistic title="accuracy" value={detail.metrics.accuracy ?? 0} precision={2} />
              </Card>
              <Card className="module-card" variant="borderless">
                <Statistic title="p95 (ms)" value={detail.metrics.response_p95_ms ?? 0} />
              </Card>
            </Space>

            <Tabs
              items={[
                {
                  key: 'cases',
                  label: '测试用例',
                  children: (
                    <Table
                      rowKey="id"
                      pagination={false}
                      dataSource={detail.cases}
                      columns={[
                        { title: '编号', dataIndex: 'case_no' },
                        { title: '语句', dataIndex: 'utterance' },
                        { title: '预期路由', dataIndex: 'expected_route' },
                        { title: '预期意图', dataIndex: 'expected_intent' },
                      ]}
                    />
                  ),
                },
                {
                  key: 'results',
                  label: '执行结果',
                  children: (
                    <Table
                      pagination={false}
                      dataSource={resultRows}
                      columns={[
                        { title: '编号', dataIndex: 'case_no' },
                        { title: '语句', dataIndex: 'utterance' },
                        { title: '预期路由', dataIndex: 'expected_route' },
                        { title: '实际路由', dataIndex: 'actual_route' },
                        { title: '预期意图', dataIndex: 'expected_intent' },
                        { title: '实际意图', dataIndex: 'actual_intent' },
                        { title: '预期槽位', dataIndex: 'expected_slots' },
                        { title: '实际槽位', dataIndex: 'actual_slots' },
                        { title: '得分', dataIndex: 'score' },
                        { title: '耗时', dataIndex: 'latency_ms' },
                        {
                          title: '结果',
                          render: (_, row) => (row.passed ? <Tag color="success">通过</Tag> : <Tag color="error">未达标</Tag>),
                        },
                        { title: '失败原因', dataIndex: 'failure_reason' },
                      ]}
                    />
                  ),
                },
                {
                  key: 'analysis',
                  label: '智能分析',
                  children: (
                    <div className="page-stack">
                      <Card title="总体汇总" variant="borderless">
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                          {JSON.stringify(analysis?.summary ?? {}, null, 2)}
                        </pre>
                      </Card>
                      <Card title="阈值口径" variant="borderless">
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                          {JSON.stringify(thresholdSnapshot, null, 2)}
                        </pre>
                      </Card>
                      <Card title="混淆矩阵" variant="borderless">
                        <Table
                          pagination={false}
                          dataSource={(analysis?.confusion_matrix ?? []).map((item, index) => ({ key: `${item.expected_intent}-${item.actual_intent}-${index}`, ...item }))}
                          columns={[
                            { title: '预期意图', dataIndex: 'expected_intent' },
                            { title: '实际意图', dataIndex: 'actual_intent' },
                            { title: '数量', dataIndex: 'count' },
                          ]}
                        />
                      </Card>
                      <Card title="根因切片" variant="borderless">
                        <Space wrap>
                          {(analysis?.root_causes ?? []).map((item) => (
                            <Tag key={`${item.reason}-${item.count}`} color="red">
                              {item.reason} x {item.count}
                            </Tag>
                          ))}
                        </Space>
                      </Card>
                      <Card title="改进建议" variant="borderless">
                        <ul style={{ margin: 0, paddingLeft: 18 }}>
                          {(analysis?.recommendations ?? []).map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
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
