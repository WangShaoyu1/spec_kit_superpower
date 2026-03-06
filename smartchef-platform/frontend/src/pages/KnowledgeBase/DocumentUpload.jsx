import { useState } from 'react';
import { Modal, Upload, message, Typography } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Dragger } = Upload;
const { Text } = Typography;

export default function DocumentUpload({ visible, kbId, onClose, onSuccess }) {
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (info) => {
    const { file } = info;
    if (!kbId) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post(`/knowledge/bases/${kbId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      message.success(`${file.name} 上传成功`);
      onSuccess?.();
    } catch (err) {
      message.error(err.response?.data?.detail || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Modal title="上传文档" open={visible} onCancel={onClose} footer={null} width={500}>
      <Dragger
        accept=".json,.md,.markdown,.txt"
        customRequest={handleUpload}
        showUploadList={false}
        disabled={uploading}
      >
        <p className="ant-upload-drag-icon"><InboxOutlined /></p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持 JSON 和 Markdown 格式。系统将自动解析内容、过滤无效字段并建立索引。
        </p>
      </Dragger>
      <div style={{ marginTop: 12 }}>
        <Text type="secondary">
          菜谱文档将自动提取菜名、食材、步骤、营养成分等有效信息，过滤图片URL、点赞数等无效字段。
        </Text>
      </div>
    </Modal>
  );
}
