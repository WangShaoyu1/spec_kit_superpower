import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Input, Button, Typography, Alert } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import useAuthStore from '../../stores/authStore';

const { Title, Text } = Typography;

const BG_STYLE = {
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: `
    radial-gradient(ellipse at 20% 50%, rgba(22,119,255,0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(22,119,255,0.06) 0%, transparent 40%),
    radial-gradient(ellipse at 60% 80%, rgba(82,196,26,0.04) 0%, transparent 40%),
    linear-gradient(160deg, #f5f7fa 0%, #e8ecf1 40%, #dfe4eb 100%)
  `,
  position: 'relative',
  overflow: 'hidden',
};

const GRID_BG = {
  position: 'absolute',
  inset: 0,
  backgroundImage: `
    linear-gradient(rgba(22,119,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22,119,255,0.04) 1px, transparent 1px)
  `,
  backgroundSize: '48px 48px',
  pointerEvents: 'none',
};

const CARD_STYLE = {
  width: 420,
  borderRadius: 'var(--radius-xl)',
  boxShadow: `
    0 8px 32px rgba(0,0,0,0.08),
    0 2px 8px rgba(0,0,0,0.04),
    0 0 0 1px rgba(22,119,255,0.06)
  `,
  border: 'none',
  backdropFilter: 'blur(20px)',
  background: 'rgba(255,255,255,0.92)',
};

export default function Login() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [visible, setVisible] = useState(false);

  const login = useAuthStore((s) => s.login);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
      return;
    }
    const raf = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(raf);
  }, [isAuthenticated, navigate]);

  const onFinish = useCallback(
    async (values) => {
      setLoading(true);
      setError('');
      try {
        await login(values.username, values.password);
        navigate('/', { replace: true });
      } catch (err) {
        setError(err?.message || '登录失败，请检查用户名和密码');
      } finally {
        setLoading(false);
      }
    },
    [login, navigate],
  );

  return (
    <div style={BG_STYLE}>
      <div style={GRID_BG} />

      <div
        style={{
          position: 'absolute',
          top: '12%',
          left: '8%',
          width: 280,
          height: 280,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(22,119,255,0.08) 0%, transparent 70%)',
          filter: 'blur(40px)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '10%',
          right: '12%',
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(22,119,255,0.06) 0%, transparent 70%)',
          filter: 'blur(30px)',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'opacity 0.5s cubic-bezier(0.4,0,0.2,1), transform 0.5s cubic-bezier(0.4,0,0.2,1)',
          zIndex: 1,
        }}
      >
        <Card style={CARD_STYLE} styles={{ body: { padding: '48px 36px 40px' } }}>
          {/* Brand */}
          <div style={{ textAlign: 'center', marginBottom: 36 }}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 14,
                background: 'linear-gradient(135deg, #1677ff 0%, #69b1ff 100%)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 22,
                fontWeight: 700,
                color: '#fff',
                boxShadow: '0 4px 14px rgba(22,119,255,0.3)',
                marginBottom: 16,
              }}
            >
              SC
            </div>
            <Title level={3} style={{ marginBottom: 4, letterSpacing: '-0.02em' }}>
              SmartChef
            </Title>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
              智能对话管理平台
            </Text>
          </div>

          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              closable
              onClose={() => setError('')}
              style={{ marginBottom: 20, borderRadius: 'var(--radius-md)' }}
            />
          )}

          <Form form={form} name="login" onFinish={onFinish} size="large" autoComplete="off">
            <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
              <Input
                prefix={<UserOutlined style={{ color: 'var(--color-text-tertiary)' }} />}
                placeholder="用户名"
                style={{ height: 44 }}
              />
            </Form.Item>

            <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
              <Input.Password
                prefix={<LockOutlined style={{ color: 'var(--color-text-tertiary)' }} />}
                placeholder="密码"
                style={{ height: 44 }}
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
              <Button
                type="primary"
                htmlType="submit"
                block
                loading={loading}
                style={{
                  height: 44,
                  fontSize: 'var(--font-size-lg)',
                  fontWeight: 600,
                  borderRadius: 'var(--radius-md)',
                  boxShadow: loading ? 'none' : '0 2px 8px rgba(22,119,255,0.25)',
                }}
              >
                登录
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center', marginTop: 28 }}>
            <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
              SmartChef v2.0 · 企业级智能对话管理平台
            </Text>
          </div>
        </Card>
      </div>
    </div>
  );
}
