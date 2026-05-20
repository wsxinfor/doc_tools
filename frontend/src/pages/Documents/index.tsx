import { useState } from 'react'
import { Table, Button, Space, Tag, Typography, Upload, message, Popconfirm, Modal, Input, Tabs } from 'antd'
import { InboxOutlined, DeleteOutlined, RobotOutlined, UploadOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { getDocuments, uploadDocument, deleteDocument, createDocumentFromText } from '../../api/documents'
import type { Document } from '../../types/api'
import type { AxiosError } from 'axios'
import './styles.css'

const { Dragger } = Upload
const { Text } = Typography
const { TextArea } = Input

const MAX_SIZE_BYTES = 20 * 1024 * 1024
const ALLOWED_TYPES = ['.docx', '.md']
const MAX_TEXT_LENGTH = 50000

export default function DocumentsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [uploading, setUploading] = useState(false)
  const [textModalVisible, setTextModalVisible] = useState(false)
  const [textInputMode, setTextInputMode] = useState<'file' | 'text'>('file')
  const [textContent, setTextContent] = useState('')
  const [textFilename, setTextFilename] = useState('')

  const { data: docs = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: getDocuments,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      message.success('删除成功')
    },
    onError: (err: AxiosError<{ message?: string }>) => {
      message.error(err.response?.data?.message ?? '删除失败')
    },
  })

  const handleUpload = async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_TYPES.includes(ext)) {
      message.error('仅支持 .docx 和 .md 格式')
      return false
    }
    if (file.size > MAX_SIZE_BYTES) {
      message.error('文件大小不能超过 20MB')
      return false
    }
    setUploading(true)
    try {
      await uploadDocument(file)
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      message.success('上传成功，可开始 AI 处理')
      setTextModalVisible(false)
    } catch (err) {
      const axiosErr = err as AxiosError<{ message?: string }>
      message.error(axiosErr.response?.data?.message ?? '上传失败')
    } finally {
      setUploading(false)
    }
    return false
  }

  const handleTextSubmit = async () => {
    if (!textContent.trim()) {
      message.error('请输入文本内容')
      return
    }
    if (textContent.length > MAX_TEXT_LENGTH) {
      message.error(`文本长度不能超过 ${MAX_TEXT_LENGTH} 字符`)
      return
    }
    if (!textFilename.trim()) {
      message.error('请输入文件名')
      return
    }

    setUploading(true)
    try {
      await createDocumentFromText(textFilename.trim(), textContent)
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      message.success('创建成功，可开始 AI 处理')
      setTextModalVisible(false)
      setTextContent('')
      setTextFilename('')
    } catch (err) {
      const axiosErr = err as AxiosError<{ message?: string }>
      message.error(axiosErr.response?.data?.message ?? '创建失败')
    } finally {
      setUploading(false)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const columns = [
    { title: '文件名', dataIndex: 'filename', key: 'filename' },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (t: string) => <Tag>{t.toUpperCase()}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (s: number) => formatSize(s),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Document) => (
        <Space>
          <Button
            type="link"
            icon={<RobotOutlined />}
            onClick={() => navigate(`/ai-process/${record.id}`)}
            data-testid={`ai-btn-${record.id}`}
          >
            AI 处理
          </Button>
          <Popconfirm
            title="确认删除此文档？"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="删除"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              data-testid={`delete-btn-${record.id}`}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="documents-page">
      <div className="page-header">
        <Typography.Title level={4} className="page-title">
          文档管理
        </Typography.Title>
        <Button
          type="primary"
          icon={<UploadOutlined />}
          onClick={() => {
            setTextModalVisible(true)
            setTextInputMode('file')
          }}
          data-testid="upload-btn"
        >
          上传文档
        </Button>
      </div>

      {/* 上传方式选择 Modal */}
      <Modal
        title="上传文档"
        open={textModalVisible}
        onCancel={() => {
          setTextModalVisible(false)
          setTextContent('')
          setTextFilename('')
        }}
        footer={null}
        className="upload-modal"
        width={800}
      >
        <Tabs
          activeKey={textInputMode}
          onChange={(v) => setTextInputMode(v as 'file' | 'text')}
          items={[
            {
              key: 'file',
              label: '文件上传',
              children: (
                <Dragger
                  id="upload-trigger"
                  beforeUpload={handleUpload}
                  showUploadList={false}
                  style={{ marginTop: 16 }}
                  accept=".docx,.md"
                >
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                  </p>
                  <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                  <p className="ant-upload-hint">
                    <Text type="secondary">支持 .docx 和 .md 格式，单文件不超过 20MB</Text>
                  </p>
                  {uploading && <Text type="secondary">上传中...</Text>}
                </Dragger>
              ),
            },
            {
              key: 'text',
              label: '粘贴文本',
              children: (
                <div style={{ marginTop: 16 }}>
                  <Input
                    placeholder="请输入文件名（如：我的文档.md）"
                    value={textFilename}
                    onChange={(e) => setTextFilename(e.target.value)}
                    style={{ marginBottom: 12 }}
                    maxLength={100}
                  />
                  <TextArea
                    placeholder="请粘贴文本内容，支持 Markdown 格式（自动检测）"
                    value={textContent}
                    onChange={(e) => setTextContent(e.target.value)}
                    rows={15}
                    maxLength={MAX_TEXT_LENGTH}
                    showCount
                  />
                  <div style={{ marginTop: 12, textAlign: 'right' }}>
                    <Text type="secondary" style={{ marginRight: 12 }}>
                      已输入 {textContent.length} / {MAX_TEXT_LENGTH} 字符
                    </Text>
                    <Button
                      type="primary"
                      onClick={handleTextSubmit}
                      loading={uploading}
                      disabled={!textContent.trim() || !textFilename.trim()}
                    >
                      创建文档
                    </Button>
                  </div>
                </div>
              ),
            },
          ]}
        />
      </Modal>

      <Table
        dataSource={docs}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 20 }}
        data-testid="documents-table"
      />
    </div>
  )
}
