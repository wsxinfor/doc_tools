import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { useAuthStore } from './stores/authStore'
import AppLayout from './components/Layout'
import LoginPage from './pages/Login'
import DocumentsPage from './pages/Documents'
import AIProcessPage from './pages/AIProcess'
import TemplatesPage from './pages/Templates'
import TemplateEditorPage from './pages/Templates/TemplateEditor'
import RenderCreatePage from './pages/Render/RenderCreate'
import RenderStatusPage from './pages/Render/RenderStatus'
import RenderHistoryPage from './pages/Render/RenderHistory'
import AdminUsersPage from './pages/Admin/Users'
import AdminSettingsPage from './pages/Admin/Settings'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore()
  if (user?.role !== 'admin') return <Navigate to="/documents" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhCN}
        theme={{
          token: {
            colorPrimary: '#4a5568',
            colorBgContainer: '#ffffff',
            borderRadius: 3,
            colorBorder: '#e2e8f0',
            fontFamily: 'Noto Sans SC, PingFang SC, Microsoft YaHei, sans-serif',
            fontSize: 13,
          },
        }}
      >
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <RequireAuth>
                  <AppLayout />
                </RequireAuth>
              }
            >
              <Route index element={<Navigate to="/documents" replace />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="ai-process/:docId" element={<AIProcessPage />} />
              <Route path="templates" element={<TemplatesPage />} />
              <Route path="templates/new" element={<TemplateEditorPage />} />
              <Route path="templates/:id/edit" element={<TemplateEditorPage />} />
              <Route path="render/new" element={<RenderCreatePage />} />
              <Route path="render/history" element={<RenderHistoryPage />} />
              <Route path="render/:taskId" element={<RenderStatusPage />} />
              <Route
                path="admin/users"
                element={
                  <RequireAdmin>
                    <AdminUsersPage />
                  </RequireAdmin>
                }
              />
              <Route
                path="admin/settings"
                element={
                  <RequireAdmin>
                    <AdminSettingsPage />
                  </RequireAdmin>
                }
              />
            </Route>
            <Route path="*" element={<Navigate to="/documents" replace />} />
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  )
}
