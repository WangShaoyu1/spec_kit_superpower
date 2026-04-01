import {
  BarChartOutlined,
  BookOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  RobotOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Button, Card, Layout, Menu, Tag, Typography } from 'antd'
import { useMemo } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'

const { Content, Sider } = Layout
const { Paragraph, Title } = Typography
const DEFAULT_CAPABILITIES = ['user_manage', 'intent_library_read', 'knowledge_write', 'profile_read', 'test_execute', 'monitoring_read']

function buildModuleItems(capabilities) {
  const capabilitySet = new Set(capabilities)

  return [
    {
      key: '/',
      icon: <DatabaseOutlined />,
      label: <Link to="/">总览驾驶舱</Link>,
    },
    {
      key: '/user-mgmt',
      icon: <UserOutlined />,
      label: <Link to="/user-mgmt">用户管理</Link>,
      disabled: !capabilitySet.has('user_manage'),
    },
    {
      key: '/intent-library',
      icon: <DatabaseOutlined />,
      label: <Link to="/intent-library">指令库管理</Link>,
      disabled: !capabilitySet.has('intent_library_read'),
    },
    {
      key: '/knowledge-base',
      icon: <BookOutlined />,
      label: <Link to="/knowledge-base">知识库管理</Link>,
      disabled: !capabilitySet.has('knowledge_write'),
    },
    {
      key: '/dialog-profiles',
      icon: <RobotOutlined />,
      label: <Link to="/dialog-profiles">对话方案</Link>,
      disabled: !capabilitySet.has('profile_read'),
    },
    {
      key: '/batch-tests',
      icon: <ExperimentOutlined />,
      label: <Link to="/batch-tests">批量测试</Link>,
      disabled: !capabilitySet.has('test_execute'),
    },
    {
      key: '/monitoring',
      icon: <BarChartOutlined />,
      label: <Link to="/monitoring">监控仪表盘</Link>,
      disabled: !capabilitySet.has('monitoring_read'),
    },
  ]
}

const MODULE_CARDS = [
  { key: 'pd-user-mgmt', title: '用户管理', tone: 'gold', state: '已完成 browser 验证' },
  { key: 'pd-intent-library', title: '指令库管理', tone: 'blue', state: '已完成 browser 验证' },
  { key: 'pd-knowledge-base', title: '知识库管理', tone: 'cyan', state: '已完成 browser 验证' },
  { key: 'pd-dialog-profile', title: '对话方案', tone: 'purple', state: '已完成 browser 验证' },
  { key: 'pd-batch-test', title: '批量测试', tone: 'volcano', state: '已完成 browser 验证' },
  { key: 'pd-monitoring', title: '监控仪表盘', tone: 'geekblue', state: '已完成 browser 验证' },
]

function DashboardPage() {
  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div className="hero-grid">
          <div>
            <div className="hero-eyebrow">Formal Rollout</div>
            <Title level={1} className="hero-title">
              SmartChef 正式研发主控台
            </Title>
            <Paragraph className="hero-paragraph">
              当前仓库已切离试点入口，正式 `backend/` 与 `frontend/` 将承接后续模块化研发。
              先完成 `pd-user-mgmt` 的文档再生与实现，再按 harness 顺序推进其他模块。
            </Paragraph>
            <div className="metric-row">
              <div className="metric-card">
                <div className="metric-label">当前阶段</div>
                <div className="metric-value">Browser Verified</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">最近完成模块</div>
                <div className="metric-value">Monitoring</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">运行约束</div>
                <div className="metric-value">Local PG</div>
              </div>
            </div>
          </div>
          <aside className="spotlight-card">
            <div className="hero-eyebrow">Harness Discipline</div>
            <Title level={3} style={{ color: '#fff', marginTop: 12 }}>
              模块先后顺序与浏览器验证已被固定
            </Title>
            <Paragraph style={{ color: 'rgba(248, 251, 255, 0.78)' }}>
              现在的壳层只暴露正式入口，不再回退到试点路径；后续每个模块都将按
              <code style={{ margin: '0 6px', color: '#ffd48b' }}>
                ad -&gt; dd -&gt; tasks -&gt; implement -&gt; browser
              </code>
              顺序推进。
            </Paragraph>
          </aside>
        </div>
      </section>

      <div className="module-grid">
        {MODULE_CARDS.map((card) => (
          <Card key={card.key} className="module-card" variant="borderless">
            <Title level={4} style={{ color: '#f8fbff', marginTop: 0 }}>
              {card.title}
            </Title>
            <Paragraph style={{ color: 'rgba(214, 224, 236, 0.76)' }}>
              {card.key}
            </Paragraph>
            <Tag color={card.tone}>{card.state}</Tag>
          </Card>
        ))}
      </div>
    </div>
  )
}

export function AppShell({ capabilities = DEFAULT_CAPABILITIES }) {
  const location = useLocation()
  const moduleItems = useMemo(() => buildModuleItems(capabilities), [capabilities])
  const selectedKeys = useMemo(() => {
    if (location.pathname === '/user-mgmt') {
      return ['/user-mgmt']
    }
    if (location.pathname === '/intent-library') {
      return ['/intent-library']
    }
    if (location.pathname.startsWith('/knowledge-base')) {
      return ['/knowledge-base']
    }
    if (location.pathname.startsWith('/dialog-profiles')) {
      return ['/dialog-profiles']
    }
    if (location.pathname.startsWith('/batch-tests')) {
      return ['/batch-tests']
    }
    if (location.pathname.startsWith('/monitoring')) {
      return ['/monitoring']
    }
    return ['/']
  }, [location.pathname])

  return (
    <Layout className="shell-layout">
      <Sider width={276} className="shell-sider">
        <div className="brand-block">
          <div className="brand-kicker">Spec Harness Console</div>
          <div className="brand-title">SmartChef</div>
          <div className="brand-copy">
            正式前端壳。试点入口已经退出，后续模块按 harness 顺序逐个接入。
          </div>
        </div>
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          items={moduleItems}
          className="shell-menu"
        />
      </Sider>
      <Layout>
        <Content className="shell-content">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 18 }}>
            <div className="status-chip">正式骨架已建立</div>
            <Button type="default" size="large">
              Local PG via temp_data/manage_services.py
            </Button>
          </div>
          {location.pathname === '/' ? <DashboardPage /> : <Outlet />}
        </Content>
      </Layout>
    </Layout>
  )
}
