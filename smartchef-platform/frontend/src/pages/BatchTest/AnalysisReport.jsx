/**
 * 批量测试分析报告组件
 * 功能：混淆矩阵可视化、归因分析、优化建议、趋势对比
 *
 * 使用方式：
 * 1. report: 传入完整分析报告对象（含 confusion_matrix, attributions, suggestions）
 * 2. suiteId: 传入套件 ID，自行调用 /testing/batch/suites/{id}/report 获取
 * 3. jobId: 传入任务 ID，自行调用 batch-test API 获取 job + cases 并计算
 * 4. job + cases: 直接传入任务和用例列表，客户端计算分析
 */
import { useEffect, useState } from 'react';
import {
  Card, Table, Tag, Typography, Space, Spin, Empty, Row, Col, message,
} from 'antd';
import { BarChartOutlined, BulbOutlined, WarningOutlined } from '@ant-design/icons';
import api from '../../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const CONFIDENCE_THRESHOLD = 0.6;
const ATTRIBUTION_LABELS = {
  route_mismatch: '路由域判断错误（预期域与实际域不一致）',
  intent_mismatch: '意图分类错误（域正确但意图识别错误）',
  low_confidence: `低置信度识别（置信度低于 ${CONFIDENCE_THRESHOLD}）`,
  no_intent_detected: '未检测到意图（Pipeline 返回空意图）',
  other: '其他未归类错误',
};

/** 根据 cases 客户端计算混淆矩阵、归因、建议 */
function computeAnalysis(job, cases) {
  const matrix = {};
  const failedCases = (cases || []).filter((c) => !c.passed);

  (cases || []).forEach((c) => {
    const exp = c.expected_intent || 'unknown';
    const act = c.actual_intent || 'none';
    if (!matrix[exp]) matrix[exp] = {};
    matrix[exp][act] = (matrix[exp][act] || 0) + 1;
  });

  const attributions = {};
  failedCases.forEach((c) => {
    let cat = 'other';
    if (
      c.expected_domain &&
      c.actual_domain &&
      c.expected_domain !== c.actual_domain
    ) {
      cat = 'route_mismatch';
    } else if (c.actual_intent == null) {
      cat = 'no_intent_detected';
    } else if (
      c.intent_confidence != null &&
      c.intent_confidence < CONFIDENCE_THRESHOLD
    ) {
      cat = 'low_confidence';
    } else if (
      c.expected_intent &&
      c.actual_intent !== c.expected_intent
    ) {
      cat = 'intent_mismatch';
    }
    if (!attributions[cat]) attributions[cat] = { count: 0, examples: [] };
    attributions[cat].count += 1;
    if (attributions[cat].examples.length < 5) {
      attributions[cat].examples.push({
        input_text: c.input_text,
        expected_intent: c.expected_intent,
        actual_intent: c.actual_intent,
        expected_domain: c.expected_domain,
        actual_domain: c.actual_domain,
        intent_confidence: c.intent_confidence,
      });
    }
  });

  const totalFail = failedCases.length || 1;
  const attributionsList = Object.entries(attributions)
    .map(([cat, { count, examples }]) => ({
      category: cat,
      description: ATTRIBUTION_LABELS[cat] || cat,
      count,
      percentage: Math.round((count / totalFail) * 1000) / 10,
      examples,
    }))
    .sort((a, b) => b.count - a.count);

  const suggestions = [];
  const acc = job?.accuracy ?? 0;
  if (acc < 0.9) {
    suggestions.push(
      `整体准确率 ${(acc * 100).toFixed(1)}% 低于 90%，建议全面审查训练数据覆盖度和路由策略配置。`
    );
  }
  const avgLat = job?.avg_latency_ms ?? 0;
  if (avgLat > 200) {
    suggestions.push(
      `平均响应延迟 ${avgLat.toFixed(0)}ms 超过 200ms 阈值，建议优化 Pipeline 性能或缩减知识库检索范围。`
    );
  }
  if (suggestions.length === 0) {
    suggestions.push('所有指标表现良好，暂无优化建议。');
  }

  return {
    confusion_matrix: matrix,
    attributions: attributionsList,
    suggestions,
    overall_accuracy: acc,
  };
}

