---
name: 手动测试反馈
description: 本项目通过Spec-Kit规范建立的前后端项目，现在完成了AI编码、AI测试阶段，现在进入手动测试阶段，请基于手动反馈的内容inx
license: MIT
metadata:
  author: wy
  version: "1.0.0"
---
> **⚠️ 弃用说明**：本文件已弃用。手动测试阶段统一采用缺陷体系，见 `specs/master/defects/` 与 `docs/DEFECT_WORKFLOW_DESIGN.md`。新问题请录入为缺陷（复制 `_template.md` 重命名为 D00x.md）。

# 规范类
## UI风格
整体UI风格非常一般，整体配色很传统、大气，看着就没有继续点击的欲望
页面滚动条非常粗，且常有滚动条，滚动条按需出现
请使用frontend-design这个skill来优化

### 弹窗
所有的页面中弹窗，去掉“点击mask，弹窗消失”这个逻辑

### Input
所有的Input 组件，要加上clearable能力

## 接口响应
### 格式
接口响应请保持如下的格式：
```json
{
  code:"000000",
  data:xxx,
  msg:xxx
}
```
接口响应正常，响应码就是"000000",异常情况，可以自行定义错误码，并且前端按照对应的错误码来调整逻辑
### 分页
凡是列表，皆用分页组件、接口


# 业务类
## 接口报错
### http://localhost:3000/api/v1/test/chat，
前端响应：{
    "domain": "chitchat",
    "route_confidence": 0.8,
    "intent": null,
    "intent_confidence": null,
    "slots": {},
    "response_text": "抱歉，暂时无法生成回复，请稍后再试。",
    "needs_followup": false,
    "language": "zh",
    "latency_ms": 3028,
    "debug_info": {
        "preprocessed": {
            "text": "你好",
            "language": "zh",
            "truncated": false
        },
        "routing": {
            "domain": "chitchat",
            "confidence": 0.8
        }
    }
}
控制台有报错："LLM call failed: Error code: 500 - {'message': 'invalid csrf token'}"
### http://localhost:3000/api/v1/intent-libraries
接口404 Not Found

# 需求类

### 逻辑类
1、新建的会话，能够实现编辑、删除功能
2、对话方案配置，该页面中，方案列表中有一个 状态字段，逻辑是什么，怎么改变“草稿”状态
3、闲聊人设管理，该弹窗中，人设列表，无法编辑
4、批量测试与分析，该页面，新建批量测试插入记录，与上传测试用例，分为两个动作。测试用例支持excel模板，并能支持excel解析，并最终输出批量测试结论（测试结论用大弹窗）
5、指令配置管理，这个增加一级路由————指令库的概念，进行页面跳转。指令库列表----意图列表，两层逻辑。
6、用户管理，该页面，需要加入角色的定义和配置，以及每个角色的能力定义

# 备注
1、如上内容，请你按照已有的需求spec.md，计划plan.md，任务task.md，进行版本迭代，并自行验证
2、docs文件夹中，期望将已有的md文件，放在一起，不同板块的内容，按照一级标题来进行扩充、修改，并在文件顶部增加一个目录，而不再是以独立md文件的形式
3、按照spec.md，有项目组成员反馈，缺少交互界面PRD（类似于之前的产品经理制作的Azure PRD交互稿），这个需要补充，用HTML的形式。