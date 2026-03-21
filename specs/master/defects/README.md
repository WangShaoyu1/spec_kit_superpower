# 缺陷管理

手动测试阶段的缺陷录入与闭环管理，作为项目规范的重要组成部分。

## feedback_1 迁移映射

| 缺陷 | 来源 |
|------|------|
| D001 | test/chat 接口报错（LLM 500、csrf token） |
| D002 | UI 风格、滚动条 |
| D003 | 弹窗点击 mask 关闭 |
| D004 | Input clearable |
| D005 | 接口响应格式 code/data/msg |
| D006 | 列表分页 |
| D007 | intent-libraries 404 |
| D008 | 会话编辑删除 |
| D009 | 对话方案状态字段逻辑 |
| D010 | 闲聊人设列表编辑 |
| D011 | 批量测试两步流、Excel、结论弹窗 |
| D012 | 指令库一级路由 |
| D013 | 用户管理角色与能力 |

## 目录结构

```
specs/master/defects/
  INDEX.md            # 状态表（扫描时自动生成，勿手动编辑）
  _template.md        # 缺陷模板（复制后重命名）
  images/             # 缺陷截图（命名：D001-1.png, D001-2.png）
  D001.md
  D002.md
  ...
```

## 新增缺陷

1. 复制 `_template.md`
2. 重命名为 `D00x.md`（x 为当前最大编号 +1）
3. 修改 frontmatter 中的 `id` 与文件名一致
4. 截图放入 `images/`，命名为 `D00x-N.png`（N 为序号）
5. 在正文中引用：`![描述](images/D001-1.png)`
6. 填写现象、期望、复现步骤等

## 状态流转

新建 → 待理解 → 已理解 → 修复中 → 修复完成 → 待确认 → 已确认

验证未通过时可改为「重新打开」，再流转回「修复中」。

## 规则扫描

手动执行：`python scripts/scan_defects.py`

## 关联与版本

- 缺陷的 `related` 由扫描脚本**自动分析**缺陷正文后填充（`python scripts/scan_defects.py --auto`），无需手动填写
- 规范文档采用 frontmatter 版本号，详见 `docs/DEFECT_WORKFLOW_DESIGN.md`

---

详见 `docs/DEFECT_WORKFLOW_DESIGN.md`。
