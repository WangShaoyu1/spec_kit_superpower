import { useMemo } from 'react';
import { Button, Tooltip } from 'antd';
import useAuthStore from '../stores/authStore';

export default function PermissionGuard({
  capability,
  requireAll = false,
  fallback,
  children,
}) {
  const capabilities = useAuthStore((s) => s.capabilities);

  const hasPermission = useMemo(() => {
    const required = Array.isArray(capability) ? capability : [capability];
    if (required.length === 0) return true;
    return requireAll
      ? required.every((c) => capabilities.includes(c))
      : required.some((c) => capabilities.includes(c));
  }, [capability, requireAll, capabilities]);

  if (hasPermission) return children;

  if (fallback !== undefined) return fallback;

  return (
    <Tooltip title="无权限">
      <Button disabled>无权限</Button>
    </Tooltip>
  );
}
