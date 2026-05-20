import { useState } from 'react'
import {
  Table, Button, Tag, Typography, Modal, Form,
  Input, Select, message, Popconfirm,
} from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { getUsers, createUser, toggleUser } from '../../api/auth'
import type { User } from '../../types/api'
import type { AxiosError } from 'axios'

const { Title } = Typography

export default function AdminUsersPage() {
  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  })

  const createMutation = useMutation({
    mutationFn: (data: { username: string; password: string; role: 'admin' | 'user' }) =>
      createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      message.success('创建成功')
      setModalOpen(false)
      form.resetFields()
    },
    onError: (err: AxiosError<{ message?: string }>) => {
      message.error(err.response?.data?.message ?? '创建失败')
    },
  })

  const toggleMutation = useMutation({
    mutationFn: toggleUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (err: AxiosError<{ message?: string }>) => {
      message.error(err.response?.data?.message ?? '操作失败')
    },
  })

  const handleCreate = async () => {
    try {
      await form.validateFields()
    } catch {
      return
    }
    const values = form.getFieldsValue() as { username: string; password: string; role: 'admin' | 'user' }
    createMutation.mutate(values)
  }

  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (r: string) => <Tag color={r === 'admin' ? 'gold' : 'blue'}>{r}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v: boolean) => <Tag color={v ? 'success' : 'error'}>{v ? '启用' : '停用'}</Tag>,
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
      render: (_: unknown, record: User) => (
        <Popconfirm
          title={`确认${record.is_active ? '停用' : '启用'}此用户？`}
          onConfirm={() => toggleMutation.mutate(record.id)}
          okText="确认"
          cancelText="取消"
        >
          <Button
            type="link"
            danger={record.is_active}
            data-testid={`toggle-btn-${record.id}`}
          >
            {record.is_active ? '停用' : '启用'}
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>用户管理</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalOpen(true)}
          data-testid="new-user-btn"
        >
          新建用户
        </Button>
      </div>

      <Table
        dataSource={users}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        data-testid="users-table"
      />

      <Modal
        open={modalOpen}
        title="新建用户"
        onOk={handleCreate}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        okText="创建"
        cancelText="取消"
        confirmLoading={createMutation.isPending}
        data-testid="create-user-modal"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{ required: true, min: 3, message: '用户名至少 3 个字符' }]}>
            <Input data-testid="new-username-input" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 8, message: '密码至少 8 个字符' }]}>
            <Input.Password data-testid="new-password-input" />
          </Form.Item>
          <Form.Item name="role" label="角色" initialValue="user">
            <Select options={[{ label: '普通用户', value: 'user' }, { label: '管理员', value: 'admin' }]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
