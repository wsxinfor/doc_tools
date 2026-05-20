import { useState } from 'react'
import {
  Steps, Button, Form, Input, Select, DatePicker, Card, Typography,
  Radio, Space, message, Spin,
} from 'antd'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { useQuery } from '@tanstack/react-query'
import { getTemplates } from '../../api/templates'
import { createRenderTask } from '../../api/render'
import { useRenderStore } from '../../stores/renderStore'
import type { AxiosError } from 'axios'

const { Title, Text } = Typography

export default function RenderCreatePage() {
  const navigate = useNavigate()
  const { docId, docName, cleanedText, structure, templateId, setTemplateId } = useRenderStore()
  const [currentStep, setCurrentStep] = useState(0)
  const [coverForm] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  const { data: templates = [], isLoading: templatesLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: getTemplates,
  })

  const handleSelectTemplate = (id: string) => {
    setTemplateId(id)
    setCurrentStep(2)
  }

  const handleSubmit = async () => {
    try {
      await coverForm.validateFields()
    } catch {
      return
    }
    if (!docId || !structure || !templateId) {
      message.error('缺少必要信息，请返回重新操作')
      return
    }
    const values = coverForm.getFieldsValue() as {
      client_name: string
      project_name: string
      doc_version: string
      date: dayjs.Dayjs
    }
    setSubmitting(true)
    try {
      const task = await createRenderTask({
        document_id: docId,
        template_id: templateId,
        ai_clean_result: cleanedText || '',  // 已废弃，传空字符串
        ai_structure: structure,
        render_params: {
          client_name: values.client_name,
          project_name: values.project_name,
          doc_version: values.doc_version,
          date: values.date ? values.date.format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD'),
        },
      })
      navigate(`/render/${task.id}`)
    } catch (err) {
      const axiosErr = err as AxiosError<{ message?: string }>
      message.error(axiosErr.response?.data?.message ?? '创建排版任务失败')
    } finally {
      setSubmitting(false)
    }
  }

  const steps = [
    {
      title: '确认文档与 AI 结果',
      content: (
        <Card>
          {docId ? (
            <div>
              <p><Text strong>文档：</Text><Text>{docName}</Text></p>
              <p><Text strong>AI 识别结构：</Text></p>
              <div
                style={{
                  background: '#fafafa',
                  padding: 12,
                  borderRadius: 6,
                  maxHeight: 200,
                  overflow: 'auto',
                  fontSize: 13,
                  marginBottom: 16,
                }}
              >
                {structure?.sections?.filter(s => s.paragraph_type === 'heading').length ?? 0} 个标题，
                {structure?.sections?.filter(s => s.paragraph_type === 'table').length ?? 0} 个表格，
                {structure?.sections?.filter(s => s.paragraph_type === 'image').length ?? 0} 张图片
              </div>
              <p><Text strong>章节数：</Text><Text>{structure?.sections?.filter(s => s.paragraph_type === 'heading').length ?? 0} 个标题</Text></p>
            </div>
          ) : (
            <Text type="secondary">未选择文档，请先通过文档列表进入 AI 处理流程</Text>
          )}
          <div style={{ textAlign: 'right', marginTop: 16 }}>
            <Button
              type="primary"
              disabled={!docId || !structure}
              onClick={() => setCurrentStep(1)}
              data-testid="step1-next-btn"
            >
              下一步：选择模板
            </Button>
          </div>
        </Card>
      ),
    },
    {
      title: '选择模板',
      content: (
        <Card>
          {templatesLoading ? (
            <Spin />
          ) : (
            <Radio.Group value={templateId} style={{ width: '100%' }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                {templates.map((t) => (
                  <Radio
                    key={t.id}
                    value={t.id}
                    onClick={() => handleSelectTemplate(t.id)}
                    data-testid={`select-tmpl-${t.id}`}
                    style={{ width: '100%', padding: '8px 0' }}
                  >
                    <Text strong>{t.name}</Text>
                    {t.description && <Text type="secondary" style={{ marginLeft: 8 }}>{t.description}</Text>}
                  </Radio>
                ))}
              </Space>
            </Radio.Group>
          )}
        </Card>
      ),
    },
    {
      title: '填写封面信息',
      content: (
        <Card>
          <Form
            form={coverForm}
            layout="vertical"
            initialValues={{
              date: dayjs(),
            }}
          >
            <Form.Item name="client_name" label="客户公司名称" rules={[{ required: true, message: '请输入客户公司名称' }]}>
              <Input data-testid="client-name-input" />
            </Form.Item>
            <Form.Item name="project_name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
              <Input data-testid="project-name-input" />
            </Form.Item>
            <Form.Item name="doc_version" label="文档版本" rules={[{ required: true, message: '请输入版本' }]} initialValue="v1.0">
              <Select
                options={['v1.0', 'v1.1', 'v2.0', 'v3.0'].map((v) => ({ label: v, value: v }))}
                style={{ width: 160 }}
              />
            </Form.Item>
            <Form.Item name="date" label="日期">
              <DatePicker format="YYYY-MM-DD" style={{ width: 200 }} />
            </Form.Item>
          </Form>
          <div style={{ textAlign: 'right', marginTop: 16 }}>
            <Button
              type="primary"
              onClick={handleSubmit}
              loading={submitting}
              data-testid="start-render-btn"
            >
              开始排版
            </Button>
          </div>
        </Card>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>创建排版任务</Title>
      <Steps
        current={currentStep}
        items={steps.map((s) => ({ title: s.title }))}
        style={{ marginBottom: 32 }}
      />
      {steps[currentStep].content}
    </div>
  )
}
