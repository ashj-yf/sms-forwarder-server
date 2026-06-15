import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type React from 'react';
import { FormEvent, useState } from 'react';
import { Link, NavLink, Navigate, Outlet, Route, Routes, useNavigate, useOutletContext, useParams } from 'react-router-dom';
import { Battery, Contact, Gauge, MapPin, MessageSquare, Phone, Radio, RotateCw, Settings, Webhook } from 'lucide-react';

import { getCurrentUser, login } from './api/endpoints/auth';
import { createDevice, getDevice, listDevices, updateDevice } from './api/endpoints/devices';
import { createWebhook, rotateWebhook } from './api/endpoints/webhooks';
import { queryBattery } from './api/endpoints/battery';
import { queryCalls } from './api/endpoints/calls';
import { queryConfig } from './api/endpoints/config';
import { queryContacts } from './api/endpoints/contacts';
import { queryLocation } from './api/endpoints/location';
import { querySms } from './api/endpoints/sms';
import { ApiError } from './api/client';
import { queryKeys } from './api/queryKeys';
import type { DeviceCreate, DeviceOut, DeviceUpdate, QueryMode, QueryResult } from './api/types';
import { clearStoredToken, getStoredToken, setStoredToken } from './store/auth';
import { compactJson, formatDateTime } from './utils/format';

function AuthGuard(): React.JSX.Element {
  const token = getStoredToken();
  const userQuery = useQuery({ queryKey: queryKeys.currentUser, queryFn: getCurrentUser, enabled: Boolean(token), retry: false });

  if (!token) {
    return <Navigate to="/login" replace />;
  }
  if (userQuery.isLoading) {
    return <div className="login-page muted">正在校验会话…</div>;
  }
  if (userQuery.isError) {
    clearStoredToken();
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

function AppShell(): React.JSX.Element {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const user = queryClient.getQueryData(queryKeys.currentUser) as { username?: string } | undefined;

  function logout(): void {
    clearStoredToken();
    queryClient.clear();
    navigate('/login');
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Radio size={22} /></div>
          <div>
            <strong>SmsForwarder</strong>
            <div className="muted mono">operator console</div>
          </div>
        </div>
        <nav className="nav-list">
          <NavLink className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} to="/" end><Gauge size={18} />总览</NavLink>
          <NavLink className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} to="/devices"><Radio size={18} />设备</NavLink>
        </nav>
      </aside>
      <main className="main-panel">
        <div className="topbar">
          <div className="muted">已登录：<span className="mono">{user?.username ?? 'operator'}</span></div>
          <button className="btn ghost" onClick={logout}>退出</button>
        </div>
        <Outlet />
      </main>
    </div>
  );
}

function LoginPage(): React.JSX.Element {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const mutation = useMutation({
    mutationFn: login,
    onSuccess: async (token) => {
      setStoredToken(token.access_token);
      await queryClient.fetchQuery({ queryKey: queryKeys.currentUser, queryFn: getCurrentUser });
      navigate('/');
    },
  });

  function submit(event: FormEvent): void {
    event.preventDefault();
    if (!username.trim() || !password) {
      return;
    }
    mutation.mutate({ username: username.trim(), password });
  }

  return (
    <div className="login-page">
      <form className="card login-card form-grid" onSubmit={submit}>
        <div className="brand">
          <div className="brand-mark"><Radio size={22} /></div>
          <div>
            <h1 className="page-title">Console</h1>
            <p className="muted">登录后管理设备、Webhook 与实时查询链路。</p>
          </div>
        </div>
        <label className="field">用户名<input className="input" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" /></label>
        <label className="field">密码<input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" /></label>
        {mutation.isError ? <div className="notice error">{errorMessage(mutation.error)}</div> : null}
        <button className="btn primary" disabled={mutation.isPending || !username.trim() || !password}>进入控制台</button>
      </form>
    </div>
  );
}

function DashboardPage(): React.JSX.Element {
  const devicesQuery = useQuery({ queryKey: queryKeys.devices.list, queryFn: listDevices });
  const devices = devicesQuery.data?.items ?? [];
  const activeCount = devices.filter((device) => device.is_active).length;
  const webhookCount = devices.reduce((sum, device) => sum + device.webhook_count, 0);
  const latest = devices.map((device) => device.last_webhook_at).filter(Boolean).sort().at(-1) ?? null;

  return (
    <div className="grid">
      <div className="split">
        <div>
          <h1 className="page-title">电信链路总览</h1>
          <p className="muted">以设备和 webhook 上报为中心的运维视图。</p>
        </div>
        <Link className="btn primary" to="/devices/new">新建设备</Link>
      </div>
      <div className="grid cards">
        <MetricCard label="设备总数" value={devicesQuery.isLoading ? '…' : devices.length} />
        <MetricCard label="活跃设备" value={activeCount} tone="ok" />
        <MetricCard label="Webhook 事件" value={webhookCount} />
        <MetricCard label="最近上报" value={formatDateTime(latest)} />
      </div>
      <DeviceTable devices={devices.slice(0, 6)} loading={devicesQuery.isLoading} />
    </div>
  );
}

