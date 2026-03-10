# Vercel React Best Practices 技能应用核查

**技能来源**: `.agents/skills/vercel-react-best-practices/SKILL.md`、`AGENTS.md`  
**项目**: SmartChef 前端（React 18 + Vite + Ant Design，**非 Next.js**）  
**核查日期**: 2026-03-10

---

## 一、技能适用性说明

- 技能面向 **React 与 Next.js**；本项目为 **React + Vite SPA**，无 RSC、无 Server Actions、无 `next/dynamic`。
- 以下仅评估**适用于当前技术栈**的规则是否在项目中有体现；Next 专用条目不适用，标为 N/A。

---

## 二、规则类别核查结果

### 1. Eliminating Waterfalls（CRITICAL）


| 规则                           | 适用性           | 项目情况                                                                                                               |
| ---------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------ |
| async-parallel / Promise.all | 适用            | 部分页面已并行请求（如 Monitoring/Dashboard.jsx 中 `Promise.all([api.get('/monitoring/stats'), api.get('/monitoring/logs')])`） |
| async-defer-await            | 适用            | 未做专项审查；建议在数据加载路径中避免串行 await 导致瀑布                                                                                   |
| async-suspense-boundaries    | Next/React 18 | 项目未使用 Suspense 做数据流；可考虑对重数据列表使用 React.lazy + Suspense                                                              |
| async-api-routes             | Next          | N/A（无 API Routes）                                                                                                  |


**结论**: 部分应用（Dashboard 并行请求）；其余可加强「先发请求、后 await」与按需加载。

---

### 2. Bundle Size Optimization（CRITICAL）


| 规则                           | 适用性                        | 项目情况                                                                           |
| ---------------------------- | -------------------------- | ------------------------------------------------------------------------------ |
| bundle-barrel-imports        | 适用                         | 未做专项审查；Ant Design 通常按需引入（如 `import { Button } from 'antd'`），建议确认未从 `antd` 全量导入 |
| bundle-dynamic-imports       | 适用（Vite 支持 dynamic import） | 未发现对重组件（如图表、富文本）使用 `React.lazy`/动态 import                                      |
| bundle-defer-third-party     | 适用                         | 未发现对 analytics 等做 hydration 后加载                                                |
| bundle-conditional / preload | 适用                         | 未做专项实现                                                                         |


**结论**: 技能**未在项目中系统应用**；建议对大型页面或重型组件做动态 import 与按需加载。

---

### 3. Server-Side Performance（HIGH）


| 规则          | 适用性      | 项目情况        |
| ----------- | -------- | ----------- |
| server-* 全部 | Next/RSC | N/A（无服务端渲染） |


**结论**: N/A。

---

### 4. Client-Side Data Fetching（MEDIUM-HIGH）


| 规则                               | 适用性 | 项目情况                                              |
| -------------------------------- | --- | ------------------------------------------------- |
| client-swr-dedup                 | 适用  | 项目使用 axios + useEffect 拉数，**未使用 SWR**；多实例同接口会重复请求 |
| client-event-listeners / passive | 适用  | 未做专项审查                                            |
| client-localstorage-schema       | 适用  | 仅存 token（`smartchef_token`），未做版本与最小化 schema       |


**结论**: **未应用** SWR；localStorage 使用简单，可补充版本与 try/catch。

---

### 5. Re-render Optimization（MEDIUM）


| 规则                              | 适用性 | 项目情况                                     |
| ------------------------------- | --- | ---------------------------------------- |
| rerender-derived-state          | 适用  | 未做全量审查；建议派生状态在渲染时计算，避免 state + effect 同步 |
| rerender-memo / lazy-state-init | 适用  | 未发现对重列表或重计算使用 useMemo/useState(fn)       |
| rerender-functional-setstate    | 适用  | 建议在基于前序 state 更新时使用函数式 setState          |
| rerender-transitions            | 适用  | 未使用 startTransition                      |


**结论**: 技能**未系统应用**；建议在列表与表单页审查派生状态与 setState 形式。

---

### 6. Rendering Performance（MEDIUM）


| 规则                              | 适用性 | 项目情况                                  |
| ------------------------------- | --- | ------------------------------------- |
| rendering-content-visibility    | 适用  | 长列表（如意图列表、日志列表）未使用 content-visibility |
| rendering-conditional-render    | 适用  | 建议用三元代替 `count && <Tag>` 避免渲染 0       |
| rendering-usetransition-loading | 适用  | 未使用 useTransition 做加载态                |


**结论**: 未系统应用；长列表与条件渲染可逐步优化。

---

### 7. JavaScript Performance（LOW-MEDIUM）


| 规则                               | 适用性 | 项目情况                                        |
| -------------------------------- | --- | ------------------------------------------- |
| js-*（Map/Set、early exit、cache 等） | 适用  | 未做专项审查；建议在热点路径（如表格过滤、大列表查找）使用 Map/Set 与提前返回 |


**结论**: 未专项应用。

---

### 8. Advanced Patterns（LOW）


| 规则                          | 适用性 | 项目情况                      |
| --------------------------- | --- | ------------------------- |
| advanced-init-once          | 适用  | 未发现重复初始化；可确认全局 init 只执行一次 |
| advanced-event-handler-refs | 适用  | 未做专项应用                    |


**结论**: 未系统应用。

---

## 三、总体结论


| 维度      | 应用情况                                                                                   |
| ------- | -------------------------------------------------------------------------------------- |
| **已体现** | 少量：Dashboard 并行请求（Promise.all）、Ant Design 按需引用（若已配置）                                   |
| **未应用** | 多数：SWR、动态 import、content-visibility、useTransition、派生状态与 setState 规范、localStorage 版本与容错 |
| **不适用** | 所有 server-*、Next 专属（Suspense 数据流、API Routes、optimizePackageImports）                    |


**建议**:  

1. 将「Vercel React 技能」中**与 SPA 相关的条目**（client-*、rerender-*、rendering-*、bundle-*、js-*）纳入前端 Code Review 检查表，在迭代中逐步落地。
2. 优先考虑：**并行/按需请求**、**SWR 或等效去重**、**长列表 content-visibility 或虚拟列表**、**条件渲染用三元避免 0 渲染**。

