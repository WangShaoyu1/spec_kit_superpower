import { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Button,
  Card,
  Descriptions,
  Tag,
  Space,
  Input,
  Spin,
  message,
  Empty,
  Row,
  Col,
  List,
  Progress,
} from 'antd';
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  SearchOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useKnowledgeStore from '../../stores/knowledgeStore';
import DangerConfirmModal from '../../components/DangerConfirmModal';
import {
  fileBasename,
  inferFieldsFromDocument,
  extractFieldTagsFromChunk,
  extractRecipeFromChunkContent,
  resolveIndexTime,
} from './fieldInference';

const { Title, Text, Paragraph } = Typography;

const STATUS_MAP = {
  uploading: { color: 'blue', label: '上传中' },
  parsing: { color: 'orange', label: '解析中' },
  indexing: { color: 'cyan', label: '索引中' },
  ready: { color: 'green', label: '就绪' },
  error: { color: 'red', label: '错误' },
};

const FILE_TYPE_ICON = {
  pdf: <FilePdfOutlined style={{ fontSize: 28, color: '#ff4d4f' }} />,
  txt: <FileTextOutlined style={{ fontSize: 28, color: '#8c8c8c' }} />,
  docx: <FileWordOutlined style={{ fontSize: 28, color: '#1677ff' }} />,
  xlsx: <FileExcelOutlined style={{ fontSize: 28, color: '#52c41a' }} />,
};

const CARD_PROPS = {
  variant: 'borderless',
  style: {
    borderRadius: 12,
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  },
};

