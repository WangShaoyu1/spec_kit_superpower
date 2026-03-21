import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Typography, Card, Table, Button, Space, Alert } from 'antd';
import { DatabaseOutlined, AppstoreOutlined, ArrowRightOutlined } from '@ant-design/icons';
import useIntentLibraryStore from '../../stores/intentLibraryStore';

const { Title, Text, Paragraph } = Typography;

/**
 * PD D031: 数据集侧栏一级入口；后端仍以 library 为命名空间，此处提供跨库导航。
 */
export default function DatasetManagement() {
  const navigate = useNavigate();
  const {
    libraries,
    loading,
    total,
    page,
    pageSize,
    setPage,
    setPageSize,
    fetchLibraries,
  } = useIntentLibraryStore();

  useEffect(() => {
    setPage(1);
    fetchLibraries();
  }, [setPage, fetchLibraries]);

  const columns = useMemo(
    () => [
      {
        title: '指令库',
        key: 'name',
        render: (_, row) => (
          <Space direction="vertical" size={0}>
            <Text strong>{row.name}</Text>
            <Text type="secondary" style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
              {row.library_key}
            </Text>
          </Space>
        ),
      },
      {
        title: '语言',
        dataIndex: 'language',
        width: 100,
        render: (lang) => (lang === 'zh' ? '中文' : lang === 'en' ? 'English' : lang),
      },
      {
        title: '操作',
        key: 'actions',
        width: 160,
        render: (_, row) => (
          <Button
            type="primary"
            size="small"
            icon={<DatabaseOutlined />}
            onClick={() => navigate(`/intent-library/${row.id}/datasets`)}
          >
            管理数据集
          </Button>
        ),
      },
    ],
    [navigate],
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      <div>
        <Title level={4} style={{ marginBottom: 8 }}>
          <DatabaseOutlined style={{ marginRight: 8 }} />
          数据集管理
        </Title>
        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
          训练数据集由指令库引用并用于模型训练。请选择指令库进入该库下的数据集列表与标注。
        </Paragraph>
      </div>

      <Alert
        type="info"
        showIcon
        message="与 PD 的对应关系"
        description={
          <>
            后端 API 仍以 <Text code>/intent-libraries/{'{id}'}/datasets</Text> 组织。侧栏入口位于
            <Text strong> 指令库管理 → 数据集管理 </Text>
            ，与本模块 PD 一致。
          </>
        }
        style={{ marginBottom: 0 }}
      />

      <Card variant="borderless">
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={libraries}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (pag) => {
              const p = pag.current;
              const ps = pag.pageSize;
              if (ps !== pageSize) setPageSize(ps);
              else setPage(p);
              useIntentLibraryStore.getState().fetchLibraries();
            },
          }}
          locale={{
            emptyText: (
              <Space direction="vertical" align="center" style={{ padding: 24 }}>
                <AppstoreOutlined style={{ fontSize: 32, color: 'var(--color-text-tertiary)' }} />
                <Text type="secondary">暂无指令库，请先在「指令库管理」中创建</Text>
                <Button type="link" icon={<ArrowRightOutlined />} onClick={() => navigate('/intent-library')}>
                  前往指令库管理
                </Button>
              </Space>
            ),
          }}
        />
      </Card>
    </div>
  );
}
