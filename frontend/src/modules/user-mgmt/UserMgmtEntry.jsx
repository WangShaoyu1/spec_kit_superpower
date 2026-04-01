import { Alert, Card, Col, Descriptions, List, Row, Tag } from 'antd'

const roleRows = [
  { key: 'admin', role: '系统管理员', scope: '全量访问', note: '账号创建、角色调整、权限矩阵维护' },
  { key: 'pm', role: '产品经理', scope: '业务维护', note: '不能维护用户与角色' },
  { key: 'tester', role: '测试人员', scope: '验证执行', note: '以只读与执行测试为主' },
]

export function UserMgmtEntry() {
  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <Descriptions
          title="用户管理正式模块入口"
          column={1}
          styles={{
            label: { color: 'rgba(208, 219, 232, 0.68)', width: 120 },
            content: { color: '#f8fbff' },
          }}
        >
          <Descriptions.Item label="当前阶段">
            <Tag color="gold">正式骨架已建立</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="下一动作">
            重新生成 `pd-user-mgmt` 的 AD / DD / plan / tasks，并通过阶段 gate 后进入正式实现。
          </Descriptions.Item>
          <Descriptions.Item label="约束">
            菜单壳、公共布局、模块入口已就位；业务实现将在下一阶段替换为正式功能。
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Row gutter={18}>
        <Col span={14}>
          <Card className="module-card" title="角色矩阵基线" variant="borderless">
            <List
              dataSource={roleRows}
              renderItem={(item) => (
                <List.Item key={item.key}>
                  <List.Item.Meta
                    title={item.role}
                    description={`${item.scope} · ${item.note}`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col span={10}>
          <Card className="module-card" title="研发入口提示" variant="borderless">
            <Alert
              type="info"
              showIcon
              message="正式 `user-mgmt` 功能尚未接入"
              description="当前页面只承担正式项目壳入口与权限边界提示，避免继续使用试点代码。"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
