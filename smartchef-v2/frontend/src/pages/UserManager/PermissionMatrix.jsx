import { useMemo } from 'react';
import { Checkbox, Typography, Spin, Table, Tooltip } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

const MODULE_LABELS = {
  指令库: { gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  对话方案: { gradient: 'linear-gradient(135deg, #1677ff 0%, #69b1ff 100%)' },
  知识库: { gradient: 'linear-gradient(135deg, #52c41a 0%, #95de64 100%)' },
  批量测试: { gradient: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)' },
  监控: { gradient: 'linear-gradient(135deg, #eb2f96 0%, #ff85c0 100%)' },
  版本管理: { gradient: 'linear-gradient(135deg, #722ed1 0%, #b37feb 100%)' },
  系统: { gradient: 'linear-gradient(135deg, #fa541c 0%, #ff7a45 100%)' },
};

function buildKeyMeta(modules) {
  const keyToModule = new Map();
  const flat = [];
  for (const mod of modules) {
    for (const p of mod.permissions || []) {
      keyToModule.set(p.key, mod.module);
      flat.push({ key: p.key, label: p.label, module: mod.module });
    }
  }
  return { keyToModule, flat };
}

/** Sort roles so admin / PM / tester appear first for column layout */
export function sortRolesForSummary(roles) {
  const rank = (r) => {
    const n = (r?.name || '').toLowerCase();
    if (n.includes('系统管理') || n.includes('admin') || n === '管理员') return 0;
    if (n.includes('产品') || n === 'pm' || n.includes('产品经理')) return 1;
    if (n.includes('测试') || n.includes('test') || n.includes('工程师')) return 2;
    return 10;
  };
  return [...(roles || [])].sort((a, b) => rank(a) - rank(b) || (a.name || '').localeCompare(b.name || ''));
}

export default function PermissionMatrix({
  modules = [],
  selectedKeys = [],
  onChange,
  loading = false,
  disabled = false,
}) {
  const selectedSet = useMemo(() => new Set(selectedKeys), [selectedKeys]);

  const handleToggle = (key) => {
    if (disabled) return;
    const next = new Set(selectedSet);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    onChange?.([...next]);
  };

  const handleModuleToggle = (perms, checked) => {
    if (disabled) return;
    const next = new Set(selectedSet);
    for (const p of perms) {
      if (checked) {
        next.add(p.key);
      } else {
        next.delete(p.key);
      }
    }
    onChange?.([...next]);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {modules.map((mod) => {
        const meta = MODULE_LABELS[mod.module] || {
          gradient: 'linear-gradient(135deg, #8c8c8c 0%, #bfbfbf 100%)',
        };
        const allChecked = mod.permissions.every((p) => selectedSet.has(p.key));
        const someChecked = mod.permissions.some((p) => selectedSet.has(p.key));

        return (
          <div
            key={mod.module}
            style={{
              border: '1px solid var(--color-border-light, #f0f0f0)',
              borderRadius: 'var(--radius-lg, 8px)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 16px',
                background: 'var(--color-fill, #fafafa)',
                borderBottom: '1px solid var(--color-border-light, #f0f0f0)',
              }}
            >
              <div
                style={{
                  width: 6,
                  height: 20,
                  borderRadius: 3,
                  background: meta.gradient,
                  flexShrink: 0,
                }}
              />
              <Checkbox
                indeterminate={someChecked && !allChecked}
                checked={allChecked}
                onChange={(e) => handleModuleToggle(mod.permissions, e.target.checked)}
                disabled={disabled}
              >
                <Text strong style={{ fontSize: 'var(--font-size-sm, 13px)' }}>
                  {mod.module}
                </Text>
              </Checkbox>
              <Text
                type="secondary"
                style={{ fontSize: 'var(--font-size-xs, 12px)', marginLeft: 'auto' }}
              >
                {mod.permissions.filter((p) => selectedSet.has(p.key)).length}/{mod.permissions.length}
              </Text>
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                gap: '4px 0',
                padding: '12px 16px',
              }}
            >
              {mod.permissions.map((p) => (
                <Checkbox
                  key={p.key}
                  checked={selectedSet.has(p.key)}
                  onChange={() => handleToggle(p.key)}
                  disabled={disabled}
                  style={{ fontSize: 'var(--font-size-sm, 13px)' }}
                >
                  {p.label}
                </Checkbox>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Read-only matrix: rows = capability points, columns = roles.
 * Icons: granted / denied / partial (same module partially authorized).
 */
export function PermissionSummaryMatrix({
  modules = [],
  roles = [],
  rolePermissionsMap = {},
  loading = false,
}) {
  const { flat, keyToModule } = useMemo(() => buildKeyMeta(modules), [modules]);

  const orderedRoles = useMemo(() => sortRolesForSummary(roles), [roles]);

  const columns = useMemo(() => {
    const cols = [
      {
        title: '能力点',
        dataIndex: 'label',
        key: 'label',
        fixed: 'left',
        width: 220,
        render: (text, row) => (
          <div>
            <Text style={{ fontSize: 'var(--font-size-sm, 13px)' }}>{text}</Text>
            <div>
              <Text type="secondary" style={{ fontSize: 'var(--font-size-xs, 12px)' }}>
                {row.module}
              </Text>
            </div>
          </div>
        ),
      },
    ];
    for (const r of orderedRoles) {
      cols.push({
        title: r.name,
        key: `role-${r.id}`,
        align: 'center',
        width: 110,
        render: (_, row) => {
          const keys = rolePermissionsMap[r.id] || [];
          const set = new Set(Array.isArray(keys) ? keys : []);
          const has = set.has(row.key);
          let hasAnyInModule = false;
          for (const k of set) {
            if (keyToModule.get(k) === row.module) {
              hasAnyInModule = true;
              break;
            }
          }
          if (has) {
            return (
              <CheckCircleOutlined
                style={{ color: 'var(--color-success, #52c41a)', fontSize: 18 }}
                aria-label="已授权"
              />
            );
          }
          if (hasAnyInModule) {
            return (
              <Tooltip title="模块内部分能力已授权（与其他能力组合相关）">
                <WarningOutlined
                  style={{ color: 'var(--color-warning, #faad14)', fontSize: 18 }}
                  aria-label="部分相关"
                />
              </Tooltip>
            );
          }
          return (
            <CloseCircleOutlined
              style={{ color: 'var(--color-error, #ff4d4f)', fontSize: 18 }}
              aria-label="未授权"
            />
          );
        },
      });
    }
    return cols;
  }, [orderedRoles, rolePermissionsMap, keyToModule]);

  const dataSource = useMemo(
    () => flat.map((p, i) => ({ ...p, key: p.key || `row-${i}` })),
    [flat],
  );

  if (loading && orderedRoles.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}>
        <Spin />
      </div>
    );
  }

  return (
    <Table
      size="small"
      rowKey="key"
      columns={columns}
      dataSource={dataSource}
      loading={loading}
      pagination={false}
      scroll={{ x: 220 + orderedRoles.length * 110 }}
      style={{ marginTop: 16 }}
    />
  );
}
