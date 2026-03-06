import { useEffect, useState } from 'react';
import { Layout, Menu, Typography, Avatar, Dropdown, Space } from 'antd';
import {
  ThunderboltOutlined,
  BookOutlined,
  MessageOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  DashboardOutlined,
  RocketOutlined,
  TeamOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import IntentManager from '../../pages/IntentManager/index';
import KnowledgeBasePage from '../../pages/KnowledgeBase/index';
import DialogProfilePage from '../../pages/DialogProfile/index';
import TestChatPage from '../../pages/TestChat/index';
import VersionsPage from '../../pages/Versions/index';
import BatchTestPage from '../../pages/BatchTest/index';
import MonitoringPage from '../../pages/Monitoring/index';
import UserManagementPage from '../../pages/UserManagement/index';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MENU_ITEMS = [
  { key: '/intents', icon: <ThunderboltOutlined />, label: '指令配置', permission: 'intent_management.read' },
  { key: '/knowledge', icon: <BookOutlined />, label: '知识库', permission: 'knowledge_management.read' },
  { key: '/profiles', icon: <MessageOutlined />, label: '对话方案', permission: 'dialog_profile.read' },
  { key: '/test', icon: <ExperimentOutlined />, label: '手动测试', permission: 'testing.manual' },
  { key: '/batch-test', icon: <FileSearchOutlined />, label: '批量测试', permission: 'testing.batch' },
  { key: '/monitoring', icon: <DashboardOutlined />, label: '监控仪表盘', permission: 'monitoring.dashboard' },
  { key: '/versions', icon: <RocketOutlined />, label: '版本管理', permission: 'version_publish' },
  { key: '/users', icon: <TeamOutlined />, label: '用户管理', permission: 'user_management' },
];

function hasPermission(permissions, key) {
  if (!permissions) return false;
  const parts = key.split('.');
  let value = permissions;
  for (const p of parts) {
    if (typeof value === 'object' && value !== null) value = value[p];
    else return !!value;
  }
  return !!value;
}

function Placeholder({ title }) {
  return (
    <div style={{ padding: 24 }}>
      <Typography.Title level={4}>{title}</Typography.Title>
      <Text type="secondary">功能开发中...</Text>
    </div>
  );
}

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, fetchMe, logout } = useAuthStore();

  useEffect(() => {
    if (!user) fetchMe();
  }, [user, fetchMe]);

  const permissions = user?.permissions || {};

  const visibleMenuItems = MENU_ITEMS.filter((item) => hasPermission(permissions, item.permission));

  const userMenu = {
    items: [
      { key: 'info', label: user?.display_name || '', disabled: true },
      { type: 'divider' },
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
    ],
    onClick: ({ key }) => {
      if (key === 'logout') logout();
    },
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="dark">
        <div
          style={{
            height: 48,
            margin: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Text strong style={{ color: '#fff', fontSize: collapsed ? 16 : 18 }}>
            {collapsed ? '🍳' : '🍳 SmartChef'}
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={visibleMenuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          }}
        >
          <Dropdown menu={userMenu} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <Text>{user?.display_name}</Text>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 8, minHeight: 280 }}>
          <Routes>
            <Route path="/" element={<Placeholder title="欢迎使用 SmartChef 智能对话管理平台" />} />
            <Route path="/intents" element={<IntentManager />} />
            <Route path="/knowledge" element={<KnowledgeBasePage />} />
            <Route path="/profiles" element={<DialogProfilePage />} />
            <Route path="/test" element={<TestChatPage />} />
            <Route path="/batch-test" element={<BatchTestPage />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
            <Route path="/versions" element={<VersionsPage />} />
            <Route path="/users" element={<UserManagementPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}
