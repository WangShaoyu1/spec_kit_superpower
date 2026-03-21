import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import MainLayout from './components/Layout/MainLayout';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import NotFound from './pages/404';
import Forbidden from './pages/403';

const DatasetsPage = lazy(() => import('./pages/IntentLibrary/Placeholder').then(m => ({ default: m.DatasetsPage })));
const DatasetDetailPage = lazy(() => import('./pages/IntentLibrary/Placeholder').then(m => ({ default: m.DatasetDetailPage })));
const ModelTestPage = lazy(() => import('./pages/IntentLibrary/Placeholder').then(m => ({ default: m.ModelTestPage })));

const IntentLibrary = lazy(() => import('./pages/IntentLibrary'));
const IntentLibraryDetail = lazy(() => import('./pages/IntentLibrary/Detail'));
const DatasetManagement = lazy(() => import('./pages/DatasetManagement'));
const KnowledgeBase = lazy(() => import('./pages/KnowledgeBase'));
const KnowledgeBaseDetail = lazy(() => import('./pages/KnowledgeBase/Detail'));
const UserManager = lazy(() => import('./pages/UserManager'));
const DialogProfile = lazy(() => import('./pages/DialogProfile'));
const DialogProfileDetail = lazy(() => import('./pages/DialogProfile/Detail'));
const TestChat = lazy(() => import('./pages/TestChat'));
const BatchTest = lazy(() => import('./pages/BatchTest'));
const BatchTestDetail = lazy(() => import('./pages/BatchTest/Detail'));
const Monitoring = lazy(() => import('./pages/Monitoring'));
const DeviceLogs = lazy(() => import('./pages/Monitoring/DeviceLogs'));
const AlertRules = lazy(() => import('./pages/Monitoring/AlertRules'));

const PageLoader = (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 320 }}>
    <Spin size="large" />
  </div>
);

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/403" element={<Forbidden />} />
        <Route path="/" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
          <Route index element={<Navigate to="/intent-library" replace />} />

          <Route
            path="intent-library"
            element={<Suspense fallback={PageLoader}><IntentLibrary /></Suspense>}
          />
          <Route
            path="intent-library/:id"
            element={<Suspense fallback={PageLoader}><IntentLibraryDetail /></Suspense>}
          />
          <Route
            path="dataset-management"
            element={<Suspense fallback={PageLoader}><DatasetManagement /></Suspense>}
          />
          <Route path="intent-library/:id/datasets" element={<Suspense fallback={PageLoader}><DatasetsPage /></Suspense>} />
          <Route path="intent-library/:id/datasets/:datasetId" element={<Suspense fallback={PageLoader}><DatasetDetailPage /></Suspense>} />
          <Route path="intent-library/:id/test" element={<Suspense fallback={PageLoader}><ModelTestPage /></Suspense>} />

          <Route
            path="knowledge-base"
            element={<Suspense fallback={PageLoader}><KnowledgeBase /></Suspense>}
          />
          <Route
            path="knowledge-base/:id"
            element={<Suspense fallback={PageLoader}><KnowledgeBaseDetail /></Suspense>}
          />

          <Route
            path="dialog-profile"
            element={<Suspense fallback={PageLoader}><DialogProfile /></Suspense>}
          />
          <Route
            path="dialog-profile/:id"
            element={<Suspense fallback={PageLoader}><DialogProfileDetail /></Suspense>}
          />

          <Route
            path="test-chat"
            element={<Suspense fallback={PageLoader}><TestChat /></Suspense>}
          />

          <Route
            path="batch-test"
            element={<Suspense fallback={PageLoader}><BatchTest /></Suspense>}
          />
          <Route
            path="batch-test/:id"
            element={<Suspense fallback={PageLoader}><BatchTestDetail /></Suspense>}
          />

          <Route
            path="monitoring"
            element={<Suspense fallback={PageLoader}><Monitoring /></Suspense>}
          />
          <Route path="monitoring/overview" element={<Navigate to="/monitoring" replace />} />
          <Route
            path="monitoring/device-logs"
            element={<Suspense fallback={PageLoader}><DeviceLogs /></Suspense>}
          />
          <Route
            path="monitoring/alert-rules"
            element={<Suspense fallback={PageLoader}><AlertRules /></Suspense>}
          />

          <Route
            path="user-manager"
            element={<Suspense fallback={PageLoader}><UserManager /></Suspense>}
          />

          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}
