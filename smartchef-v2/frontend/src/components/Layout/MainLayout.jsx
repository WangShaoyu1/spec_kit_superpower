import { useState, useMemo, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Button, Dropdown, Avatar, Typography, theme } from 'antd';
import {
  AppstoreOutlined,
  DatabaseOutlined,
  MessageOutlined,
  BookOutlined,
  ExperimentOutlined,
  DashboardOutlined,
  TeamOutlined,
  CommentOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons';
import useAuthStore from '../../stores/authStore';

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

const SIDEBAR_WIDTH = 240;
const SIDEBAR_COLLAPSED = 80;
const HEADER_HEIGHT = 56;

const sidebarStyle = {
  background: '#001529',
  borderRight: 'none',
};

const logoBox = (collapsed) => ({
  height: HEADER_HEIGHT,
  display: 'flex',
  alignItems: 'center',
  justifyContent: collapsed ? 'center' : 'flex-start',
  padding: collapsed ? 0 : '0 20px',
  gap: 10,
  borderBottom: '1px solid rgba(255,255,255,0.08)',
  flexShrink: 0,
});

const MENU_ITEMS = [
  {
    key: 'sub-intent-library',
    icon: <AppstoreOutlined />,
    label: '指令库管理',
    children: [
      { key: '/intent-library', label: '指令库列表' },
      { key: '/dataset-management', label: '数据集管理', icon: <DatabaseOutlined /> },
    ],
  },
  { key: '/dialog-profile', icon: <MessageOutlined />, label: '对话方案' },
  { key: '/knowledge-base', icon: <BookOutlined />, label: '知识库' },
  { key: '/batch-test', icon: <ExperimentOutlined />, label: '批量测试' },
  {
    key: '/monitoring',
    icon: <DashboardOutlined />,
    label: '监控仪表盘',
    children: [
      { key: '/monitoring/overview', label: '概览' },
      { key: '/monitoring/device-logs', label: '设备日志' },
      { key: '/monitoring/alert-rules', label: '告警规则' },
    ],
  },
  { key: '/user-manager', icon: <TeamOutlined />, label: '用户管理' },
  { key: '/test-chat', icon: <CommentOutlined />, label: '手动测试' },
];

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token: themeToken } = theme.useToken();

  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  const loadUser = useAuthStore((s) => s.loadUser);
  const logout = useAuthStore((s) => s.logout);

  useEffect(() => {
    if (token && !user) loadUser();
  }, [token, user, loadUser]);

  const selectedKey = useMemo(() => {
    const path = location.pathname;
    // 数据集枢纽页或 /intent-library/:id/datasets 高亮子项「数据集管理」
    if (path === '/dataset-management' || /\/intent-library\/[^/]+\/datasets(\/|$)/.test(path)) {
      return ['/dataset-management'];
    }
    for (const item of MENU_ITEMS) {
      if (item.children) {
        const child = item.children.find((c) => path === c.key || path.startsWith(c.key + '/'));
        if (child) return [child.key];
      } else if (path === item.key || path.startsWith(item.key + '/')) {
        return [item.key];
      }
    }
    return [];
  }, [location.pathname]);

  const [menuOpenKeys, setMenuOpenKeys] = useState([]);

  useEffect(() => {
    const path = location.pathname;
    const keys = [];
    if (path === '/dataset-management' || path.startsWith('/intent-library')) {
      keys.push('sub-intent-library');
    }
    if (path.startsWith('/monitoring')) {
      keys.push('/monitoring');
    }
    setMenuOpenKeys(keys);
  }, [location.pathname]);

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
      onClick: logout,
    },
  ];

  const contentMargin = collapsed ? SIDEBAR_COLLAPSED : SIDEBAR_WIDTH;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* ── Dark sidebar ── */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(v) => setCollapsed(v)}
        trigger={null}
        width={SIDEBAR_WIDTH}
        collapsedWidth={SIDEBAR_COLLAPSED}
        style={{
          ...sidebarStyle,
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
        }}
      >
        {/* Logo */}
        <div style={logoBox(collapsed)}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: 'linear-gradient(135deg, #1677ff 0%, #69b1ff 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 16,
              fontWeight: 700,
              color: '#fff',
              flexShrink: 0,
              boxShadow: '0 2px 8px rgba(22,119,255,0.35)',
            }}
          >
            SC
          </div>
          {!collapsed && (
            <Text
              strong
              style={{
                fontSize: 15,
                color: '#fff',
                letterSpacing: '-0.01em',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
              }}
            >
              SmartChef
            </Text>
          )}
        </div>

        {/* Navigation */}
        <Menu
          mode="inline"
          selectedKeys={selectedKey}
          openKeys={menuOpenKeys}
          onOpenChange={setMenuOpenKeys}
          items={MENU_ITEMS}
          onClick={({ key }) => {
            if (!key.startsWith('sub-')) navigate(key);
          }}
          style={{
            background: 'transparent',
            border: 'none',
            padding: '12px 0',
            fontWeight: 500,
          }}
          theme="dark"
        />
      </Sider>

      {/* ── Main area ── */}
      <Layout
        style={{
          marginLeft: contentMargin,
          transition: 'margin-left var(--duration-normal) var(--easing)',
        }}
      >
        {/* Header */}
        <Header
          style={{
            height: HEADER_HEIGHT,
            lineHeight: `${HEADER_HEIGHT}px`,
            padding: '0 24px',
            background: themeToken.colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${themeToken.colorBorderSecondary}`,
            boxShadow: 'var(--shadow-sm)',
            position: 'sticky',
            top: 0,
            zIndex: 90,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed((prev) => !prev)}
            style={{ fontSize: 16, width: 40, height: 40 }}
          />

          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" trigger={['click']}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: 'var(--radius-md)',
                transition: 'background var(--duration-fast) var(--easing)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-fill)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <Avatar
                size={30}
                icon={<UserOutlined />}
                style={{
                  background: 'linear-gradient(135deg, #1677ff, #4096ff)',
                  flexShrink: 0,
                }}
              />
              <Text style={{ fontSize: 'var(--font-size-sm)', maxWidth: 120 }} ellipsis>
                {user?.display_name || user?.username || '用户'}
              </Text>
            </div>
          </Dropdown>
        </Header>

        {/* Page content */}
        <Content
          style={{
            margin: 24,
            minHeight: `calc(100vh - ${HEADER_HEIGHT}px - 48px)`,
            minWidth: 0,
          }}
        >
          <div className="fade-in" style={{ minWidth: 0 }}>
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
