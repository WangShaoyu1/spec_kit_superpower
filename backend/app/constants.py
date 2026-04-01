ROLE_LABELS = {
    "admin": "系统管理员",
    "pm": "产品经理",
    "tester": "测试人员",
}


CAPABILITY_ROWS = [
    ("intent_library_read", "查看指令库列表", None, "intent-library"),
    ("intent_library_write", "创建/编辑指令库", None, "intent-library"),
    ("intent_library_delete", "删除指令库", None, "intent-library"),
    ("model_train", "创建训练任务", None, "intent-library"),
    ("model_test_manage", "管理 testable 模型", None, "intent-library"),
    ("model_publish", "发布模型", None, "intent-library"),
    ("profile_read", "查看对话方案", None, "dialog-profile"),
    ("profile_write", "创建/编辑方案", None, "dialog-profile"),
    ("profile_publish", "发布方案", None, "dialog-profile"),
    ("knowledge_write", "上传/管理知识库", None, "knowledge-base"),
    ("test_execute", "执行测试", None, "batch-test"),
    ("monitoring_read", "查看监控", None, "monitoring"),
    ("alert_manage", "管理告警规则", None, "monitoring"),
    ("user_manage", "用户管理", None, "user-mgmt"),
]


ROLE_CAPABILITIES = {
    "admin": {item[0]: item[2] for item in CAPABILITY_ROWS},
    "pm": {
        "intent_library_read": None,
        "intent_library_write": "仅自己创建的",
        "intent_library_delete": "仅自己+草稿",
        "model_train": None,
        "model_test_manage": None,
        "model_publish": "需审批",
        "profile_read": None,
        "profile_write": None,
        "profile_publish": "需审批",
        "knowledge_write": None,
        "test_execute": None,
        "monitoring_read": None,
    },
    "tester": {
        "intent_library_read": None,
        "model_test_manage": None,
        "profile_read": None,
        "test_execute": None,
        "monitoring_read": None,
    },
}
