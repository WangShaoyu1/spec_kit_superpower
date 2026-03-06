from app.services.nlu.preprocessor import preprocess, detect_language, clean_text


def test_detect_chinese():
    assert detect_language("帮我搜索红烧肉") == "zh"


def test_detect_english():
    assert detect_language("search for braised pork") == "en"


def test_detect_mixed():
    assert detect_language("帮我search红烧肉") == "zh"


def test_clean_removes_extra_spaces():
    assert clean_text("  帮我  搜索  红烧肉  ") == "帮我 搜索 红烧肉"


def test_preprocess_truncation():
    long_text = "测试" * 300
    cleaned, lang, truncated = preprocess(long_text)
    assert truncated is True
    assert len(cleaned) <= 500


def test_preprocess_normal():
    cleaned, lang, truncated = preprocess("开始烹饪")
    assert cleaned == "开始烹饪"
    assert lang == "zh"
    assert truncated is False
