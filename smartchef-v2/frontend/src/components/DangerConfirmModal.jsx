import { useState, useEffect, useCallback, useRef } from 'react';
import { Modal, Checkbox, Typography, Space } from 'antd';
import { ExclamationCircleFilled } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

const COUNTDOWN_SECONDS = 3;

export default function DangerConfirmModal({
  open,
  title = '确认删除',
  description = '此操作不可恢复，请确认是否继续。',
  impactText,
  onConfirm,
  onCancel,
  confirmLoading = false,
}) {
  const [checked, setChecked] = useState(false);
  const [countdown, setCountdown] = useState(COUNTDOWN_SECONDS);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!open) {
      setChecked(false);
      setCountdown(COUNTDOWN_SECONDS);
      return;
    }
  }, [open]);

  useEffect(() => {
    if (!open || !checked) {
      clearInterval(timerRef.current);
      return;
    }

    setCountdown(COUNTDOWN_SECONDS);
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timerRef.current);
  }, [open, checked]);

  const handleConfirm = useCallback(() => {
    if (!checked || countdown > 0) return;
    onConfirm?.();
  }, [checked, countdown, onConfirm]);

  const canConfirm = checked && countdown === 0;

  const buttonLabel = !checked
    ? '确认'
    : countdown > 0
      ? `确认 (${countdown}s)`
      : '确认';

  return (
    <Modal
      open={open}
      title={null}
      onCancel={onCancel}
      onOk={handleConfirm}
      okText={buttonLabel}
      okButtonProps={{
        danger: true,
        disabled: !canConfirm,
      }}
      cancelText="取消"
      confirmLoading={confirmLoading}
      width={440}
      centered
      destroyOnHidden
    >
      <Space direction="vertical" size={16} style={{ width: '100%', padding: '8px 0' }}>
        <Space align="start" size={12}>
          <ExclamationCircleFilled
            style={{ fontSize: 22, color: 'var(--color-error)', marginTop: 2 }}
          />
          <div>
            <Text strong style={{ fontSize: 'var(--font-size-lg)' }}>
              {title}
            </Text>
            <Paragraph
              type="secondary"
              style={{ marginTop: 4, marginBottom: 0, fontSize: 'var(--font-size-sm)' }}
            >
              {description}
            </Paragraph>
          </div>
        </Space>

        {impactText && (
          <div
            style={{
              background: '#fff2f0',
              border: '1px solid #ffccc7',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
            }}
          >
            <Text type="danger" style={{ fontSize: 'var(--font-size-sm)' }}>
              {impactText}
            </Text>
          </div>
        )}

        <Checkbox
          checked={checked}
          onChange={(e) => setChecked(e.target.checked)}
          style={{ fontSize: 'var(--font-size-sm)' }}
        >
          我已了解影响
        </Checkbox>
      </Space>
    </Modal>
  );
}
