import { useEffect } from 'react'
import { Form, Input, Button, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { login } from '../../api/auth'
import type { AxiosError } from 'axios'
import './styles.css'
import '../../styles/global.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const { token, setAuth } = useAuthStore()

  useEffect(() => {
    if (token) navigate('/documents', { replace: true })
  }, [token, navigate])

  const onFinish = async (values: { username: string; password: string }) => {
    try {
      const resp = await login(values.username, values.password)
      setAuth(resp.user, resp.access_token)
      navigate('/documents', { replace: true })
    } catch (err) {
      const axiosErr = err as AxiosError<{ message?: string }>
      message.error(axiosErr.response?.data?.message ?? '登录失败，请重试')
    }
  }

  return (
    <div className="login-layout">
      {/* 左侧品牌区 */}
      <div className="login-brand">
        {/* SVG 平行线条 Logo */}
        <svg className="brand-logo" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="8" y1="12" x2="72" y2="12" stroke="currentColor" strokeWidth="0.8" opacity="0.2" />
          <line x1="8" y1="22" x2="72" y2="22" stroke="currentColor" strokeWidth="0.8" opacity="0.2" />
          <line x1="8" y1="32" x2="72" y2="32" stroke="currentColor" strokeWidth="0.8" opacity="0.2" />
          <line x1="8" y1="42" x2="72" y2="42" stroke="currentColor" strokeWidth="0.8" opacity="0.2" />
          <line x1="8" y1="52" x2="72" y2="52" stroke="currentColor" strokeWidth="0.8" opacity="0.2" />
          <line x1="8" y1="62" x2="72" y2="62" stroke="currentColor" strokeWidth="0.8" opacity="0.2" />
          <line x1="8" y1="72" x2="72" y2="72" stroke="currentColor" strokeWidth="0.8" opacity="0.2" />
        </svg>
        <h1 className="brand-name">DocFormat</h1>
        <p className="brand-sub">智能文档排版工具</p>
      </div>

      {/* 右侧表单区 */}
      <div className="login-form-area">
        <h2 className="form-title">欢迎登录</h2>
        <Form name="login" onFinish={onFinish} autoComplete="off" size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入用户名"
              data-testid="username"
              className="login-input"
            />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入密码"
              data-testid="password"
              className="login-input"
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block data-testid="login-btn" className="btn-login">
              登 录
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  )
}