function formatSize(size) {
  if (!size) return '-';
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function shortId(id) {
  if (!id) return '-';
  const s = String(id);
  if (s.length <= 12) return s;
  return `${s.slice(0, 8)}…`;
}

const SEARCH_TEMPLATES = [
  { key: 'similar', label: '相似菜谱', query: '红烧肉 菜谱 做法 家常' },
  { key: 'steps', label: '步骤查询', query: '加热 翻炒 步骤' },
  { key: 'ingredients', label: '食材搜索', query: '葱姜蒜 食材 配料' },
];

export default function KnowledgeBaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const {
    currentDocument,
    detailLoading,
    searchResults,
    searchLoading,
    fetchDocumentDetail,
    reindexDocument,
    deleteDocument,
    searchKnowledge,
    clearDetail,
    clearSearch,
  } = useKnowledgeStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [reindexing, setReindexing] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    fetchDocumentDetail(id);
    return () => {
      clearDetail();
      clearSearch();
    };
  }, [id, fetchDocumentDetail, clearDetail, clearSearch]);

  const handleReindex = useCallback(async () => {
    setReindexing(true);
    try {
      await reindexDocument(id);
      message.success('重新索引已完成');
    } catch (err) {
      message.error(err?.message || '重新索引失败');
    } finally {
      setReindexing(false);
    }
  }, [id, reindexDocument]);

  const handleSearch = useCallback(
    (q) => {
      const text = (q ?? searchQuery).trim();
      if (!text) return;
      searchKnowledge(text, undefined, 12);
    },
    [searchQuery, searchKnowledge],
  );

  const handleDelete = useCallback(async () => {
    setDeleteLoading(true);
    try {
      await deleteDocument(id);
      message.success('已删除');
      navigate('/knowledge-base');
    } catch (err) {
      message.error(err?.message || '删除失败');
    } finally {
      setDeleteLoading(false);
      setDeleteOpen(false);
    }
  }, [id, deleteDocument, navigate]);

  const maxSearchScore = useMemo(() => {
    const m = searchResults.reduce((acc, h) => Math.max(acc, Number(h.score) || 0), 0);
    return m > 0 ? m : 1;
  }, [searchResults]);

  const fieldSplit = useMemo(() => {
    if (!currentDocument) return { valid: [], invalid: [] };
    return inferFieldsFromDocument(currentDocument);
  }, [currentDocument]);

  if (detailLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!currentDocument) {
    return (
      <Empty description="文档不存在">
        <Button type="primary" onClick={() => navigate('/knowledge-base')}>
          返回列表
        </Button>
      </Empty>
    );
  }

  const doc = currentDocument;
  const statusInfo = STATUS_MAP[doc.status] || { color: 'default', label: doc.status };
  const indexTime = resolveIndexTime(doc);
  const storedName = fileBasename(doc.file_path);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <Space>
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/knowledge-base')} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: 'var(--color-fill, #f5f5f5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {FILE_TYPE_ICON[doc.file_type] || <FileTextOutlined style={{ fontSize: 24 }} />}
            </div>
            <div>
              <Title level={4} style={{ marginBottom: 0 }}>
                {doc.title}
              </Title>
              <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                {storedName && storedName !== doc.title ? `存储文件: ${storedName}` : ''}
              </Text>
            </div>
          </div>
        </Space>
        <Space>
          <Button danger icon={<DeleteOutlined />} onClick={() => setDeleteOpen(true)}>
            删除
          </Button>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            loading={reindexing}
            onClick={handleReindex}
            disabled={doc.status === 'uploading' || doc.status === 'parsing'}
          >
            重新索引
          </Button>
        </Space>
      </div>

      {/* Document metadata */}
      <Card {...CARD_PROPS} styles={{ body: { padding: 'var(--space-6, 24px)' } }}>
        <Descriptions
          bordered
          size="small"
          column={{ xs: 1, sm: 2, md: 3 }}
          labelStyle={{
            color: 'var(--color-text-secondary, rgba(0,0,0,0.45))',
            fontSize: 'var(--font-size-sm)',
            width: 100,
          }}
          contentStyle={{ fontSize: 'var(--font-size-sm)' }}
        >
          <Descriptions.Item label="文件名">{doc.title || '-'}</Descriptions.Item>
          <Descriptions.Item label="格式">{(doc.file_type || '-').toUpperCase()}</Descriptions.Item>
          <Descriptions.Item label="大小">{formatSize(doc.file_size)}</Descriptions.Item>
          <Descriptions.Item label="分类">{doc.category_name || '未分类'}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusInfo.color}>{statusInfo.label}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="上传时间">
            {doc.created_at ? dayjs(doc.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="索引时间">
            {indexTime ? dayjs(indexTime).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="chunk数量">
            <Text style={{ fontFamily: 'var(--font-mono)' }}>{doc.chunk_count ?? doc.chunks?.length ?? 0}</Text>
          </Descriptions.Item>
        </Descriptions>

        {doc.error_message && (
          <div
            style={{
              marginTop: 16,
              padding: '12px 16px',
              background: '#fff2f0',
              border: '1px solid #ffccc7',
              borderRadius: 8,
            }}
          >
            <Text type="danger" style={{ fontSize: 'var(--font-size-sm)' }}>
              {doc.error_message}
            </Text>
          </div>
        )}
      </Card>

      {/* Parsed fields */}
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Card
            {...CARD_PROPS}
            title={<span style={{ color: '#52c41a' }}>有效字段</span>}
            styles={{ body: { minHeight: 120 } }}
          >
            {fieldSplit.valid.length ? (
              <Space wrap size={[8, 8]}>
                {fieldSplit.valid.map((f) => (
                  <Tag key={f} color="success" style={{ margin: 0 }}>
                    {f}
                  </Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                暂无有效字段（上传 JSON 菜谱或等待服务端解析结果后可在此展示）
              </Text>
            )}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card
            {...CARD_PROPS}
            title={<span style={{ color: '#ff4d4f' }}>无效字段</span>}
            styles={{ body: { minHeight: 120 } }}
          >
            {fieldSplit.invalid.length ? (
              <Space wrap size={[8, 8]}>
                {fieldSplit.invalid.map((f) => (
                  <Tag
                    key={f}
                    color="error"
                    style={{
                      margin: 0,
                      textDecoration: 'line-through',
                      opacity: 0.95,
                    }}
                  >
                    {f}
                  </Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                暂无无效或未识别字段
              </Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* Chunk preview */}
      <Card {...CARD_PROPS} title={`索引内容预览 (${doc.chunks?.length || 0})`}>
        <List
          itemLayout="vertical"
          dataSource={doc.chunks || []}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  doc.status === 'ready'
                    ? '暂无分片'
                    : doc.status === 'error'
                      ? '处理失败，请尝试重新索引'
                      : '文档处理中…'
                }
              />
            ),
          }}
          renderItem={(chunk) => {
            const tags = extractFieldTagsFromChunk(chunk.content);
            const recipe = extractRecipeFromChunkContent(chunk.content);
            return (
              <List.Item key={chunk.id} style={{ borderBottom: '1px solid var(--color-border-light, #f0f0f0)' }}>
                <List.Item.Meta
                  title={
                    <Space align="center">
                      <Text strong style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-sm)' }}>
                        chunk_id: {shortId(chunk.id)}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
                        #{chunk.chunk_index}
                      </Text>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                      <Paragraph
                        ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
                        style={{
                          marginBottom: 0,
                          fontSize: 'var(--font-size-sm)',
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {chunk.content}
                      </Paragraph>
                      {tags.length > 0 && (
                        <Space wrap size={[4, 4]}>
                          {tags.map((t) => (
                            <Tag key={t} color="processing" style={{ margin: 0, fontSize: 'var(--font-size-xs)' }}>
                              {t}
                            </Tag>
                          ))}
                        </Space>
                      )}
                      {recipe && (
                        <Card
                          size="small"
                          style={{
                            borderRadius: 10,
                            border: '1px solid #b7eb8f',
                            background: '#f6ffed',
                          }}
                          title={recipe.name || '结构化菜谱'}
                        >
                          {recipe.ingredients?.length > 0 && (
                            <div style={{ marginBottom: 8 }}>
                              <Text strong style={{ fontSize: 'var(--font-size-sm)', color: '#52c41a' }}>
                                食材
                              </Text>
                              <Paragraph style={{ marginBottom: 0, fontSize: 'var(--font-size-sm)' }}>
                                {recipe.ingredients.join(' · ')}
                              </Paragraph>
                            </div>
                          )}
                          {recipe.steps?.length > 0 && (
                            <div>
                              <Text strong style={{ fontSize: 'var(--font-size-sm)', color: '#1677ff' }}>
                                步骤
                              </Text>
                              <ol style={{ margin: '8px 0 0', paddingLeft: 20, fontSize: 'var(--font-size-sm)' }}>
                                {recipe.steps.map((s, i) => (
                                  <li key={i}>{s}</li>
                                ))}
                              </ol>
                            </div>
                          )}
                        </Card>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            );
          }}
        />
      </Card>

      {/* Search test */}
      <Card {...CARD_PROPS} title="检索快速测试">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Input.Search
            placeholder="输入查询，测试知识库检索…"
            value={searchQuery}
            enterButton={
              <Button type="primary" icon={<SearchOutlined />} loading={searchLoading}>
                搜索
              </Button>
            }
            onChange={(e) => setSearchQuery(e.target.value)}
            onSearch={(v) => {
              setSearchQuery(v);
              handleSearch(v);
            }}
          />
          <Space wrap>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
              快捷填充：
            </Text>
            {SEARCH_TEMPLATES.map((t) => (
              <Button key={t.key} size="small" onClick={() => { setSearchQuery(t.query); handleSearch(t.query); }}>
                {t.label}
              </Button>
            ))}
          </Space>
          {searchResults.length > 0 && (
            <List
              size="small"
              dataSource={searchResults}
              renderItem={(hit) => {
                const raw = Number(hit.score) || 0;
                const pct = Math.min(100, Math.round((raw / maxSearchScore) * 100));
                return (
                  <List.Item style={{ padding: '12px 0', borderBottom: '1px solid var(--color-border-light, #f0f0f0)' }}>
                    <div style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
                        <Text strong style={{ fontSize: 'var(--font-size-sm)', color: '#1677ff' }}>
                          {hit.document_title}
                        </Text>
                        <Tag style={{ fontFamily: 'var(--font-mono)', margin: 0 }}>{raw.toFixed(3)}</Tag>
                      </div>
                      <Progress
                        percent={pct}
                        size="small"
                        showInfo={false}
                        strokeColor={{ '0%': '#1677ff', '100%': '#69b1ff' }}
                        style={{ marginTop: 8 }}
                      />
                      <Paragraph
                        type="secondary"
                        ellipsis={{ rows: 2 }}
                        style={{ marginBottom: 0, marginTop: 8, fontSize: 'var(--font-size-sm)' }}
                      >
                        {hit.content}
                      </Paragraph>
                    </div>
                  </List.Item>
                );
              }}
            />
          )}
        </Space>
      </Card>

      <DangerConfirmModal
        open={deleteOpen}
        title="删除文档"
        description={`确定删除「${doc.title}」？`}
        impactText="此操作不可恢复，文档及分片将被永久移除。"
        onConfirm={handleDelete}
        onCancel={() => setDeleteOpen(false)}
        confirmLoading={deleteLoading}
      />
    </div>
  );
}