function MetricCard(props: { label: string; value: number | string; tone?: 'ok' }): React.JSX.Element {
  return <section className="card"><p className="card-title">{props.label}</p><div className={`metric ${props.tone === 'ok' ? 'ok' : ''}`}>{props.value}</div></section>;
}

function DevicesListPage(): React.JSX.Element {
  const devicesQuery = useQuery({ queryKey: queryKeys.devices.list, queryFn: listDevices });
  return (
    <div className="grid">
      <div className="split">
        <div>
          <h1 className="page-title">设备</h1>
          <p className="muted">管理 SmsForwarder 终端、通道和上报状态。</p>
        </div>
        <Link className="btn primary" to="/devices/new">新建设备</Link>
      </div>
      <DeviceTable devices={devicesQuery.data?.items ?? []} loading={devicesQuery.isLoading} />
      {devicesQuery.isError ? <div className="notice error">{errorMessage(devicesQuery.error)}</div> : null}
    </div>
  );
}

function DeviceTable(props: { devices: DeviceOut[]; loading: boolean }): React.JSX.Element {
  if (props.loading) {
    return <div className="card muted">正在载入设备…</div>;
  }
  if (props.devices.length === 0) {
    return <div className="card"><h3>还没有设备</h3><p className="muted">先创建设备，再把 Webhook URL 配到 SmsForwarder App。</p></div>;
  }
  return (
    <section className="card table-wrap">
      <table>
        <thead><tr><th>设备</th><th>通道</th><th>状态</th><th>最近心跳</th><th>最近 Webhook</th><th>事件</th></tr></thead>
        <tbody>{props.devices.map((device) => (
          <tr key={device.device_id}>
            <td><Link to={`/devices/${device.device_id}/overview`}><strong>{device.device_name || '未命名设备'}</strong><div className="mono muted">{device.device_id}</div></Link></td>
            <td><span className="badge hot">{device.channel_type}</span></td>
            <td><span className={`badge ${device.is_active ? 'ok' : ''}`}>{device.status}</span></td>
            <td>{formatDateTime(device.last_seen_at)}</td>
            <td>{formatDateTime(device.last_webhook_at)}</td>
            <td className="mono">{device.webhook_count}</td>
          </tr>
        ))}</tbody>
      </table>
    </section>
  );
}

function DeviceFormPage(): React.JSX.Element {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({ mutationFn: createDevice, onSuccess: async (device) => { await queryClient.invalidateQueries({ queryKey: queryKeys.devices.list }); navigate(`/devices/${device.device_id}/overview`); } });
  return <DeviceEditor title="新建设备" submitLabel="创建" onSubmit={(payload) => mutation.mutate(payload as DeviceCreate)} error={mutation.error} pending={mutation.isPending} />;
}

function DeviceEditor(props: { title: string; submitLabel: string; initial?: DeviceOut; pending: boolean; error: unknown; onSubmit: (payload: DeviceCreate | DeviceUpdate) => void }): React.JSX.Element {
  const [deviceName, setDeviceName] = useState(props.initial?.device_name ?? '');
  const [channelType, setChannelType] = useState(props.initial?.channel_type ?? 'hybrid');
  const [baseUrl, setBaseUrl] = useState(props.initial?.base_url ?? '');
  const [signSecret, setSignSecret] = useState('');
  const showRemote = channelType !== 'webhook_only';

  function submit(event: FormEvent): void {
    event.preventDefault();
    props.onSubmit({ device_name: deviceName.trim() || null, channel_type: channelType, base_url: showRemote && baseUrl.trim() ? baseUrl.trim() : null, sign_secret: signSecret || null });
  }

  return (
    <form className="card form-grid" onSubmit={submit}>
      <h1 className="page-title">{props.title}</h1>
      <label className="field">设备名称<input className="input" value={deviceName} onChange={(event) => setDeviceName(event.target.value)} maxLength={255} /></label>
      <label className="field">通道类型<select className="select" value={channelType} onChange={(event) => setChannelType(event.target.value)}><option value="hybrid">hybrid</option><option value="webhook_only">webhook_only</option><option value="http">http</option></select></label>
      {showRemote ? <label className="field">设备 HTTP Base URL<input className="input" value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} placeholder="http://192.168.1.12:8080" /></label> : <div className="notice">webhook_only 设备只支持 cache 查询，realtime 会被后端拒绝。</div>}
      <label className="field">签名密钥（可选，一次性写入）<input className="input" value={signSecret} onChange={(event) => setSignSecret(event.target.value)} maxLength={512} placeholder="留空表示不设置或不变更" /></label>
      {props.error ? <div className="notice error">{errorMessage(props.error)}</div> : null}
      <button className="btn primary" disabled={props.pending}>{props.submitLabel}</button>
    </form>
  );
}

