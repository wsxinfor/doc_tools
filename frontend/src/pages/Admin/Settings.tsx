import { useEffect, useState } from 'react'
import { Form, Radio, Input, Button, message, Typography, Card, Space, Alert } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { getAiSettings, updateAiSettings, testAiSettings } from '../../api/aiProcess'
import type { AxiosError } from 'axios'

const { Title, Text } = Typography

export default function AdminSettingsPage() {
  const [form] = Form.useForm()
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null)

  const { data: settings } = useQuery({
    queryKey: ['ai-settings'],
    queryFn: getAiSettings,
  })

  useEffect(() => {
    if (settings) {
      form.setFieldsValue({
        provider: settings.provider,
        model_url: settings.model_url,
        model_name: settings.model_name,
      })
    }
  }, [settings, form])

  const onFinish = async (values: {
    provider: 'qwen' | 'openai'
    api_key?: string
    model_url?: string
    model_name?: string
  }) => {
    if (!values.api_key) {
      message.warning('请输入 API Key')
      return
    }
    try {
      await updateAiSettings(
        values.provider,
        values.api_key,
        values.model_url ?? '',
        values.model_name ?? '',
      )
      message.success('保存成功')
      form.setFieldValue('api_key', '')
      setTestResult(null)
    } catch (err) {
      const axiosErr = err as AxiosError<{ message?: string }>
      message.error(axiosErr.response?.data?.message ?? '保存失败')
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const result = await testAiSettings()
      setTestResult(result)
      if (!result.ok) {
        message.error(result.message)
      } else {
        message.success(result.message)
      }
    } catch (err) {
      const axiosErr = err as AxiosError<{ message?: string }>
      const errMsg = axiosErr.response?.data?.message || '请求失败'
      setTestResult({ ok: false, message: errMsg })
      message.error(errMsg)
    } finally {
      setTesting(false)
    }
  }

  return (
    <div>
      <Title level={4}>系统设置</Title>
      <Card title="AI 服务配置" style={{ maxWidth: 560 }}>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="provider" label="AI 服务提供商" rules={[{ required: true }]}>
            <Radio.Group>
              <Radio value="qwen">通义千问</Radio>
              <Radio value="openai">OpenAI / 兼容接口</Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            name="model_url"
            label="模型地址（Base URL）"
            extra="留空使用默认地址；私有部署或代理时填写，例如 https://your-proxy.com/v1"
          >
            <Input placeholder="https://api.openai.com/v1" data-testid="model-url-input" allowClear />
          </Form.Item>

          <Form.Item
            name="model_name"
            label="模型名称"
            extra="留空使用默认：通义千问 → qwen-turbo，OpenAI → gpt-4o-mini"
          >
            <Input placeholder="例如 qwen-plus / gpt-4o / deepseek-chat" data-testid="model-name-input" allowClear />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            extra={settings?.has_api_key ? '已配置（输入新 Key 将覆盖原有配置）' : '尚未配置'}
          >
            <Input.Password placeholder="输入新的 API Key" data-testid="api-key-input" />
          </Form.Item>

          {testResult && (
            <Form.Item>
              <Alert
                type={testResult.ok ? 'success' : 'error'}
                icon={testResult.ok ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                message={
                  <Text>
                    {testResult.ok ? '连接成功' : '连接失败'}
                    {!testResult.ok && (
                      <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
                        {testResult.message}
                      </span>
                    )}
                  </Text>
                }
                showIcon
              />
            </Form.Item>
          )}

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" data-testid="save-settings-btn">
                保存配置
              </Button>
              <Button
                onClick={handleTest}
                loading={testing}
                data-testid="test-connection-btn"
              >
                测试连接
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
