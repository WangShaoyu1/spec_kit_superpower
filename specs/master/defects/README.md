# 缺陷管理

当前目录用于本轮手动验收阶段的缺陷录入与闭环管理。

## 目录结构

```text
specs/master/defects/
  README.md            # 当前目录说明
  _template.md         # 缺陷模板（复制后重命名）
  images/              # 缺陷截图（命名：D001-1.png, D001-2.png）
  D001.md
  D002.md
  ...
```

## 新增缺陷

1. 复制 `_template.md`
2. 重命名为 `D00x.md`（x 为当前最大编号 +1）
3. 修改 frontmatter 中的 `id` 与文件名一致
4. 截图放入 `images/`，命名为 `D00x-N.png`
5. 在正文中引用截图：`![描述](images/D00x-1.png)`
6. 填写现象、期望、复现步骤等内容

## 状态流转

新建 -> 待理解 -> 已理解 -> 修复中 -> 修复完成 -> 待确认 -> 已确认

验证未通过时可改为“重新打开”，再流转回“修复中”。

## 规则扫描

手动执行：`python scripts/scan_defects.py`

## 关联与版本

- `related` 可由扫描脚本自动分析后补充：`python scripts/scan_defects.py --auto`
- 规范文档版本规则详见 `docs/DEFECT_WORKFLOW_DESIGN.md`
