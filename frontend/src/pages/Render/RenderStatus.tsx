import { useEffect, useRef, useState } from 'react'
import { Result, Button, Spin, Typography, Alert, Space } from 'antd'
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import { getRenderStatus, downloadRender } from '../../api/render'
import { useAuthStore } from '../../stores/authStore'
import type { RenderTask } from '../../types/api'

const { Title } = Typography

export default function RenderStatusPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const { token } = useAuthStore()
  const [task, setTask] = useState<RenderTask | null>(null)
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const [previewError, setPreviewError] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchStatus = async () => {
    if (!taskId) return
    try {
      const t = await getRenderStatus(taskId)
      setTask(t)
      if (t.status === 'done' || t.status === 'failed') {
        if (intervalRef.current) clearInterval(intervalRef.current)
        if (t.status === 'done') fetchPreview()
      }
    } catch {/* ignore */}
  }

  const fetchPreview = async () => {
    if (!taskId || !token) return
    try {
      const res = await fetch(`/api/render/${taskId}/preview`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const html = await res.text()
        setPreviewHtml(html)
      } else {
        setPreviewError(true)
      }
    } catch {
      setPreviewError(true)
    }
  }

  useEffect(() => {
    fetchStatus()
    intervalRef.current = setInterval(fetchStatus, 2000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [taskId]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!task) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载中...</div>
      </div>
    )
  }

  if (task.status === 'failed') {
    return (
      <Result
        status="error"
        title="排版失败"
        subTitle={task.error_message ?? '未知错误'}
        extra={[
          <Button key="retry" type="primary" onClick={() => navigate('/render/new')}>
            重新排版
          </Button>,
        ]}
      />
    )
  }

  if (task.status === 'pending' || task.status === 'processing') {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          {task.status === 'pending' ? '排版任务排队中...' : '排版处理中，请稍候...'}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>排版预览</Title>
        <Space>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => token && downloadRender(taskId!, token)}
            data-testid="download-btn"
          >
            下载 Word 文档
          </Button>
          <Button icon={<ReloadOutlined />} onClick={() => navigate('/render/new')}>
            重新排版
          </Button>
        </Space>
      </div>

      {previewError && (
        <Alert type="warning" message="预览加载失败，但文档已生成，可直接下载" style={{ marginBottom: 16 }} />
      )}

      {previewHtml && !previewError && (
        <iframe
          srcDoc={previewHtml}
          style={{
            width: '100%',
            height: 800,
            border: '1px solid #e8e8e8',
            borderRadius: 8,
            background: '#fff',
          }}
          title="排版预览"
          data-testid="preview-content"
        />
      )}

      {!previewHtml && !previewError && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin />
          <div style={{ marginTop: 8 }}>预览加载中...</div>
        </div>
      )}
    </div>
  )
}