const tabs = [
  ['overview', '概览'], ['sms', '短信'], ['calls', '通话'], ['contacts', '联系人'], ['battery', '电量'], ['location', '位置'], ['config', '配置'], ['webhook', 'Webhook'], ['settings', '设置'],
] as const;

function DeviceDetailLayout(): React.JSX.Element {
  const { deviceId = '' } = useParams();
  const deviceQuery = useQuery({ queryKey: queryKeys.devices.detail(deviceId), queryFn: () => getDevice(deviceId), enabled: Boolean(deviceId) });
  if (deviceQuery.isLoading) return <div className="card muted">正在载入设备…</div>;
  if (!deviceQuery.data) return <div className="notice error">设备不存在或无权限访问。</div>;
  return (
    <div className="grid">
      <div className="split">
        <div><h1 className="page-title">{deviceQuery.data.device_name || '未命名设备'}</h1><p className="mono muted">{deviceQuery.data.device_id}</p></div>
        <span className={`badge ${deviceQuery.data.is_active ? 'ok' : ''}`}>{deviceQuery.data.status}</span>
      </div>
      <div className="tabs">{tabs.map(([path, label]) => <NavLink key={path} className={({ isActive }) => `tab ${isActive ? 'active' : ''}`} to={`/devices/${deviceId}/${path}`}>{label}</NavLink>)}</div>
      <Outlet context={deviceQuery.data} />
    </div>
  );
}

function useDevice(): DeviceOut {
  return useOutletContext<DeviceOut>();
}

function OverviewTab(): React.JSX.Element {
  const device = useDevice();
  return <div className="grid cards"><MetricCard label="通道" value={device.channel_type} /><MetricCard label="最近心跳" value={formatDateTime(device.last_seen_at)} /><MetricCard label="最近 Webhook" value={formatDateTime(device.last_webhook_at)} /><MetricCard label="Webhook 事件" value={device.webhook_count} /></div>;
}

function SettingsTab(): React.JSX.Element {
  const device = useDevice();
  const queryClient = useQueryClient();
  const mutation = useMutation({ mutationFn: (payload: DeviceUpdate) => updateDevice(device.device_id, payload), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: queryKeys.devices.detail(device.device_id) }); } });
  return <DeviceEditor title="设备设置" submitLabel="保存设置" initial={device} pending={mutation.isPending} error={mutation.error} onSubmit={(payload) => mutation.mutate(payload as DeviceUpdate)} />;
}

function ModeToggle(props: { value: QueryMode; onChange: (mode: QueryMode) => void; realtimeDisabled?: boolean }): React.JSX.Element {
  return <div className="segmented"><button className={props.value === 'cache' ? 'active' : ''} onClick={() => props.onChange('cache')} type="button">cache</button><button className={props.value === 'realtime' ? 'active' : ''} onClick={() => props.onChange('realtime')} disabled={props.realtimeDisabled} type="button">realtime</button></div>;
}

function QueryPanel(props: { title: string; icon: React.JSX.Element; run: (mode: QueryMode) => Promise<QueryResult>; realtimeDisabled?: boolean }): React.JSX.Element {
  const [mode, setMode] = useState<QueryMode>(props.realtimeDisabled ? 'cache' : 'realtime');
  const mutation = useMutation({ mutationFn: () => props.run(mode) });
  return (
    <section className="card grid">
      <div className="split"><h2>{props.icon} {props.title}</h2><div className="actions"><ModeToggle value={mode} onChange={setMode} realtimeDisabled={props.realtimeDisabled} /><button className="btn primary" onClick={() => mutation.mutate()} disabled={mutation.isPending}><RotateCw size={16} />查询</button></div></div>
      {props.realtimeDisabled ? <div className="notice">该设备为 webhook_only，已限制为 cache 查询。</div> : null}
      {mutation.isError ? <div className="notice error">{errorMessage(mutation.error)}</div> : null}
      {mutation.data ? <RequestInspector data={mutation.data} /> : <div className="muted">点击查询以查看结果。</div>}
    </section>
  );
}

function RequestInspector(props: { data: QueryResult }): React.JSX.Element {
  return <div className="grid"><div className="actions"><span className="badge hot">{props.data.mode}</span><span className="badge mono">{props.data.request_id}</span></div><pre className="card mono">{compactJson(props.data.result)}</pre></div>;
}

