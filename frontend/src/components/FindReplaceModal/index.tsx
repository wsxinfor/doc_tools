import { useState } from 'react'
import { Modal, Input, Button, Checkbox, Typography } from 'antd'
import type { CheckboxChangeEvent } from 'antd/es/checkbox'

const { Text } = Typography

interface FindReplaceModalProps {
  open: boolean
  onClose: () => void
  onFindReplace: (find: string, replace: string, caseSensitive: boolean, replaceAll: boolean) => Promise<number>
}

export default function FindReplaceModal({
  open,
  onClose,
  onFindReplace,
}: FindReplaceModalProps) {
  const [findText, setFindText] = useState('')
  const [replaceText, setReplaceText] = useState('')
  const [caseSensitive, setCaseSensitive] = useState(false)
  const [replaceAll, setReplaceAll] = useState(true)
  const [loading, setLoading] = useState(false)
  const [lastResult, setLastResult] = useState<number | null>(null)

  const handleFindReplace = async () => {
    if (!findText) {
      return
    }

    setLoading(true)
    try {
      const count = await onFindReplace(findText, replaceText, caseSensitive, replaceAll)
      setLastResult(count)
    } catch (error) {
      console.error('Find-replace error:', error)
      setLastResult(-1)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setFindText('')
    setReplaceText('')
    setCaseSensitive(false)
    setReplaceAll(true)
    setLastResult(null)
    onClose()
  }

  return (
    <Modal
      title="查找和替换"
      open={open}
      onCancel={handleClose}
      footer={[
        <Button key="cancel" onClick={handleClose}>
          关闭
        </Button>,
        <Button
          key="execute"
          type="primary"
          loading={loading}
          onClick={handleFindReplace}
          disabled={!findText}
        >
          {replaceAll ? '全部替换' : '替换'}
        </Button>,
      ]}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <Text style={{ display: 'block', marginBottom: 8 }}>查找内容：</Text>
          <Input
            value={findText}
            onChange={(e) => setFindText(e.target.value)}
            placeholder="输入要查找的文本"
            onPressEnter={handleFindReplace}
            autoFocus
          />
        </div>

        <div>
          <Text style={{ display: 'block', marginBottom: 8 }}>替换为：</Text>
          <Input
            value={replaceText}
            onChange={(e) => setReplaceText(e.target.value)}
            placeholder="输入替换后的文本"
            onPressEnter={handleFindReplace}
          />
        </div>

        <div style={{ display: 'flex', gap: 16 }}>
          <Checkbox
            checked={caseSensitive}
            onChange={(e: CheckboxChangeEvent) => setCaseSensitive(e.target.checked)}
          >
            区分大小写
          </Checkbox>
          <Checkbox
            checked={replaceAll}
            onChange={(e: CheckboxChangeEvent) => setReplaceAll(e.target.checked)}
          >
            全部替换
          </Checkbox>
        </div>

        {lastResult !== null && (
          <div style={{ padding: '8px 12px', background: lastResult >= 0 ? '#f6ffed' : '#fff2f0', border: '1px solid #b7eb8f', borderRadius: 4 }}>
            <Text type={lastResult >= 0 ? 'success' : 'danger'}>
              {lastResult >= 0
                ? `已替换 ${lastResult} 处匹配`
                : '替换失败，请重试'}
            </Text>
          </div>
        )}
      </div>
    </Modal>
  )
}
