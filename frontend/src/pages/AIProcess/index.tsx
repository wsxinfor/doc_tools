import { useState, useEffect } from 'react'
import { Button, Typography, Spin, Alert, Tree, Select, Card, Progress, Input, Space, message, Modal } from 'antd'
import { EditOutlined, DeleteOutlined, PlusOutlined, SearchOutlined, SaveOutlined } from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import { extractStructureAsync, getStructureTaskStatus, updateStructure, findAndReplace } from '../../api/aiProcess'
import { getDocument } from '../../api/documents'
import { useRenderStore } from '../../stores/renderStore'
import type { Section, AiStructure } from '../../types/api'
import FindReplaceModal from '../../components/FindReplaceModal'

const { Title, Text } = Typography

type StepStatus = 'idle' | 'loading' | 'done' | 'failed'

// 轮询间隔（毫秒）
const POLL_INTERVAL = 3000
// 最大轮询次数（约 10 分钟）
const MAX_POLL_COUNT = 200

// 为每个节点生成唯一 ID
let nodeIdCounter = 0
const generateNodeId = () => `node_${++nodeIdCounter}`

// 递归为 nodes 添加 _id 字段
const addIdsToSections = (sections: Section[]): any[] => {
  return sections.map((section) => ({
    ...section,
    _id: generateNodeId(),
    children: section.children ? addIdsToSections(section.children) : [],
  }))
}

