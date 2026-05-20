import { Card, Button, Typography, Row, Col, Tag, message, Popconfirm, Empty } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { getTemplates, deleteTemplate } from '../../api/templates'
import type { Template } from '../../types/api'
import type { AxiosError } from 'axios'
import './styles.css'

const { Title, Text } = Typography

export default function TemplatesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: templates = [], isLoading, error } = useQuery({
    queryKey: ['templates'],
    queryFn: getTemplates,
    retry: false,
  })

  if (error) {
    const axiosErr = error as AxiosError<{ message?: string }>
    const errorMsg = axiosErr.response?.data?.message || axiosErr.message || '加载失败'
    if (axiosErr.response?.status === 401) {
      message.error('登录已过期，请重新登录')
    } else {
      message.error(errorMsg)
    }
    return <Empty description={errorMsg} />
  }

  const deleteMutation = useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      message.success('删除成功')
    },
    onError: (err: AxiosError<{ message?: string }>) => {
      message.error(err.response?.data?.message ?? '删除失败')
    },
  })

  if (isLoading) return null

  return (
    <div className="templates-page">
      <div className="page-header">
        <Title level={4} className="page-title">
          模板管理
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/templates/new')}
          data-testid="new-template-btn"
        >
          新建模板
        </Button>
      </div>

      {templates.length === 0 ? (
        <Empty description="暂无模板，点击「新建模板」创建" className="templates-empty" />
      ) : (
        <Row gutter={[16, 16]} className="templates-grid">
          {templates.map((tmpl: Template) => (
            <Col key={tmpl.id} xs={24} sm={12} md={8} lg={6}>
              <Card
                title={tmpl.name}
                className="template-card"
                extra={<Tag className="template-tag">模板</Tag>}
                actions={[
                  <EditOutlined
                    key="edit"
                    onClick={() => navigate(`/templates/${tmpl.id}/edit`)}
                    data-testid={`edit-tmpl-${tmpl.id}`}
                  />,
                  <Popconfirm
                    key="delete"
                    title="确认删除此模板？"
                    onConfirm={() => deleteMutation.mutate(tmpl.id)}
                    okText="删除"
                    cancelText="取消"
                  >
                    <DeleteOutlined style={{ color: '#ff4d4f' }} data-testid={`delete-tmpl-${tmpl.id}`} />
                  </Popconfirm>,
                ]}
              >
                {tmpl.description && <Text type="secondary" className="template-description">{tmpl.description}</Text>}
                <div className="template-date">
                  <Text type="secondary" className="template-date-text">
                    {dayjs(tmpl.created_at).format('YYYY-MM-DD')}
                  </Text>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  )
}
