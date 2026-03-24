import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildIntentLibraryBatchCreatePayload,
  buildIntentLibraryBatchImportPayload,
} from './batchTestBridge.js';

test('buildIntentLibraryBatchCreatePayload builds a model-target batch request', () => {
  assert.deepEqual(
    buildIntentLibraryBatchCreatePayload({
      modelId: 'model-12345678',
      libraryId: 'library-abc',
    }),
    {
      name: '指令库批量测试-model-123',
      description: '来源: intent-library/library-abc/test',
      model_id: 'model-12345678',
      accuracy_threshold: 0.95,
      latency_threshold_ms: 2000,
    },
  );
});

test('buildIntentLibraryBatchImportPayload keeps only valid input rows', () => {
  assert.deepEqual(
    buildIntentLibraryBatchImportPayload([
      { id: '1', input: '打开烤箱', expected: 'device.on' },
      { id: '2', input: '   ', expected: 'ignored' },
      { id: '3', input: '设定五分钟', expected: '' },
    ]),
    {
      cases: [
        {
          input_text: '打开烤箱',
          expected_intent: 'device.on',
          expected_domain: 'command',
          expected_slots: {},
        },
        {
          input_text: '设定五分钟',
          expected_intent: null,
          expected_domain: 'command',
          expected_slots: {},
        },
      ],
    },
  );
});

test('buildIntentLibraryBatchImportPayload rejects empty effective rows', () => {
  assert.throws(
    () =>
      buildIntentLibraryBatchImportPayload([
        { id: '1', input: '   ', expected: '' },
      ]),
    /请填写至少一条输入/,
  );
});