export default function AIProcessPage() {
  const { docId } = useParams<{ docId: string }>()
  const navigate = useNavigate()
  const {
    setDoc,
    setStructure,
    structure,
    editedStructure,
    docId: storeDocId,
    setIsExtracting,
    setEditedStructure,
    isEditing,
    setIsEditing,
    setDraftSaved,
    taskId: storeTaskId,
    setTaskId,
  } = useRenderStore()

  const [extractStatus, setExtractStatus] = useState<StepStatus>('idle')
  const [sections, setSections] = useState<Section[]>([])
  const [extractMsg, setExtractMsg] = useState('')
  const [docName, setDocName] = useState('')
  const [taskId, setTaskIdLocal] = useState<string | null>(null)
  const [pollCount, setPollCount] = useState(0)
  const [progress, setProgress] = useState(0)

  // 编辑相关状态
  const [findReplaceOpen, setFindReplaceOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  // 带有 _id 的 sections 数据
  const [sectionsWithIds, setSectionsWithIds] = useState<any[]>([])

  // 获取当前结构（优先使用 editedStructure）
  const currentStructure = editedStructure || structure
  const displaySections = currentStructure?.sections || sections
  const displayTitle = currentStructure?.title || docName

  // 初始化时为 sections 添加 ID
  useEffect(() => {
    if (displaySections.length > 0 && sectionsWithIds.length === 0) {
      setSectionsWithIds(addIdsToSections(displaySections))
    }
  }, [])

  // 同步 displaySections 变化时更新 sectionsWithIds
  useEffect(() => {
    if (displaySections.length > 0) {
      // 保留已有的 _id，只更新其他字段
      const syncIds = (existing: any[], updated: Section[]): any[] => {
        return updated.map((item, idx) => {
          const existingItem = existing[idx]
          return {
            ...item,
            _id: existingItem?._id || generateNodeId(),
            children: existingItem?.children
              ? syncIds(existingItem.children, item.children || [])
              : [],
          }
        })
      }
      setSectionsWithIds((prev) => {
        if (prev.length === 0) {
          return addIdsToSections(displaySections)
        }
        return syncIds(prev, displaySections)
      })
    }
  }, [displaySections])

  useEffect(() => {
    if (!docId) return

    // 如果 store 中已有该文档的识别结果，直接使用
    if (storeDocId === docId && (structure || editedStructure)) {
      setDocName(editedStructure?.title || structure?.title || docName)
      setExtractStatus('done')
      setIsExtracting(false)
      if (storeTaskId) {
        setTaskIdLocal(storeTaskId)
      }
      return
    }

    setExtractStatus('idle')
    setSections([])
    setTaskIdLocal(null)
    setPollCount(0)
    setProgress(0)
    setExtractMsg('')

    if (extractStatus === 'loading') {
      return
    }

    getDocument(docId)
      .then((doc) => {
        setDoc(doc.id, doc.filename)
        setDocName(doc.filename)
        setExtractStatus('loading')
        setIsExtracting(true)
        return extractStructureAsync(docId!)
      })
      .then((task) => {
        setTaskIdLocal(task.id)
        setTaskId(task.id)
        setPollCount(0)
        setProgress(10)
      })
      .catch((err) => {
        console.error('Create structure task error:', err)
        setExtractMsg('创建任务失败：' + (err.message || '未知错误'))
        setExtractStatus('failed')
        setIsExtracting(false)
      })

    return () => {
      setIsExtracting(false)
    }
  }, [docId, setIsExtracting])

  useEffect(() => {
    if (!taskId || extractStatus !== 'loading') return

    const pollTaskStatus = () => {
      if (pollCount >= MAX_POLL_COUNT) {
        setExtractMsg('任务超时，请重试')
        setExtractStatus('failed')
        setIsExtracting(false)
        return
      }

      getStructureTaskStatus(taskId)
        .then((task) => {
          setPollCount((c) => c + 1)
          setProgress((p) => Math.min(p + 2, 90))

          if (task.status === 'done') {
            setProgress(100)
            const sectionsData = task.ai_structure?.sections ?? []
            const title = task.ai_structure?.title || docName
            const structureData = { title, sections: sectionsData }

            setStructure(structureData)
            if (task.edited_structure) {
              setEditedStructure(task.edited_structure as AiStructure)
            }

            setExtractStatus('done')
            setIsExtracting(false)
          } else if (task.status === 'failed') {
            setExtractMsg(task.error_message || '任务失败，请重试')
            setExtractStatus('failed')
            setIsExtracting(false)
          }
        })
        .catch((err) => {
          console.error('Poll task status error:', err)
          setExtractMsg('查询任务状态失败：' + (err.message || '未知错误'))
          setExtractStatus('failed')
          setIsExtracting(false)
        })
    }

    pollTaskStatus()
    const intervalId = setInterval(pollTaskStatus, POLL_INTERVAL)

    return () => {
      clearInterval(intervalId)
    }
  }, [taskId, extractStatus, docName, setStructure, setIsExtracting])

  const updateSectionLevel = (id: string, newLevel: number) => {
    const updateLevel = (items: any[]): any[] =>
      items.map((item) => {
        if (item._id === id) {
          if (newLevel === 0 && item.paragraph_type === 'heading') {
            return { ...item, level: 0, paragraph_type: 'body' }
          }
          if (newLevel > 0 && item.paragraph_type === 'body') {
            return { ...item, level: newLevel, paragraph_type: 'heading' }
          }
          return { ...item, level: newLevel }
        }
        return {
          ...item,
          children: item.children ? updateLevel(item.children) : [],
        }
      })

    const newSections = updateLevel(sectionsWithIds)
    setSectionsWithIds(newSections)
    const newStructure = { title: displayTitle, sections: newSections }
    setEditedStructure(newStructure)
    setDraftSaved(false)
  }

  const startEditing = (id: string, value: string) => {
    setEditingId(id)
    setEditValue(value)
  }

  const saveEditing = () => {
    const updateText = (items: any[]): any[] =>
      items.map((item) => {
        if (item._id === editingId) {
          return { ...item, text: editValue }
        }
        return {
          ...item,
          children: item.children ? updateText(item.children) : [],
        }
      })

    const newSections = updateText(sectionsWithIds)
    setSectionsWithIds(newSections)
    const newStructure = { title: displayTitle, sections: newSections }
    setEditedStructure(newStructure)
    setDraftSaved(false)
    setEditingId(null)
    setEditValue('')
  }

  const deleteSection = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这一行吗？',
      onOk: () => {
        const deleteItem = (items: any[]): any[] =>
          items.filter((item) => {
            if (item._id === id) {
              return false
            }
            if (item.children && item.children.length > 0) {
              item.children = deleteItem(item.children)
            }
            return true
          })

        const newSections = deleteItem(sectionsWithIds)
        setSectionsWithIds(newSections)
        const newStructure = { title: displayTitle, sections: newSections }
        setEditedStructure(newStructure)
        setDraftSaved(false)
      },
    })
  }

  const insertSectionAfter = (id: string) => {
    const newItem: Section & { _id: string } = {
      _id: generateNodeId(),
      level: 0,
      text: '新段落',
      paragraph_type: 'body',
      children: [],
    }

    const insertItem = (items: any[]): any[] =>
      items.flatMap((item) => {
        if (item._id === id) {
          return [item, newItem]
        }
        if (item.children && item.children.length > 0) {
          return { ...item, children: insertItem(item.children) }
        }
        return [item]
      })

    const newSections = insertItem(sectionsWithIds)
    setSectionsWithIds(newSections)
    const newStructure = { title: displayTitle, sections: newSections }
    setEditedStructure(newStructure)
    setDraftSaved(false)
  }

  const handleSaveDraft = async () => {
    if (!taskId) {
      message.error('任务 ID 不存在')
      return
    }

    try {
      const sectionsWithoutIds = sectionsWithIds.map((s) => {
        const { _id, ...rest } = s
        return rest
      })
      await updateStructure(taskId, sectionsWithoutIds, editedStructure?.title)
      setDraftSaved(true)
      message.success('草稿已保存')
    } catch (error) {
      console.error('Save draft error:', error)
      message.error('保存失败，请重试')
    }
  }

  const handleFindReplace = async (
    find: string,
    replace: string,
    caseSensitive: boolean,
    replaceAll: boolean,
  ): Promise<number> => {
    if (!taskId) {
      throw new Error('任务 ID 不存在')
    }

    const result = await findAndReplace(taskId, find, replace, caseSensitive, replaceAll)
    const task = await getStructureTaskStatus(taskId)
    if (task.edited_structure) {
      setEditedStructure(task.edited_structure as AiStructure)
    }
    setDraftSaved(false)
    return result.count
  }

  const handleConfirmStructure = () => {
    const finalStructure = editedStructure || structure || { title: docName, sections: [] }
    setStructure(finalStructure)
    navigate('/render/new')
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>AI 结构识别 - {docName}</Title>
        {extractStatus === 'done' && (
          <Space>
            <Button icon={<SearchOutlined />} onClick={() => setFindReplaceOpen(true)}>
              查找替换
            </Button>
            <Button
              type={isEditing ? 'primary' : 'default'}
              icon={<EditOutlined />}
              onClick={() => setIsEditing(!isEditing)}
            >
              {isEditing ? '完成编辑' : '编辑模式'}
            </Button>
            {isEditing && (
              <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveDraft}>
                保存草稿
              </Button>
            )}
            <Button type="primary" onClick={handleConfirmStructure}>
              确认结构，进入排版
            </Button>
          </Space>
        )}
      </div>

      <Card>
        {extractStatus === 'loading' && (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>AI 正在识别文档结构（标题/表格/图片）...</div>
            <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
              大文档（50 页 +）可能需要 2-5 分钟，请耐心等待
            </div>
            <Progress
              percent={progress}
              status="active"
              style={{ marginTop: 24, maxWidth: 300, margin: '24px auto 0' }}
              strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
            />
            <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
              已等待 {Math.floor(pollCount * POLL_INTERVAL / 1000)} 秒
            </div>
          </div>
        )}
        {extractStatus === 'failed' && (
          <>
            <Alert type="warning" message={extractMsg} style={{ marginBottom: 16 }} />
            <div style={{ marginTop: 16, textAlign: 'right' }}>
              <Button onClick={() => navigate(-1)}>返回</Button>
              <Button type="primary" onClick={() => window.location.reload()} style={{ marginLeft: 8 }}>
                重试
              </Button>
            </div>
          </>
        )}
        {extractStatus === 'done' && (
          <>
            {isEditing && (
              <Alert
                type="info"
                message="编辑模式：点击文本即可编辑，可删除/插入行，完成后点击保存草稿或确认结构"
                style={{ marginBottom: 16 }}
                showIcon
              />
            )}
            <Title level={5}>
              识别出的结构 {isEditing ? '（可调整标题层级和编辑内容）' : '（可调整标题层级）'}
            </Title>
            {displaySections.length === 0 ? (
              <Text type="secondary">未识别到内容，请重试</Text>
            ) : (
              <div style={{ maxHeight: 500, overflow: 'auto', border: '1px solid #d9d9d9', padding: 16 }}>
                <Tree
                  defaultExpandAll
                  treeData={renderTreeData(sectionsWithIds)}
                  style={{ fontSize: 14 }}
                />
              </div>
            )}
            {!isEditing && (
              <div style={{ marginTop: 16, textAlign: 'right' }}>
                <Button type="primary" onClick={handleConfirmStructure}>
                  确认结构，进入排版
                </Button>
              </div>
            )}
          </>
        )}
      </Card>

      <FindReplaceModal
        open={findReplaceOpen}
        onClose={() => setFindReplaceOpen(false)}
        onFindReplace={handleFindReplace}
      />
    </div>
  )

  function renderTreeData(items: any[], parentKey: string = ''): object[] {
    if (!items || items.length === 0) return []
    return items.map((item) => {
      const fullKey = parentKey ? `${parentKey}-${item._id}` : item._id
      const isCurrentEditing = editingId === item._id

      // 图片节点
      if (item.paragraph_type === 'image') {
        return {
          key: fullKey,
          title: (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
              <span style={{ color: '#999', fontSize: 12 }}>
                📷 图片：{item.image_path?.split('/').pop() || '未知'}
              </span>
              {isEditing && (
                <Space size={4}>
                  <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => deleteSection(item._id)} />
                </Space>
              )}
            </div>
          ),
        }
      }

      // 表格节点
      if (item.paragraph_type === 'table') {
        const rows = item.table_data?.rows || []
        return {
          key: fullKey,
          title: (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
              <span style={{ color: '#1890ff', fontSize: 12 }}>
                📊 表格：{rows.length} 行 x {rows[0]?.length || 0} 列
              </span>
              {isEditing && (
                <Space size={4}>
                  <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => deleteSection(item._id)} />
                </Space>
              )}
            </div>
          ),
        }
      }

      // 标题节点
      if (item.paragraph_type === 'heading') {
        return {
          key: fullKey,
          title: (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', flexWrap: 'wrap' }}>
              {!isEditing ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Select
                    size="small"
                    value={item.level}
                    onChange={(v: number) => updateSectionLevel(item._id, v)}
                    options={[
                      { label: '正文', value: 0 },
                      { label: 'H1', value: 1 },
                      { label: 'H2', value: 2 },
                      { label: 'H3', value: 3 },
                      { label: 'H4', value: 4 },
                    ]}
                    style={{ width: 64 }}
                  />
                  <Text>{item.text}</Text>
                </span>
              ) : isCurrentEditing ? (
                <Space size={4}>
                  <Input
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    style={{ width: 300 }}
                    onPressEnter={saveEditing}
                    onBlur={saveEditing}
                    autoFocus
                  />
                  <Select
                    size="small"
                    value={item.level}
                    onChange={(v: number) => updateSectionLevel(item._id, v)}
                    options={[
                      { label: '正文', value: 0 },
                      { label: 'H1', value: 1 },
                      { label: 'H2', value: 2 },
                      { label: 'H3', value: 3 },
                      { label: 'H4', value: 4 },
                    ]}
                    style={{ width: 64 }}
                  />
                  <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => deleteSection(item._id)} />
                </Space>
              ) : (
                <Space size={4}>
                  <Select
                    size="small"
                    value={item.level}
                    onChange={(v: number) => updateSectionLevel(item._id, v)}
                    options={[
                      { label: '正文', value: 0 },
                      { label: 'H1', value: 1 },
                      { label: 'H2', value: 2 },
                      { label: 'H3', value: 3 },
                      { label: 'H4', value: 4 },
                    ]}
                    style={{ width: 64 }}
                  />
                  <Text
                    onClick={() => startEditing(item._id, item.text || '')}
                    style={{ cursor: 'pointer', borderBottom: '1px dashed #999' }}
                  >
                    {item.text}
                  </Text>
                  <Button type="text" size="small" icon={<EditOutlined />} onClick={() => startEditing(item._id, item.text || '')} />
                  <Button type="text" size="small" icon={<PlusOutlined />} onClick={() => insertSectionAfter(item._id)} />
                  <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => deleteSection(item._id)} />
                </Space>
              )}
            </div>
          ),
          children: item.children && item.children.length > 0 ? renderTreeData(item.children, fullKey) : undefined,
        }
      }

      // 正文节点
      return {
        key: fullKey,
        title: (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', flexWrap: 'wrap' }}>
            {!isEditing ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Select
                  size="small"
                  value={0}
                  onChange={(v: number) => updateSectionLevel(item._id, v)}
                  options={[
                    { label: '正文', value: 0 },
                    { label: 'H1', value: 1 },
                    { label: 'H2', value: 2 },
                    { label: 'H3', value: 3 },
                    { label: 'H4', value: 4 },
                  ]}
                  style={{ width: 64 }}
                />
                <Text style={{ color: '#666', fontSize: 12 }}>
                  {item.text?.length > 50 ? item.text.slice(0, 50) + '…' : item.text}
                </Text>
              </span>
            ) : isCurrentEditing ? (
              <Space size={4}>
                <Input
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  style={{ width: 300 }}
                  onPressEnter={saveEditing}
                  onBlur={saveEditing}
                  autoFocus
                />
                <Select
                  size="small"
                  value={0}
                  onChange={(v: number) => updateSectionLevel(item._id, v)}
                  options={[
                    { label: '正文', value: 0 },
                    { label: 'H1', value: 1 },
                    { label: 'H2', value: 2 },
                    { label: 'H3', value: 3 },
                    { label: 'H4', value: 4 },
                  ]}
                  style={{ width: 64 }}
                />
                <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => deleteSection(item._id)} />
              </Space>
            ) : (
              <Space size={4}>
                <Select
                  size="small"
                  value={0}
                  onChange={(v: number) => updateSectionLevel(item._id, v)}
                  options={[
                    { label: '正文', value: 0 },
                    { label: 'H1', value: 1 },
                    { label: 'H2', value: 2 },
                    { label: 'H3', value: 3 },
                    { label: 'H4', value: 4 },
                  ]}
                  style={{ width: 64 }}
                />
                <Text
                  onClick={() => startEditing(item._id, item.text || '')}
                  style={{ cursor: 'pointer', borderBottom: '1px dashed #999', color: '#666', fontSize: 12 }}
                >
                  {item.text?.length > 50 ? item.text.slice(0, 50) + '…' : item.text}
                </Text>
                <Button type="text" size="small" icon={<EditOutlined />} onClick={() => startEditing(item._id, item.text || '')} />
                <Button type="text" size="small" icon={<PlusOutlined />} onClick={() => insertSectionAfter(item._id)} />
                <Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={() => deleteSection(item._id)} />
              </Space>
            )}
          </div>
        ),
      }
    })
  }
}
