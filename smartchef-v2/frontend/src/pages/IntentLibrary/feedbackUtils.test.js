import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getExcelImportFeedback,
  getLlmGenerationFeedback,
} from './feedbackUtils.js';

test('getExcelImportFeedback keeps deferred excel import out of success state', () => {
  assert.deepEqual(getExcelImportFeedback({ fileName: 'dataset.xlsx' }), {
    level: 'info',
    text: 'Excel 导入解析服务尚未接入，本次仅完成文件格式校验，未创建导入任务。',
  });
});

test('getLlmGenerationFeedback reports explicit zero-result outcome', () => {
  assert.deepEqual(
    getLlmGenerationFeedback({
      generated_count: 0,
      intent_count: 3,
    }),
    {
      level: 'info',
      text: '本次未生成新样本，请检查提示词、数据集绑定和 LLM 配置后重试。',
    },
  );
});

test('getLlmGenerationFeedback preserves partial-failure warning details', () => {
  assert.deepEqual(
    getLlmGenerationFeedback({
      generated_count: 4,
      errors: ['intent.a 超时', 'intent.b 未配置'],
    }),
    {
      level: 'warning',
      text: '成功生成 4 条样本，但部分意图生成失败: intent.a 超时；intent.b 未配置',
    },
  );
});
