import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { useCallback, useEffect, useState } from 'react'

import { AppShell } from './app/AppShell'
import { LoginPage } from './modules/auth/LoginPage'
import { BatchTestDetailPage } from './modules/batch-test/BatchTestDetailPage'
import { BatchTestPage } from './modules/batch-test/BatchTestPage'
import { DialogProfileDetailPage } from './modules/dialog-profile/DialogProfileDetailPage'
import { DialogProfilePage } from './modules/dialog-profile/DialogProfilePage'
import { DialogProfileTestPage } from './modules/dialog-profile/DialogProfileTestPage'
import { IntentLibraryDatasetsPage } from './modules/intent-library/IntentLibraryDatasetsPage'
import { IntentLibraryDatasetDetailPage } from './modules/intent-library/IntentLibraryDatasetDetailPage'
import { IntentLibraryDetailPage } from './modules/intent-library/IntentLibraryDetailPage'
import { IntentLibraryPage } from './modules/intent-library/IntentLibraryPage'
import { IntentLibraryTestPage } from './modules/intent-library/IntentLibraryTestPage'
import { KnowledgeBasePage } from './modules/knowledge-base/KnowledgeBasePage'
import { KnowledgeDocumentDetailPage } from './modules/knowledge-base/KnowledgeDocumentDetailPage'
import { MonitoringAlertRulesPage } from './modules/monitoring/MonitoringAlertRulesPage'
import { MonitoringDashboardPage } from './modules/monitoring/MonitoringDashboardPage'
import { MonitoringDeviceLogsPage } from './modules/monitoring/MonitoringDeviceLogsPage'
import { UserMgmtPage } from './modules/user-mgmt/UserMgmtPage'
import { login, setAuthFailureHandler } from './services/api'

const theme = {
  token: {
    colorPrimary: '#b87333',
    colorInfo: '#8f5622',
    colorSuccess: '#2d6a4f',
    colorWarning: '#c17f4a',
    colorError: '#9b2c2c',
    colorBgBase: '#f3eee6',
    colorTextBase: '#161311',
    colorBorder: 'rgba(42, 36, 30, 0.12)',
    borderRadiusLG: 18,
    borderRadius: 14,
    fontFamily: '"Outfit", "PingFang SC", "Microsoft YaHei", sans-serif',
    fontSizeHeading1: 34,
    boxShadowSecondary: '0 8px 28px rgba(18, 14, 10, 0.08)',
  },
  components: {
    Button: {
      primaryShadow: '0 2px 0 rgba(255, 255, 255, 0.22) inset, 0 8px 24px rgba(143, 86, 34, 0.18)',
      fontWeight: 600,
    },
    Card: {
      headerBg: 'transparent',
    },
    Input: {
      activeBorderColor: '#b87333',
      hoverBorderColor: 'rgba(184, 115, 51, 0.55)',
    },
    Table: {
      headerBg: 'rgba(255, 252, 248, 0.92)',
      headerColor: 'rgba(110, 82, 52, 0.78)',
      headerSplitColor: 'rgba(42, 36, 30, 0.06)',
      rowHoverBg: 'rgba(184, 115, 51, 0.05)',
      borderColor: 'rgba(42, 36, 30, 0.08)',
      colorBgContainer: 'transparent',
    },
    Tabs: {
      inkBarColor: '#b87333',
      itemActiveColor: '#161311',
      itemHoverColor: '#8f5622',
      itemSelectedColor: '#161311',
      titleFontSize: 15,
      horizontalMargin: '0 0 12px 0',
    },
    Statistic: {
      titleFontSize: 13,
      contentFontSize: 28,
    },
    Typography: {
      fontWeightStrong: 600,
    },
    Modal: {
      contentBg: '#f8f4ec',
    },
    List: {
      colorText: '#161311',
      colorTextDescription: 'rgba(22, 19, 17, 0.62)',
    },
    /* 侧栏为深色底，必须脱离全局 colorTextBase，否则菜单字色近黑不可读 */
    Menu: {
      itemColor: 'rgba(252, 246, 235, 0.92)',
      itemHoverColor: '#fffbf5',
      itemHoverBg: 'rgba(255, 236, 210, 0.14)',
      itemSelectedColor: '#fff4e6',
      itemSelectedBg: 'rgba(184, 115, 51, 0.24)',
      itemActiveBg: 'rgba(184, 115, 51, 0.16)',
      itemDisabledColor: 'rgba(236, 220, 198, 0.52)',
      iconSize: 18,
      collapsedIconSize: 18,
    },
  },
}

const SESSION_KEY = 'smartchef-session'

export default function App() {
  const [session, setSession] = useState(() => {
    const stored = localStorage.getItem(SESSION_KEY)
    return stored ? JSON.parse(stored) : null
  })

  const clearSession = useCallback(() => {
    localStorage.removeItem(SESSION_KEY)
    window.history.replaceState({}, '', '/')
    setSession(null)
  }, [])

  useEffect(() => {
    setAuthFailureHandler(clearSession)
    return () => setAuthFailureHandler(null)
  }, [clearSession])

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
          <Route path="/" element={<AppShell capabilities={session.capabilities} onLogout={clearSession} />}>
            <Route path="user-mgmt" element={<UserMgmtPage token={session.access_token} />} />
            <Route path="intent-library" element={<IntentLibraryPage token={session.access_token} />} />
            <Route path="intent-library/:libraryId" element={<IntentLibraryDetailPage token={session.access_token} />} />
            <Route path="intent-library/:libraryId/datasets" element={<IntentLibraryDatasetsPage token={session.access_token} />} />
            <Route path="intent-library/:libraryId/datasets/:datasetId" element={<IntentLibraryDatasetDetailPage token={session.access_token} />} />
            <Route path="intent-library/:libraryId/test" element={<IntentLibraryTestPage token={session.access_token} />} />
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
