import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { useState } from 'react'

import { AppShell } from './app/AppShell'
import { LoginPage } from './modules/auth/LoginPage'
import { BatchTestDetailPage } from './modules/batch-test/BatchTestDetailPage'
import { BatchTestPage } from './modules/batch-test/BatchTestPage'
import { DialogProfileDetailPage } from './modules/dialog-profile/DialogProfileDetailPage'
import { DialogProfilePage } from './modules/dialog-profile/DialogProfilePage'
import { DialogProfileTestPage } from './modules/dialog-profile/DialogProfileTestPage'
import { IntentLibraryPage } from './modules/intent-library/IntentLibraryPage'
import { KnowledgeBasePage } from './modules/knowledge-base/KnowledgeBasePage'
import { KnowledgeDocumentDetailPage } from './modules/knowledge-base/KnowledgeDocumentDetailPage'
import { MonitoringAlertRulesPage } from './modules/monitoring/MonitoringAlertRulesPage'
import { MonitoringDashboardPage } from './modules/monitoring/MonitoringDashboardPage'
import { MonitoringDeviceLogsPage } from './modules/monitoring/MonitoringDeviceLogsPage'
import { UserMgmtPage } from './modules/user-mgmt/UserMgmtPage'
import { login } from './services/api'

const theme = {
  token: {
    colorPrimary: '#ffb04d',
    colorBgBase: '#0f1723',
    colorTextBase: '#e6edf7',
    borderRadius: 18,
    fontFamily: '"Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
  },
}

const SESSION_KEY = 'smartchef-session'

export default function App() {
  const [session, setSession] = useState(() => {
    const stored = localStorage.getItem(SESSION_KEY)
    return stored ? JSON.parse(stored) : null
  })

  async function handleLogin(credentials) {
    const nextSession = await login(credentials.username, credentials.password)
    localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession))
    window.history.pushState({}, '', '/user-mgmt')
    setSession(nextSession)
  }

  if (!session) {
    return (
      <ConfigProvider locale={zhCN} theme={theme}>
        <LoginPage onLogin={handleLogin} />
      </ConfigProvider>
    )
  }

  return (
    <ConfigProvider locale={zhCN} theme={theme}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppShell capabilities={session.capabilities} />}>
            <Route path="user-mgmt" element={<UserMgmtPage token={session.access_token} />} />
            <Route path="intent-library" element={<IntentLibraryPage token={session.access_token} />} />
            <Route path="knowledge-base" element={<KnowledgeBasePage token={session.access_token} />} />
            <Route path="knowledge-base/:documentId" element={<KnowledgeDocumentDetailPage token={session.access_token} />} />
            <Route path="dialog-profiles" element={<DialogProfilePage token={session.access_token} />} />
            <Route path="dialog-profiles/:profileId" element={<DialogProfileDetailPage token={session.access_token} />} />
            <Route path="dialog-profiles/:profileId/test" element={<DialogProfileTestPage token={session.access_token} />} />
            <Route path="batch-tests" element={<BatchTestPage token={session.access_token} />} />
            <Route path="batch-tests/:batchId" element={<BatchTestDetailPage token={session.access_token} />} />
            <Route path="monitoring" element={<MonitoringDashboardPage token={session.access_token} />} />
            <Route path="monitoring/device-logs" element={<MonitoringDeviceLogsPage token={session.access_token} />} />
            <Route path="monitoring/alert-rules" element={<MonitoringAlertRulesPage token={session.access_token} />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}
