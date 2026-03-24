export function buildIntentLibraryBatchCreatePayload({ modelId, libraryId }) {
  if (!modelId) {
    throw new Error('请选择模型');
  }

  return {
    name: `指令库批量测试-${String(modelId).slice(0, 9)}`,
    description: `来源: intent-library/${libraryId}/test`,
    model_id: modelId,
    accuracy_threshold: 0.95,
    latency_threshold_ms: 2000,
  };
}

export function buildIntentLibraryBatchImportPayload(rows = []) {
  const cases = (rows || [])
    .filter((row) => row?.input?.trim())
    .map((row) => ({
      input_text: row.input.trim(),
      expected_intent: row.expected?.trim() ? row.expected.trim() : null,
      expected_domain: 'command',
      expected_slots: {},
    }));

  if (!cases.length) {
    throw new Error('请填写至少一条输入');
  }

  return { cases };
}
