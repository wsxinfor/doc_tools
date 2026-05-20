import { Select } from 'antd'
import { FONT_SIZE_MAP, ptToLabel } from './fontSizes'

interface Props {
  /** 存储值：pt 数值 */
  value?: number
  onChange?: (pt: number) => void
  style?: React.CSSProperties
}

export default function FontSizePicker({ value, onChange, style }: Props) {
  const selectValue = ptToLabel(value)

  const handleChange = (label: string) => {
    const found = FONT_SIZE_MAP.find((item) => item.label === label)
    if (found) onChange?.(found.pt)
  }

  return (
    <Select
      value={selectValue}
      onChange={handleChange}
      style={{ width: 100, ...style }}
      options={FONT_SIZE_MAP.map((item) => ({
        label: `${item.label}（${item.pt}pt）`,
        value: item.label,
      }))}
      placeholder="字号"
    />
  )
}
