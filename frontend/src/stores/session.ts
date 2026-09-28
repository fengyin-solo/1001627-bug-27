import { defineStore } from 'pinia'

export type AccessContext = {
  account: string
  /** null 表示可管理全部通行区域；数组中的区域只允许查看。 */
  managedAreas: string[] | null
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    operator: '国内机坪值班员',
    shiftLabel: '白班 08:00-20:00',
    scope: '国内机坪',
    managedAreas: ['国内机坪'] as string[] | null,
  }),
  getters: {
    canOperate: (state) => state.operator.length > 0,
    isRestricted: (state) => Array.isArray(state.managedAreas),
  },
  actions: {
    setShift(label: string) {
      this.shiftLabel = label
    },
  },
})
