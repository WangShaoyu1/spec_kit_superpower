export function getExcelImportFeedback({ fileName } = {}) {
  void fileName;
  return {
    level: 'info',
    text: 'Excel 导入解析服务尚未接入，本次仅完成文件格式校验，未创建导入任务。',
  };
}

export function getLlmGenerationFeedback(result = {}) {
  const count = result?.generated_count ?? 0;
  const errors = result?.errors ?? result?.failed_intents ?? [];
  if (count > 0 && errors.length) {
    return {
      level: 'warning',
      text: `成功生成 ${count} 条样本，但部分意图生成失败: ${errors.join('；')}`,
    };
  }
  if (count > 0) {
    return {
      level: 'success',
      text: `成功生成 ${count} 条样本（覆盖 ${result?.intent_count ?? '-'} 个意图）`,
    };
  }
  if (errors.length) {
    return {
      level: 'warning',
      text: `本次未生成新样本，失败意图: ${errors.join('；')}`,
    };
  }
  return {
    level: 'info',
    text: '本次未生成新样本，请检查提示词、数据集绑定和 LLM 配置后重试。',
  };
}
