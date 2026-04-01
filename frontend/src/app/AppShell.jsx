import {
  AppstoreOutlined,
  BarChartOutlined,
  BookOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  RobotOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Button, Card, Drawer, Layout, Menu, Tag, Typography } from 'antd'
import { useMemo, useState } from 'react'
import { Link, Navigate, Outlet, useLocation } from 'react-router-dom'

const { Content, Sider } = Layout
const { Paragraph, Title } = Typography
const DEFAULT_CAPABILITIES = ['user_manage', 'intent_library_read', 'knowledge_write', 'profile_read', 'test_execute', 'monitoring_read']

function buildModuleItems(capabilities) {
  const capabilitySet = new Set(capabilities)

  return [
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
  { key: 'user-mgmt', title: '用户管理', tagClass: 'module-tag module-tag--a', state: '验收可用', summary: '账号、角色、权限矩阵与重置密码。' },
  { key: 'intent-library', title: '指令库管理', tagClass: 'module-tag module-tag--b', state: '验收可用', summary: '指令库列表、训练、评测与发布。' },
  { key: 'knowledge-base', title: '知识库管理', tagClass: 'module-tag module-tag--c', state: '验收可用', summary: '分类、文档上传、过滤与回读。' },
  { key: 'dialog-profiles', title: '对话方案', tagClass: 'module-tag module-tag--d', state: '验收可用', summary: '方案编辑、发布与手动测试。' },
  { key: 'batch-tests', title: '批量测试', tagClass: 'module-tag module-tag--e', state: '验收可用', summary: '生成样例、执行测试与查看报告。' },
  { key: 'monitoring', title: '监控中心', tagClass: 'module-tag module-tag--f', state: '验收可用', summary: '运行指标、设备日志与告警规则。' },
]

function OverviewPanel() {
  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div className="hero-eyebrow">Platform Overview</div>
        <Title level={2} className="hero-title" style={{ fontFamily: 'var(--font-display)' }}>
          平台概览
        </Title>
        <Paragraph className="hero-paragraph">
          当前后台已接入用户管理、指令库、知识库、对话方案、批量测试和监控中心六个业务模块，可直接进入对应页面完成验收与回归。
        </Paragraph>
        <div className="metric-row">
          <div className="metric-card">
            <div className="metric-label">已接入模块</div>
            <div className="metric-value">6</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">当前数据库</div>
            <div className="metric-value">PostgreSQL</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">当前重点</div>
            <div className="metric-value">手动验收</div>
          </div>
        </div>
      </section>

      <div className="module-grid">
        {MODULE_CARDS.map((card) => (
          <Card key={card.key} className="module-card" variant="borderless">
            <Title level={4} style={{ fontFamily: 'var(--font-display)', color: 'var(--ink)', marginTop: 0, fontWeight: 600 }}>
              {card.title}
            </Title>
            <Paragraph style={{ color: 'var(--ink-muted)' }}>
              {card.summary}
            </Paragraph>
            <Tag className={card.tagClass}>{card.state}</Tag>
          </Card>
        ))}
      </div>
    </div>
  )
}

export function AppShell({ capabilities = DEFAULT_CAPABILITIES, onLogout = () => {} }) {
  const location = useLocation()
  const [overviewOpen, setOverviewOpen] = useState(false)
  const moduleItems = useMemo(() => buildModuleItems(capabilities), [capabilities])
  const firstAvailablePath = useMemo(() => {
    return moduleItems.find((item) => !item.disabled)?.key ?? '/user-mgmt'
  }, [moduleItems])
  const selectedKeys = useMemo(() => {
    if (location.pathname === '/user-mgmt') {
      return ['/user-mgmt']
    }
    if (location.pathname.startsWith('/intent-library')) {
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
    return [firstAvailablePath]
  }, [firstAvailablePath, location.pathname])

  if (location.pathname === '/') {
    return <Navigate to={firstAvailablePath} replace />
  }

  return (
    <Layout className="shell-layout">
      <Sider width={276} className="shell-sider">
        <div className="brand-block">
          <div className="brand-title">SmartChef</div>
          <div className="brand-copy">管理后台</div>
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
          <div className="shell-toolbar">
            <div className="status-chip">当前阶段: 手动验收</div>
            <div className="shell-actions">
              <Button
                aria-label="平台概览"
                icon={<AppstoreOutlined />}
                size="large"
                onClick={() => setOverviewOpen(true)}
              >
                平台概览
              </Button>
              <Button type="default" size="large" onClick={onLogout}>
                退出登录
              </Button>
            </div>
          </div>
          <Outlet />
          <Drawer
            title="平台概览"
            width={1200}
            open={overviewOpen}
            onClose={() => setOverviewOpen(false)}
            className="overview-drawer"
          >
            <OverviewPanel />
          </Drawer>
        </Content>
      </Layout>
    </Layout>
  )
}
