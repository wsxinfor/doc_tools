import { Input } from 'antd'

interface Props {
  value?: string
  onChange?: (v: string) => void
}

export default function ColorPicker({ value = '#000000', onChange }: Props) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
      <input
        type="color"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        style={{ width: 36, height: 32, padding: 2, cursor: 'pointer', border: '1px solid #d9d9d9', borderRadius: 6 }}
      />
      <Input
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        style={{ width: 110 }}
        maxLength={7}
      />
    </span>
  )
}
