<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">机场地面保障调度平台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向机场机坪运行的航班保障、机位资源、廊桥对接、除冰加注、行李装卸与保障结算的一体化地面调度后台。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.scope }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'

const store = useSessionStore()

const navItems = [{ label: "运营概览", path: "/" }, { label: "航班计划", path: "/flight" }, { label: "机位资源", path: "/stand" }, { label: "机坪巡查", path: "/apron" }, { label: "廊桥对接", path: "/bridge" }, { label: "除冰作业", path: "/deicing" }, { label: "航油加注", path: "/fueling" }, { label: "行李装卸", path: "/baggage" }, { label: "货邮装载", path: "/cargo" }, { label: "航空配餐", path: "/catering" }, { label: "摆渡接送", path: "/shuttle" }, { label: "航空器牵引", path: "/towing" }, { label: "载重平衡", path: "/loadsheet" }, { label: "通行证件", path: "/permit" }, { label: "保障车辆", path: "/gse" }, { label: "安全监察", path: "/safety" }, { label: "保障协议", path: "/agreement" }, { label: "保障结算", path: "/settlement" }, { label: "资质培训", path: "/training" }]
</script>
