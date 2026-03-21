import { Tag } from 'antd';
import {
  SyncOutlined,
  LoadingOutlined,
} from '@ant-design/icons';

const STATUS_MAP = {
  draft: { color: 'default', label: '草稿' },
  training: { color: 'processing', label: '训练中', icon: <SyncOutlined spin /> },
  failed: { color: 'error', label: '训练失败' },
  trained: { color: 'blue', label: '已训练' },
  evaluating: { color: 'orange', label: '评估中', icon: <LoadingOutlined /> },
  testable: { color: 'cyan', label: '测试态' },
  published: { color: 'green', label: '已发布' },
  archived: { color: 'default', label: '已归档' },
};

export default function ModelStatusTag({ status }) {
  const config = STATUS_MAP[status] || { color: 'default', label: status };
  return (
    <Tag color={config.color} icon={config.icon} style={{ margin: 0 }}>
      {config.label}
    </Tag>
  );
}
