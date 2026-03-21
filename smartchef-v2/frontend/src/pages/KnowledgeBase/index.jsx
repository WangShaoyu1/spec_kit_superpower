import { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Button,
  Input,
  Select,
  Table,
  Tag,
  Card,
  Row,
  Col,
  Tree,
  Space,
  Modal,
  Form,
  Upload,
  List,
  message,
  Empty,
  Tooltip,
  Dropdown,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  UploadOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  InboxOutlined,
  ReloadOutlined,
  UndoOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useKnowledgeStore from '../../stores/knowledgeStore';
import DangerConfirmModal from '../../components/DangerConfirmModal';
import { getDocumentFieldStats, ratioColor, readUploadPreview } from './fieldInference';

const { Title, Text } = Typography;
const { Dragger } = Upload;

const STATUS_MAP = {
  uploading: { color: 'blue', label: '上传中' },
  parsing: { color: 'orange', label: '解析中' },
  indexing: { color: 'cyan', label: '索引中' },
  ready: { color: 'green', label: '就绪' },
  error: { color: 'red', label: '错误' },
};

const FILE_TYPE_ICON = {
  pdf: <FilePdfOutlined style={{ color: '#ff4d4f' }} />,
  txt: <FileTextOutlined style={{ color: '#8c8c8c' }} />,
  docx: <FileWordOutlined style={{ color: '#1677ff' }} />,
  xlsx: <FileExcelOutlined style={{ color: '#52c41a' }} />,
};

const STAT_CARDS = [
  {
    key: 'categories',
    label: '分类总数',
    icon: <FolderOutlined />,
    gradient: 'linear-gradient(135deg, #1677ff 0%, #69b1ff 100%)',
    getValue: ({ categoriesCount }) => categoriesCount,
  },
  {
    key: 'documents',
    label: '文档总数',
    icon: <FileTextOutlined />,
    gradient: 'linear-gradient(135deg, #52c41a 0%, #95de64 100%)',
    getValue: ({ documentsTotal }) => documentsTotal,
  },
  {
    key: 'indexed',
    label: '已索引',
    icon: <CheckCircleOutlined />,
    gradient: 'linear-gradient(135deg, #13c2c2 0%, #5cdbd3 100%)',
    getValue: ({ indexedCount }) => indexedCount,
  },
  {
    key: 'indexing',
    label: '索引中',
    icon: <SyncOutlined />,
    gradient: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
    getValue: ({ indexingCount }) => indexingCount,
  },
];

function buildTreeData(categories, selectedKey) {
  return categories.map((cat) => ({
    key: cat.id,
    title: (
      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{cat.name}</span>
        {cat.document_count > 0 && (
          <Tag style={{ marginRight: 0, fontSize: 'var(--font-size-xs)' }}>{cat.document_count}</Tag>
        )}
      </span>
    ),
    icon: ({ expanded }) => expanded ? <FolderOpenOutlined /> : <FolderOutlined />,
    children: cat.children?.length ? buildTreeData(cat.children, selectedKey) : undefined,
    rawData: cat,
  }));
}

export default function KnowledgeBase() {
  const navigate = useNavigate();

  const {
    categories,
    categoriesLoading,
    documents,
    documentsLoading,
    total,
    page,
    pageSize,
    search,
    categoryFilter,
    statusFilter,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
    reindexDocument,
    setSearch,
    setCategoryFilter,
    setStatusFilter,
    setPage,
    setPageSize,
    searchResults,
    searchLoading,
    searchKnowledge,
    clearSearch,
  } = useKnowledgeStore();

  const [catModalOpen, setCatModalOpen] = useState(false);
  const [editingCat, setEditingCat] = useState(null);
  const [catForm] = Form.useForm();
  const [catSubmitting, setCatSubmitting] = useState(false);

  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadForm] = Form.useForm();
  const [uploading, setUploading] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [fieldPreview, setFieldPreview] = useState(null);
  const [reindexingId, setReindexingId] = useState(null);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteType, setDeleteType] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [formatFilter, setFormatFilter] = useState('');
  const [searchTestOpen, setSearchTestOpen] = useState(false);
  const [searchTestQuery, setSearchTestQuery] = useState('');

  const statData = useMemo(() => ({
    categoriesCount: categories.length,
    documentsTotal: total,
    indexedCount: documents.filter((d) => d.status === 'indexed' || d.status === 'ready').length,
    indexingCount: documents.filter((d) => d.status === 'indexing').length,
  }), [categories, total, documents]);

  const filteredDocuments = useMemo(() => {
    if (!formatFilter) return documents;
    return documents.filter((d) => (d.file_type || d.doc_type || '').toLowerCase() === formatFilter);
  }, [documents, formatFilter]);

  const handleResetFilters = useCallback(() => {
    setSearch('');
    setCategoryFilter(null);
    setStatusFilter('');
    setFormatFilter('');
    setPage(1);
  }, [setSearch, setCategoryFilter, setStatusFilter, setPage]);

  const handleSearchTest = useCallback(async () => {
    if (!searchTestQuery.trim()) {
      message.warning('请输入检索内容');
      return;
    }
    await searchKnowledge(searchTestQuery.trim());
  }, [searchTestQuery, searchKnowledge]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments, page, pageSize, search, categoryFilter, statusFilter]);

  const treeData = useMemo(() => buildTreeData(categories, categoryFilter), [categories, categoryFilter]);

  const onSelectCategory = useCallback(
    (keys) => {
      setCategoryFilter(keys.length ? keys[0] : null);
    },
    [setCategoryFilter],
  );

  const openCreateCategory = useCallback(
    (parentId = null) => {
      setEditingCat(null);
      catForm.resetFields();
      catForm.setFieldsValue({ parent_id: parentId });
      setCatModalOpen(true);
    },
    [catForm],
  );

  const openEditCategory = useCallback(
    (cat) => {
      setEditingCat(cat);
      catForm.setFieldsValue({ name: cat.name, description: cat.description });
      setCatModalOpen(true);
    },
    [catForm],
  );

  const handleCatSubmit = useCallback(async () => {
    try {
      const values = await catForm.validateFields();
      setCatSubmitting(true);
      if (editingCat) {
        await updateCategory(editingCat.id, values);
        message.success('更新成功');
      } else {
        await createCategory(values);
        message.success('创建成功');
      }
      setCatModalOpen(false);
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    } finally {
      setCatSubmitting(false);
    }
  }, [catForm, editingCat, createCategory, updateCategory]);

  const handleUpload = useCallback(async () => {
    try {
      const values = await uploadForm.validateFields();
      if (!fileList.length) {
        message.warning('请选择文件');
        return;
      }
      setUploading(true);
      const formData = new FormData();
      formData.append('title', values.title);
      if (categoryFilter) formData.append('category_id', categoryFilter);
      formData.append('file', fileList[0].originFileObj || fileList[0]);
      await uploadDocument(formData);
      message.success('上传成功');
      setUploadModalOpen(false);
      setFileList([]);
      setFieldPreview(null);
      uploadForm.resetFields();
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '上传失败');
    } finally {
      setUploading(false);
    }
  }, [uploadForm, fileList, categoryFilter, uploadDocument]);

  const handleReindexRow = useCallback(
    async (recordId) => {
      setReindexingId(recordId);
      try {
        await reindexDocument(recordId);
        message.success('重新索引已完成');
      } catch (err) {
        message.error(err?.message || '重新索引失败');
      } finally {
        setReindexingId(null);
      }
    },
    [reindexDocument],
  );

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      if (deleteType === 'category') {
        await deleteCategory(deleteTarget.id);
      } else {
        await deleteDocument(deleteTarget.id);
      }
      message.success('删除成功');
      setDeleteTarget(null);
    } catch (err) {
      message.error(err?.message || '删除失败');
    } finally {
      setDeleteLoading(false);
    }
  }, [deleteTarget, deleteType, deleteCategory, deleteDocument]);

  const catContextMenu = useCallback(
    (node) => ({
      items: [
        { key: 'add-child', icon: <PlusOutlined />, label: '添加子分类', onClick: () => openCreateCategory(node.key) },
        { key: 'edit', icon: <EditOutlined />, label: '编辑', onClick: () => openEditCategory(node.rawData) },
        {
          key: 'delete',
          icon: <DeleteOutlined />,
          label: '删除',
          danger: true,
          onClick: () => { setDeleteTarget(node.rawData); setDeleteType('category'); },
        },
      ],
    }),
    [openCreateCategory, openEditCategory],
  );

  const columns = useMemo(
    () => [
      {
        title: '文档名称',
        dataIndex: 'title',
        key: 'title',
        ellipsis: true,
        render: (text, record) => (
          <Space>
            {FILE_TYPE_ICON[record.file_type] || <FileTextOutlined />}
            <Button
              type="link"
              style={{ padding: 0, fontWeight: 500 }}
              onClick={() => navigate(`/knowledge-base/${record.id}`)}
            >
              {text}
            </Button>
          </Space>
        ),
      },
      {
        title: '分类',
        dataIndex: 'category_name',
        key: 'category_name',
        width: 140,
        render: (name) => name || <Text type="secondary">未分类</Text>,
      },
      {
        title: '类型',
        dataIndex: 'file_type',
        key: 'file_type',
        width: 80,
        align: 'center',
        render: (t) => <Tag>{t?.toUpperCase()}</Tag>,
      },
      {
        title: '大小',
        dataIndex: 'file_size',
        key: 'file_size',
        width: 100,
        align: 'right',
        render: (size) => {
          if (!size) return '-';
          if (size < 1024) return `${size} B`;
          if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
          return `${(size / 1024 / 1024).toFixed(1)} MB`;
        },
      },
      {
        title: '分片',
        dataIndex: 'chunk_count',
        key: 'chunk_count',
        width: 80,
        align: 'center',
        render: (c) => <Text style={{ fontFamily: 'var(--font-mono)' }}>{c}</Text>,
      },
      {
        title: '有效/总字段',
        key: 'field_ratio',
        width: 110,
        align: 'center',
        render: (_, record) => {
          const stats = getDocumentFieldStats(record);
          if (!stats) {
            return (
              <Tooltip title="服务端返回 valid_field_count / total_field_count 后将显示比例">
                <Text type="secondary">—</Text>
              </Tooltip>
            );
          }
          const { valid, total, ratio } = stats;
          return (
            <Text
              style={{
                fontFamily: 'var(--font-mono)',
                color: ratioColor(ratio),
                fontSize: 'var(--font-size-sm)',
              }}
            >
              {valid}/{total}
            </Text>
          );
        },
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        render: (s) => {
          const info = STATUS_MAP[s] || { color: 'default', label: s };
          return <Tag color={info.color}>{info.label}</Tag>;
        },
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 160,
        render: (val) => (
          <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
            {val ? dayjs(val).format('YYYY-MM-DD HH:mm') : '-'}
          </Text>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        width: 196,
        render: (_, record) => (
          <Space size={4}>
            <Tooltip title="详情">
              <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => navigate(`/knowledge-base/${record.id}`)} />
            </Tooltip>
            <Tooltip title="重新索引">
              <Button
                type="link"
                size="small"
                icon={<ReloadOutlined />}
                loading={reindexingId === record.id}
                disabled={record.status === 'uploading' || record.status === 'parsing'}
                onClick={() => handleReindexRow(record.id)}
              />
            </Tooltip>
            <Tooltip title="删除">
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => { setDeleteTarget(record); setDeleteType('document'); }}
              />
            </Tooltip>
          </Space>
        ),
      },
    ],
    [navigate, reindexingId, handleReindexRow],
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>知识库</Title>
          <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
            管理知识文档，支持分类、上传、分片和语义检索
          </Text>
        </div>
        <Space>
          <Button icon={<SearchOutlined />} onClick={() => { setSearchTestOpen(true); clearSearch(); setSearchTestQuery(''); }}>
            检索测试
          </Button>
          <Button icon={<PlusOutlined />} onClick={() => openCreateCategory()}>新建分类</Button>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => {
              setFileList([]);
              setFieldPreview(null);
              uploadForm.resetFields();
              setUploadModalOpen(true);
            }}
          >
            上传文档
          </Button>
        </Space>
      </div>

      {/* Stat cards */}
      <Row gutter={16}>
        {STAT_CARDS.map((card) => (
          <Col span={6} key={card.key}>
            <Card
              style={{
                borderRadius: 'var(--radius-lg)',
                border: 'none',
                overflow: 'hidden',
                minWidth: 180,
              }}
              styles={{ body: { padding: '20px 24px' } }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 'var(--radius-lg)',
                    background: card.gradient,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 22,
                    color: '#fff',
                    flexShrink: 0,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  }}
                >
                  {card.icon}
                </div>
                <div>
                  <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)', display: 'block' }}>
                    {card.label}
                  </Text>
                  <Text
                    strong
                    style={{
                      fontSize: 'var(--font-size-2xl)',
                      fontFamily: 'var(--font-mono)',
                      lineHeight: 1.2,
                    }}
                  >
                    {card.getValue(statData)}
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Main content: sidebar + table */}
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        {/* Left: Category tree */}
        <Card
          title="文档分类"
          size="small"
          style={{ width: 320, flexShrink: 0, borderRadius: 'var(--radius-lg)' }}
          styles={{ body: { padding: '8px 0' } }}
        >
          {categoriesLoading ? (
            <div style={{ textAlign: 'center', padding: 32 }}><Spin /></div>
          ) : treeData.length > 0 ? (
            <Tree
              showIcon
              blockNode
              selectedKeys={categoryFilter ? [categoryFilter] : []}
              onSelect={onSelectCategory}
              treeData={treeData}
              titleRender={(node) => (
                <Dropdown menu={catContextMenu(node)} trigger={['contextMenu']}>
                  <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    {node.title}
                  </div>
                </Dropdown>
              )}
              style={{ padding: '0 8px' }}
            />
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无分类" style={{ padding: '24px 0' }}>
              <Button size="small" type="dashed" icon={<PlusOutlined />} onClick={() => openCreateCategory()}>
                创建分类
              </Button>
            </Empty>
          )}
          {categoryFilter && (
            <div style={{ padding: '8px 16px', borderTop: '1px solid var(--color-border-light)' }}>
              <Button type="link" size="small" onClick={() => setCategoryFilter(null)} style={{ padding: 0 }}>
                清除筛选
              </Button>
            </div>
          )}
        </Card>

        {/* Right: Document table */}
        <Card style={{ flex: 1, minWidth: 0, borderRadius: 'var(--radius-lg)' }} styles={{ body: { padding: 0 } }}>
          <div
            style={{
              padding: '16px 24px',
              display: 'flex',
              gap: 12,
              borderBottom: '1px solid var(--color-border-light)',
            }}
          >
            <Input
              placeholder="搜索文档名称..."
              prefix={<SearchOutlined style={{ color: 'var(--color-text-tertiary)' }} />}
              allowClear
              style={{ width: 280 }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 120 }}
              options={[
                { value: '', label: '全部状态' },
                { value: 'ready', label: '就绪' },
                { value: 'uploading', label: '上传中' },
                { value: 'parsing', label: '解析中' },
                { value: 'indexing', label: '索引中' },
                { value: 'error', label: '错误' },
              ]}
            />
            <Select
              value={formatFilter}
              onChange={setFormatFilter}
              style={{ width: 120 }}
              options={[
                { value: '', label: '全部类型' },
                { value: 'json', label: 'JSON' },
                { value: 'md', label: 'Markdown' },
                { value: 'txt', label: 'TXT' },
                { value: 'pdf', label: 'PDF' },
                { value: 'docx', label: 'DOCX' },
              ]}
            />
            <Button icon={<UndoOutlined />} onClick={handleResetFilters}>
              重置
            </Button>
          </div>

          <div style={{ minWidth: 0, overflow: 'hidden' }}>
            <Table
              rowKey="id"
              columns={columns}
              dataSource={filteredDocuments}
              loading={documentsLoading}
              tableLayout="fixed"
              scroll={{ x: true }}
              pagination={{
              current: page,
              pageSize,
              total,
              showSizeChanger: true,
              showTotal: (t) => `共 ${t} 条`,
              onChange: (p, ps) => { setPage(p); if (ps !== pageSize) setPageSize(ps); },
              style: { padding: '0 24px 16px' },
            }}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="暂无文档"
                  style={{ padding: '48px 0' }}
                >
                  <Button
                    type="primary"
                    icon={<UploadOutlined />}
                    onClick={() => {
                      setFileList([]);
                      setFieldPreview(null);
                      uploadForm.resetFields();
                      setUploadModalOpen(true);
                    }}
                  >
                    上传第一个文档
                  </Button>
                </Empty>
              ),
            }}
          />
          </div>
        </Card>
      </div>

      {/* Category create/edit modal */}
      <Modal
        open={catModalOpen}
        title={editingCat ? '编辑分类' : '新建分类'}
        onCancel={() => setCatModalOpen(false)}
        onOk={handleCatSubmit}
        confirmLoading={catSubmitting}
        okText={editingCat ? '保存' : '创建'}
        cancelText="取消"
        width={460}
        centered
        destroyOnHidden
      >
        <Form form={catForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="分类名称" rules={[{ required: true, message: '请输入分类名称' }]}>
            <Input placeholder="例如: 产品手册" maxLength={100} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="分类描述..." maxLength={500} />
          </Form.Item>
          <Form.Item name="parent_id" hidden>
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      {/* Upload modal */}
      <Modal
        open={uploadModalOpen}
        title="上传文档"
        onCancel={() => {
          setUploadModalOpen(false);
          setFieldPreview(null);
        }}
        onOk={handleUpload}
        confirmLoading={uploading}
        okText="上传"
        cancelText="取消"
        width={520}
        centered
        destroyOnHidden
      >
        <Form form={uploadForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="title" label="文档标题" rules={[{ required: true, message: '请输入文档标题' }]}>
            <Input placeholder="例如: 智能烹饪用户手册" maxLength={200} />
          </Form.Item>
          <Form.Item label="选择文件" required>
            <Dragger
              maxCount={1}
              accept=".pdf,.txt,.docx,.xlsx,.json"
              fileList={fileList}
              beforeUpload={() => false}
              onChange={async ({ fileList: fl }) => {
                const next = fl.slice(-1);
                setFileList(next);
                const last = next[0];
                if (!last) {
                  setFieldPreview(null);
                  return;
                }
                if (!uploadForm.getFieldValue('title')) {
                  const name = last?.name?.replace(/\.[^.]+$/, '') || '';
                  uploadForm.setFieldsValue({ title: name });
                }
                const preview = await readUploadPreview(last);
                setFieldPreview(preview);
              }}
            >
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">点击或拖拽文件到此区域</p>
              <p className="ant-upload-hint">支持 PDF、TXT、DOCX、XLSX、JSON（菜谱结构化）格式</p>
            </Dragger>
          </Form.Item>
          {fieldPreview && (
            <div
              style={{
                marginTop: 8,
                padding: 12,
                borderRadius: 12,
                background: 'var(--color-fill, #fafafa)',
                border: '1px solid var(--color-border-light, #f0f0f0)',
              }}
            >
              {fieldPreview.hint && (
                <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)', display: 'block' }}>
                  {fieldPreview.hint}
                </Text>
              )}
              {fieldPreview.error && (
                <Text type="danger" style={{ fontSize: 'var(--font-size-sm)', display: 'block' }}>
                  {fieldPreview.error}
                </Text>
              )}
              {(fieldPreview.valid?.length > 0 || fieldPreview.invalid?.length > 0) && (
                <>
                  <div style={{ marginTop: fieldPreview.hint || fieldPreview.error ? 12 : 0 }}>
                    <Text strong style={{ color: '#52c41a', fontSize: 'var(--font-size-sm)' }}>
                      有效字段
                    </Text>
                    <div style={{ marginTop: 8 }}>
                      <Space wrap>
                        {fieldPreview.valid.map((f) => (
                          <Tag key={f} color="success" style={{ margin: 0 }}>
                            {f}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                  </div>
                  <div style={{ marginTop: 12 }}>
                    <Text strong style={{ color: '#ff4d4f', fontSize: 'var(--font-size-sm)' }}>
                      无效字段
                    </Text>
                    <div style={{ marginTop: 8 }}>
                      <Space wrap>
                        {fieldPreview.invalid.map((f) => (
                          <Tag
                            key={f}
                            color="error"
                            style={{ margin: 0, textDecoration: 'line-through' }}
                          >
                            {f}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                  </div>
                </>
              )}
              {fieldPreview.mode === 'heuristic' &&
                !fieldPreview.valid?.length &&
                !fieldPreview.invalid?.length &&
                !fieldPreview.hint &&
                !fieldPreview.error && (
                  <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                    未从文本中识别到「键: 值」结构，上传后由服务端完整解析。
                  </Text>
                )}
            </div>
          )}
        </Form>
      </Modal>

      {/* Delete confirmation */}
      <DangerConfirmModal
        open={!!deleteTarget}
        title={deleteType === 'category' ? '删除分类' : '删除文档'}
        description={
          deleteType === 'category'
            ? `确定删除分类「${deleteTarget?.name}」？`
            : `确定删除文档「${deleteTarget?.title}」？`
        }
        impactText={
          deleteType === 'category'
            ? '删除分类后，分类下的文档不会被删除，但会变为"未分类"。'
            : '此操作不可恢复，文档及所有分片数据将被永久移除。'
        }
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        confirmLoading={deleteLoading}
      />

      {/* Search test modal */}
      <Modal
        open={searchTestOpen}
        title="检索测试"
        onCancel={() => setSearchTestOpen(false)}
        footer={null}
        width={640}
        centered
        destroyOnHidden
      >
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <Input
            placeholder="输入检索内容..."
            prefix={<SearchOutlined style={{ color: 'var(--color-text-tertiary)' }} />}
            value={searchTestQuery}
            onChange={(e) => setSearchTestQuery(e.target.value)}
            onPressEnter={handleSearchTest}
            allowClear
            style={{ flex: 1 }}
          />
          <Button type="primary" icon={<SearchOutlined />} loading={searchLoading} onClick={handleSearchTest}>
            检索
          </Button>
        </div>
        {searchResults.length > 0 ? (
          <List
            dataSource={searchResults}
            renderItem={(item, idx) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <Space>
                      <Tag color="blue">#{idx + 1}</Tag>
                      <Text strong>{item.document_title || item.title || '未知文档'}</Text>
                      <Tag color="cyan">得分: {(item.score ?? item.similarity ?? 0).toFixed(3)}</Tag>
                    </Space>
                  }
                  description={
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)', whiteSpace: 'pre-wrap' }}>
                      {item.content || item.text || '-'}
                    </Text>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          !searchLoading && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="输入关键词进行语义检索" />
        )}
      </Modal>
    </div>
  );
}
