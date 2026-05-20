import { Select } from 'antd'

const CN_FONTS = ['宋体', '黑体', '微软雅黑', '仿宋', '楷体', '方正书宋']
const EN_FONTS = ['Times New Roman', 'Arial', 'Calibri', 'Helvetica', 'Georgia', 'Verdana']

interface Props {
  value?: string
  onChange?: (v: string) => void
  type?: 'cn' | 'en' | 'all'
}

export default function FontPicker({ value, onChange, type = 'all' }: Props) {
  const fonts =
    type === 'cn' ? CN_FONTS : type === 'en' ? EN_FONTS : [...CN_FONTS, ...EN_FONTS]
  return (
    <Select
      value={value}
      onChange={onChange}
      style={{ width: 180 }}
      options={fonts.map((f) => ({ label: f, value: f }))}
    />
  )
}
