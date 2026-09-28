import { defineStore } from 'pinia'

export interface OperatorAccount {
  id: string
  name: string
  areas: string[] | null  // null 表示可管全部通行区域
}

// 与后端 app/accounts.py 的内置值班账号保持一致
export const OPERATOR_ACCOUNTS: OperatorAccount[] = [
  { id: 'admin', name: '值班管理员', areas: null },
  { id: 'terminal', name: '航站楼区证件专员', areas: ['航站楼'] },
  { id: 'apron', name: '机坪区证件专员', areas: ['机坪'] },
]

export function scopeLabel(areas: string[] | null): string {
  return areas === null ? '全部通行区域' : areas.join('、')
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    operatorId: 'admin',
    operator: '值班管理员',
    shiftLabel: '白班 08:00-20:00',
    scope: '机场地面保障调度平台',
  }),
  getters: {
    canOperate: (state) => state.operator.length > 0,
    account(state): OperatorAccount {
      return OPERATOR_ACCOUNTS.find((item) => item.id === state.operatorId) ?? OPERATOR_ACCOUNTS[0]
    },
    areas: (state): string[] | null => {
      const current = OPERATOR_ACCOUNTS.find((item) => item.id === state.operatorId)
      return current ? current.areas : null
    },
  },
  actions: {
    switchOperator(operatorId: string) {
      const target = OPERATOR_ACCOUNTS.find((item) => item.id === operatorId)
      if (!target) {
        return
      }
      this.operatorId = target.id
      this.operator = target.name
      this.scope = scopeLabel(target.areas)
    },
    canManageArea(area: unknown): boolean {
      if (this.areas === null) {
        return true
      }
      return this.areas.includes(String(area ?? '').trim())
    },
    setShift(label: string) {
      this.shiftLabel = label
    },
  },
})
