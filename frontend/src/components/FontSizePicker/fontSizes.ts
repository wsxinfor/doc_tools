export const FONT_SIZE_MAP: { label: string; pt: number }[] = [
  { label: '初号', pt: 42 },
  { label: '小初', pt: 36 },
  { label: '一号', pt: 26 },
  { label: '小一', pt: 24 },
  { label: '二号', pt: 22 },
  { label: '小二', pt: 18 },
  { label: '三号', pt: 16 },
  { label: '小三', pt: 15 },
  { label: '四号', pt: 14 },
  { label: '小四', pt: 12 },
  { label: '五号', pt: 10.5 },
  { label: '小五', pt: 9 },
  { label: '六号', pt: 7.5 },
  { label: '小六', pt: 6.5 },
  { label: '七号', pt: 5.5 },
  { label: '八号', pt: 5 },
]

export function ptToLabel(pt: number | undefined): string | undefined {
  if (pt === undefined || pt === null) return undefined
  const found = FONT_SIZE_MAP.find((item) => Math.abs(item.pt - pt) < 0.01)
  return found ? found.label : `${pt}pt`
}
