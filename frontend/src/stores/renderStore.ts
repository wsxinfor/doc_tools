import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { AiStructure } from '../types/api'

interface RenderFlowState {
  docId: string | null
  docName: string | null
  cleanedText: string | null
  structure: AiStructure | null
  editedStructure: AiStructure | null  // 用户编辑后的结构
  templateId: string | null
  isExtracting: boolean // 标记是否正在提取结构（不持久化）
  isEditing: boolean // 标记是否处于编辑模式
  draftSaved: boolean // 标记草稿是否已保存
  taskId: string | null // 结构识别任务 ID
  setDoc: (id: string, name: string) => void
  setCleanedText: (text: string) => void
  setStructure: (s: AiStructure) => void
  setEditedStructure: (s: AiStructure) => void
  setTemplateId: (id: string) => void
  setIsExtracting: (v: boolean) => void
  setIsEditing: (v: boolean) => void
  setDraftSaved: (v: boolean) => void
  setTaskId: (id: string) => void
  reset: () => void
}

export const useRenderStore = create<RenderFlowState>()(
  persist(
    (set) => ({
      docId: null,
      docName: null,
      cleanedText: null,
      structure: null,
      editedStructure: null,
      templateId: null,
      isExtracting: false,
      isEditing: false,
      draftSaved: false,
      taskId: null,
      setDoc: (id, name) => set({ docId: id, docName: name }),
      setCleanedText: (text) => set({ cleanedText: text }),
      setStructure: (s) => set({ structure: s }),
      setEditedStructure: (s) => set({ editedStructure: s }),
      setTemplateId: (id) => set({ templateId: id }),
      setIsExtracting: (v) => set({ isExtracting: v }),
      setIsEditing: (v) => set({ isEditing: v }),
      setDraftSaved: (v) => set({ draftSaved: v }),
      setTaskId: (id) => set({ taskId: id }),
      reset: () => set({
        docId: null,
        docName: null,
        cleanedText: null,
        structure: null,
        editedStructure: null,
        templateId: null,
        isExtracting: false,
        isEditing: false,
        draftSaved: false,
        taskId: null,
      }),
    }),
    {
      name: 'render-flow',
      storage: createJSONStorage(() => sessionStorage),
      // 只持久化部分状态，isExtracting/isEditing/draftSaved 不持久化
      partialize: (state) => ({
        docId: state.docId,
        docName: state.docName,
        cleanedText: state.cleanedText,
        structure: state.structure,
        editedStructure: state.editedStructure,
        templateId: state.templateId,
        taskId: state.taskId,
      }),
    },
  ),
)