function SmsTab(): React.JSX.Element { const device = useDevice(); return <QueryPanel title="短信查询" icon={<MessageSquare size={18} />} realtimeDisabled={device.channel_type === 'webhook_only'} run={(mode) => querySms(device.device_id, { mode, page_num: 1, page_size: 20 })} />; }
function CallsTab(): React.JSX.Element { const device = useDevice(); return <QueryPanel title="通话查询" icon={<Phone size={18} />} realtimeDisabled={device.channel_type === 'webhook_only'} run={(mode) => queryCalls(device.device_id, { mode, page_num: 1, page_size: 20 })} />; }
function ContactsTab(): React.JSX.Element { const device = useDevice(); return <QueryPanel title="联系人查询" icon={<Contact size={18} />} realtimeDisabled={device.channel_type === 'webhook_only'} run={(mode) => queryContacts(device.device_id, { mode, page_num: 1, page_size: 20 })} />; }
function BatteryTab(): React.JSX.Element { const device = useDevice(); return <QueryPanel title="电量快照" icon={<Battery size={18} />} realtimeDisabled={device.channel_type === 'webhook_only'} run={(mode) => queryBattery(device.device_id, { mode })} />; }
function LocationTab(): React.JSX.Element { const device = useDevice(); return <QueryPanel title="位置快照" icon={<MapPin size={18} />} realtimeDisabled={device.channel_type === 'webhook_only'} run={(mode) => queryLocation(device.device_id, { mode })} />; }
function ConfigTab(): React.JSX.Element { const device = useDevice(); return <QueryPanel title="配置快照" icon={<Settings size={18} />} realtimeDisabled={device.channel_type === 'webhook_only'} run={(mode) => queryConfig(device.device_id, { mode })} />; }

function WebhookTab(): React.JSX.Element {
  const device = useDevice();
  const [secret, setSecret] = useState<{ url: string; token: string } | null>(null);
  const createMutation = useMutation({ mutationFn: () => createWebhook(device.device_id), onSuccess: (data) => setSecret({ url: data.webhook_url, token: data.webhook_token }) });
  const rotateMutation = useMutation({ mutationFn: () => rotateWebhook(device.device_id), onSuccess: (data) => setSecret({ url: data.webhook_url, token: data.webhook_token }) });
  const pending = createMutation.isPending || rotateMutation.isPending;
  return (
    <section className="card grid">
      <div className="split"><h2><Webhook size={18} /> Webhook 管理</h2><div className="actions"><button className="btn primary" onClick={() => createMutation.mutate()} disabled={pending}>创建</button><button className="btn" onClick={() => rotateMutation.mutate()} disabled={pending}>轮换</button></div></div>
      <p className="muted">Webhook token 只在创建或轮换时明文返回。关闭弹窗后前端不会保存明文。</p>
      {createMutation.error || rotateMutation.error ? <div className="notice error">{errorMessage(createMutation.error ?? rotateMutation.error)}</div> : null}
      {secret ? <OneTimeSecret url={secret.url} token={secret.token} onClose={() => setSecret(null)} /> : null}
    </section>
  );
}

function OneTimeSecret(props: { url: string; token: string; onClose: () => void }): React.JSX.Element {
  return <div className="notice grid"><strong>一次性 Webhook 机密</strong><div>URL</div><pre className="mono">{props.url}</pre><div>Token</div><pre className="mono">{props.token}</pre><div className="actions"><button className="btn primary" onClick={() => void navigator.clipboard.writeText(props.url)}>复制 URL</button><button className="btn" onClick={props.onClose}>我已保存，关闭</button></div></div>;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const requestId = error.requestId ? `（request_id: ${error.requestId}）` : '';
    const retry = error.retryAfter ? ` 请 ${error.retryAfter} 秒后重试。` : '';
    return `${error.message}${requestId}${retry}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return '请求失败';
}

export default function App(): React.JSX.Element {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AuthGuard />}>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="devices" element={<DevicesListPage />} />
          <Route path="devices/new" element={<DeviceFormPage />} />
          <Route path="devices/:deviceId" element={<DeviceDetailLayout />}>
            <Route index element={<Navigate to="overview" replace />} />
            <Route path="overview" element={<OverviewTab />} />
            <Route path="sms" element={<SmsTab />} />
            <Route path="calls" element={<CallsTab />} />
            <Route path="contacts" element={<ContactsTab />} />
            <Route path="battery" element={<BatteryTab />} />
            <Route path="location" element={<LocationTab />} />
            <Route path="config" element={<ConfigTab />} />
            <Route path="webhook" element={<WebhookTab />} />
            <Route path="settings" element={<SettingsTab />} />
          </Route>
          <Route path="*" element={<div className="card"><h1>404</h1><p className="muted">没有找到这个控制台页面。</p></div>} />
        </Route>
      </Route>
    </Routes>
  );
}
