import {
  Card, Tag, Progress, Table, Timeline, Statistic, Typography, Empty, Descriptions,
} from 'antd';
import { ClockCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

// 域类型 → Tag 颜色
const DOMAIN_COLORS = {
  command: 'blue',
  knowledge: 'green',
  chitchat: 'orange',
  error: 'red',
};

// 域类型 → 中文
const DOMAIN_LABELS = {
  command: '指令域',
  knowledge: '知识域',
  chitchat: '闲聊域',
  error: '错误',
};

/**
 * 调试面板组件 - 展示 NLU 处理链路的完整调试信息
 * @param {Object} debug_info - 调试信息（可包含顶层字段 + debug_info 嵌套）
 *   - domain, route_confidence, intent, intent_confidence, slots
 *   - latency_ms, debug_info: { routing, intent, slots, dialog_state, knowledge_hits }
 */
export default function DebugPanel({ debug_info }) {
  if (!debug_info) {
    return (
      <Card title="调试面板" size="small">
        <Empty description="暂无调试数据，发送消息后展示" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    );
  }

  const domain = debug_info.domain ?? debug_info.debug_info?.routing?.domain;
  const routeConfidence = debug_info.route_confidence ?? debug_info.debug_info?.routing?.confidence;
  const intent = debug_info.intent ?? debug_info.debug_info?.intent?.intent_key;
  const intentConfidence = debug_info.intent_confidence ?? debug_info.debug_info?.intent?.confidence;
  const slots = debug_info.slots ?? {};
  const latencyMs = debug_info.latency_ms;
  const inner = debug_info.debug_info ?? {};
  const dialogState = inner.dialog_state;
  const knowledgeHits = inner.knowledge_hits ?? [];
  const slotDetails = inner.slots ?? [];

  return (
    <Card title="调试面板" size="small">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* 1. 路由结果 + 置信度 */}
        <div>
          <Text strong>路由结果</Text>
          <div style={{ marginTop: 4 }}>
            <Tag color={DOMAIN_COLORS[domain] ?? 'default'}>
              {DOMAIN_LABELS[domain] ?? domain ?? '-'}
            </Tag>
            {routeConfidence != null && (
              <Text type="secondary"> 置信度: {(routeConfidence * 100).toFixed(1)}%</Text>
            )}
          </div>
        </div>

        {/* 2. 意图分类 + 置信度 (Progress bar) */}
        {(intent || intentConfidence != null) && (
          <div>
            <Text strong>意图分类</Text>
            <div style={{ marginTop: 4 }}>
              {intent && <Tag>{intent}</Tag>}
              {intentConfidence != null && (
                <Progress
                  percent={Math.round(intentConfidence * 100)}
                  size="small"
                  style={{ marginTop: 4, maxWidth: 200 }}
                />
              )}
            </div>
          </div>
        )}

        {/* 3. 槽位提取详情 (Table) */}
        {(Object.keys(slots).length > 0 || slotDetails.length > 0) && (
          <div>
            <Text strong>槽位提取</Text>
            <Table
              size="small"
              pagination={false}
              rowKey={(_, i) => i}
              dataSource={
                slotDetails.length > 0
                  ? slotDetails.map((s, i) => ({ id: i, slot_key: s.key, value: s.value }))
                  : Object.entries(slots).map(([k, v], i) => ({ id: i, slot_key: k, value: String(v) }))
              }
              columns={[
                { title: '槽位名', dataIndex: 'slot_key', key: 'slot_key', width: 120 },
                { title: '提取值', dataIndex: 'value', key: 'value' },
              ]}
              style={{ marginTop: 4 }}
            />
          </div>
        )}

        {/* 4. 对话状态变化 (Timeline) */}
        {(dialogState || debug_info.needs_followup != null) && (
          <div>
            <Text strong>对话状态</Text>
            <Timeline
              size="small"
              style={{ marginTop: 8 }}
              items={[
                dialogState?.state && {
                  color: dialogState.is_complete ? 'green' : 'blue',
                  children: (
                    <div>
                      <Text>状态: {dialogState.state}</Text>
                      {dialogState.is_complete != null && (
                        <Text type="secondary"> (完成: {dialogState.is_complete ? '是' : '否'})</Text>
                      )}
                    </div>
                  ),
                },
                debug_info.needs_followup != null && {
                  color: debug_info.needs_followup ? 'orange' : 'gray',
                  children: (
                    <div>
                      <Text>需要追问: {debug_info.needs_followup ? '是' : '否'}</Text>
                    </div>
                  ),
                },
              ].filter(Boolean)}
            />
          </div>
        )}

        {/* 5. 知识库命中条目 */}
        {knowledgeHits.length > 0 && (
          <div>
            <Text strong>知识库命中</Text>
            <div style={{ marginTop: 4 }}>
              {knowledgeHits.map((hit, i) => (
                <Card key={i} size="small" style={{ marginBottom: 4 }}>
                  {typeof hit === 'string' ? (
                    <Text>{hit}</Text>
                  ) : (
                    <Descriptions size="small" column={1}>
                      {hit.title != null && <Descriptions.Item label="标题">{hit.title}</Descriptions.Item>}
                      {hit.content != null && <Descriptions.Item label="内容">{String(hit.content).slice(0, 200)}...</Descriptions.Item>}
                      {hit.score != null && <Descriptions.Item label="得分">{hit.score}</Descriptions.Item>}
                    </Descriptions>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* 6. 响应耗时 (Statistic) */}
        {latencyMs != null && (
          <div>
            <Statistic
              title="响应耗时"
              value={latencyMs}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
            />
          </div>
        )}
      </div>
    </Card>
  );
}
