import { Modal } from 'antd'

interface Props {
  open: boolean
  title?: string
  content: string
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
}

export default function ConfirmModal({ open, title = '确认删除', content, onConfirm, onCancel, loading }: Props) {
  return (
    <Modal
      open={open}
      title={title}
      okText="确认"
      cancelText="取消"
      okButtonProps={{ danger: true, loading }}
      onOk={onConfirm}
      onCancel={onCancel}
    >
      <p>{content}</p>
    </Modal>
  )
}
