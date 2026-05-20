import { Table, Button, Tag, Space, Typography } from 'antd'
import { EyeOutlined, DownloadOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { getRenderList, downloadRender } from '../../api/render'
import { useAuthStore } from '../../stores/authStore'
import type { RenderTask } from '../../types/api'

const { Title } = Typography

const STATUS_MAP: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '等待中' },
  processing: { color: 'processing', text: '处理中' },
  done: { color: 'success', text: '完成' },
  failed: { color: 'error', text: '失败' },
}

export default function RenderHistoryPage() {
  const navigate = useNavigate()
  const { token } = useAuthStore()

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['render-list'],
    queryFn: getRenderList,
  })

  const columns = [
    { title: '任务 ID', dataIndex: 'id', key: 'id', render: (id: string) => id.slice(0, 8) + '...' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => {
        const m = STATUS_MAP[s] ?? { color: 'default', text: s }
        return <Tag color={m.color}>{m.text}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: RenderTask) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/render/${record.id}`)}
            data-testid={`view-btn-${record.id}`}
          >
            查看
          </Button>
          {record.status === 'done' && (
            <Button
              type="link"
              icon={<DownloadOutlined />}
              onClick={() => token && downloadRender(record.id, token)}
              data-testid={`dl-btn-${record.id}`}
            >
              下载
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>排版历史</Title>
      <Table
        dataSource={tasks}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
        data-testid="history-table"
      />
    </div>
  )
}
