import { Menu, Typography } from 'antd';
import {
  ThunderboltOutlined,
  BookOutlined,
  MessageOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  DashboardOutlined,
  RocketOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

const { Text } = Typography;

// 菜单项定义，每项绑定对应的权限 key
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

/**
 * 根据 permissions 对象检查是否拥有指定权限。
 * 支持嵌套路径 (如 "intent_management.read") 和顶层布尔值 (如 "user_management")。
 */
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

export default function Sidebar({ collapsed }) {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);

  const permissions = user?.permissions || {};
  const visibleMenuItems = MENU_ITEMS.filter((item) => hasPermission(permissions, item.permission));

  return (
    <>
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
    </>
  );
}

export { hasPermission, MENU_ITEMS };