/** 获取混淆矩阵单元格背景色：对角线绿色，非对角线红色深浅 */
function getCellStyle(expected, actual, count, maxCount) {
  const isDiagonal = expected === actual;
  if (count === 0) return { background: '#fafafa' };
  if (isDiagonal) {
    const intensity = maxCount > 0 ? 0.3 + (count / maxCount) * 0.6 : 0.6;
    return {
      background: `rgba(82, 196, 26, ${intensity})`,
      color: intensity < 0.5 ? '#333' : '#fff',
    };
  }
  const intensity = maxCount > 0 ? 0.2 + (count / maxCount) * 0.6 : 0.4;
  return {
    background: `rgba(255, 77, 79, ${intensity})`,
    color: intensity < 0.5 ? '#333' : '#fff',
  };
}

export default function AnalysisReport({
  report: reportProp,
  suiteId,
  jobId,
  job: jobProp,
  cases: casesProp,
  historyJobs = [],
}) {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [job, setJob] = useState(jobProp);
  const [cases, setCases] = useState(casesProp);

  useEffect(() => {
    if (reportProp) {
      setReport(reportProp);
      return;
    }
    if (suiteId) {
      setLoading(true);
      api
        .get(`/testing/batch/suites/${suiteId}/report`)
        .then((res) => {
          const r = res.data;
          setReport({
            confusion_matrix: r.analysis_report?.confusion_matrix ?? {},
            attributions:
              r.analysis_report?.attributions ??
              r.analysis_report?.failure_analysis ??
              [],
            suggestions:
              r.analysis_report?.suggestions ??
              r.analysis_report?.optimization_suggestions ??
              [],
            overall_accuracy: r.accuracy ?? 0,
          });
        })
        .catch(() => message.error('加载报告失败'))
        .finally(() => setLoading(false));
      return;
    }
    if (jobId && !jobProp) {
      setLoading(true);
      Promise.all([
        api.get(`/batch-test/jobs/${jobId}`),
        api.get(`/batch-test/jobs/${jobId}/cases`),
      ])
        .then(([jobRes, casesRes]) => {
          setJob(jobRes.data);
          setCases(casesRes.data);
          setReport(computeAnalysis(jobRes.data, casesRes.data));
        })
        .catch(() => message.error('加载数据失败'))
        .finally(() => setLoading(false));
      return;
    }
    if (jobProp && casesProp) {
      setReport(computeAnalysis(jobProp, casesProp));
    }
  }, [reportProp, suiteId, jobId, jobProp, casesProp]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" tip="加载分析报告..." />
      </div>
    );
  }

  if (!report) {
    return (
      <Empty
        description="暂无分析数据，请传入 report、suiteId、jobId 或 job+cases"
        style={{ padding: 48 }}
      />
    );
  }

  const matrix = report.confusion_matrix ?? {};
  const attributions = report.attributions ?? [];
  const suggestionsList = report.suggestions ?? [];

  const expectedIntents = Object.keys(matrix);
  const allActual = new Set();
  expectedIntents.forEach((exp) => {
    Object.keys(matrix[exp] || {}).forEach((a) => allActual.add(a));
  });
  expectedIntents.forEach((e) => allActual.add(e));
  const actualIntents = [...allActual].sort();

  let maxCount = 0;
  expectedIntents.forEach((e) => {
    actualIntents.forEach((a) => {
      const c = matrix[e]?.[a] ?? 0;
      if (c > maxCount) maxCount = c;
    });
  });

  return (
    <div style={{ padding: '0 0 24px 0' }}>
      <Row gutter={[16, 16]}>
        {/* 混淆矩阵 */}
        <Col span={24}>
          <Card
            title={
              <Space>
                <BarChartOutlined />
                混淆矩阵（预期意图 vs 实际意图）
              </Space>
            }
            size="small"
          >
            {expectedIntents.length === 0 ? (
              <Empty description="无混淆矩阵数据" />
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table
                  style={{
                    borderCollapse: 'collapse',
                    fontSize: 12,
                    minWidth: 300,
                  }}
                >
                  <thead>
                    <tr>
                      <th
                        style={{
                          padding: '8px 12px',
                          border: '1px solid #f0f0f0',
                          background: '#fafafa',
                          textAlign: 'center',
                          fontWeight: 600,
                        }}
                      >
                        预期 \ 实际
                      </th>
                      {actualIntents.map((a) => (
                        <th
                          key={a}
                          style={{
                            padding: '8px 12px',
                            border: '1px solid #f0f0f0',
                            background: '#fafafa',
                            textAlign: 'center',
                            maxWidth: 100,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                          title={a}
                        >
                          {a}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {expectedIntents.map((exp) => (
                      <tr key={exp}>
                        <td
                          style={{
                            padding: '8px 12px',
                            border: '1px solid #f0f0f0',
                            background: '#fafafa',
                            fontWeight: 500,
                            maxWidth: 100,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                          title={exp}
                        >
                          {exp}
                        </td>
                        {actualIntents.map((act) => {
                          const count = matrix[exp]?.[act] ?? 0;
                          const style = getCellStyle(exp, act, count, maxCount);
                          return (
                            <td
                              key={act}
                              style={{
                                padding: '8px 12px',
                                border: '1px solid #f0f0f0',
                                textAlign: 'center',
                                ...style,
                              }}
                            >
                              {count || '-'}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              <Tag color="green">绿色：正确分类（对角线）</Tag>
              <Tag color="red">红色：误分类</Tag>
            </div>
          </Card>
        </Col>

        {/* 归因分析 */}
        <Col span={24}>
          <Card
            title={
              <Space>
                <WarningOutlined />
                归因分析
              </Space>
            }
            size="small"
          >
            {attributions.length === 0 ? (
              <Empty description="无失败归因数据" />
            ) : (
              attributions.map((attr) => (
                <div
                  key={attr.category}
                  style={{
                    marginBottom: 16,
                    padding: 12,
                    background: '#fff7e6',
                    borderRadius: 8,
                    border: '1px solid #ffd591',
                  }}
                >
                  <Space>
                    <Tag color="orange">{attr.description}</Tag>
                    <Text type="secondary">
                      {attr.count} 条 ({attr.percentage}%)
                    </Text>
                  </Space>
                  {(attr.examples || []).length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        典型样例：
                      </Text>
                      <ul style={{ margin: '4px 0 0 0', paddingLeft: 20 }}>
                        {(attr.examples || []).slice(0, 3).map((ex, i) => (
                          <li key={i} style={{ fontSize: 12, marginTop: 4 }}>
                            「{ex.input_text}」 → 期望 {ex.expected_intent || '-'}
                            / 实际 {ex.actual_intent ?? '-'}
                            {ex.intent_confidence != null &&
                              ` (置信度: ${(ex.intent_confidence * 100).toFixed(0)}%)`}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))
            )}
          </Card>
        </Col>

        {/* 优化建议 */}
        <Col span={24}>
          <Card
            title={
              <Space>
                <BulbOutlined />
                优化建议
              </Space>
            }
            size="small"
          >
            {suggestionsList.length === 0 ? (
              <Empty description="暂无优化建议" />
            ) : (
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {suggestionsList.map((s, i) => (
                  <li key={i} style={{ marginBottom: 8 }}>
                    <Text>{s}</Text>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </Col>

        {/* 趋势对比 */}
        {historyJobs.length > 0 && (
          <Col span={24}>
            <Card
              title={
                <Space>
                  <BarChartOutlined />
                  准确率趋势
                </Space>
              }
              size="small"
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'flex-end',
                  gap: 8,
                  height: 120,
                  padding: '16px 0',
                }}
              >
                {historyJobs
                  .slice(0, 10)
                  .sort(
                    (a, b) =>
                      new Date(b.created_at) - new Date(a.created_at)
                  )
                  .reverse()
                  .map((h, i) => (
                    <div
                      key={h.id}
                      style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        minWidth: 40,
                      }}
                    >
                      <div
                        style={{
                          width: '100%',
                          maxWidth: 36,
                          height: 80,
                          background: '#e6f7ff',
                          borderRadius: '4px 4px 0 0',
                          position: 'relative',
                        }}
                      >
                        <div
                          style={{
                            position: 'absolute',
                            bottom: 0,
                            left: 0,
                            right: 0,
                            height: `${(h.accuracy ?? 0) * 100}%`,
                            background: '#1890ff',
                            borderRadius: '4px 4px 0 0',
                          }}
                        />
                      </div>
                      <Text
                        type="secondary"
                        style={{
                          fontSize: 10,
                          marginTop: 4,
                          maxWidth: 60,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                        title={dayjs(h.created_at).format('YYYY-MM-DD HH:mm')}
                      >
                        {dayjs(h.created_at).format('MM-DD')}
                      </Text>
                      <Text style={{ fontSize: 10 }}>
                        {((h.accuracy ?? 0) * 100).toFixed(0)}%
                      </Text>
                    </div>
                  ))}
              </div>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
}
