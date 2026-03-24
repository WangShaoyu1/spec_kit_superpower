import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getDebugInfoFromMessage,
  getPaginatedMessageItems,
  removeTemporaryMessage,
} from './testMessageUtils.js';

test('getDebugInfoFromMessage extracts nested result fields from assistant messages', () => {
  const message = {
    id: 'msg-1',
    role: 'assistant',
    content: '意图: device.on',
    result: {
      intent: 'device.on',
      confidence: 0.92,
      slots: { device: '烤箱' },
      latency_ms: 42,
    },
  };

  assert.deepEqual(getDebugInfoFromMessage(message), {
    intent: 'device.on',
    confidence: 0.92,
    slots: { device: '烤箱' },
    latency_ms: 42,
    domain: null,
    fallback: null,
    raw: message.result,
  });
});

test('getDebugInfoFromMessage preserves top-level debug fields when present', () => {
  const message = {
    id: 'msg-2',
    role: 'assistant',
    content: 'ok',
    intent: 'timer.set',
    confidence: 0.81,
    slots: { duration: '5分钟' },
    latency_ms: 35,
    fallback: false,
    raw: { source: 'mock' },
  };

  assert.deepEqual(getDebugInfoFromMessage(message), {
    intent: 'timer.set',
    confidence: 0.81,
    slots: { duration: '5分钟' },
    latency_ms: 35,
    domain: null,
    fallback: false,
    raw: { source: 'mock' },
  });
});

test('removeTemporaryMessage drops the optimistic temp bubble after send failure', () => {
  const messages = [
    { id: 'temp-1', role: 'user', text: 'hello' },
    { id: 'msg-2', role: 'assistant', content: 'ok' },
  ];

  assert.deepEqual(removeTemporaryMessage(messages, 'temp-1'), [
    { id: 'msg-2', role: 'assistant', content: 'ok' },
  ]);
});

test('getPaginatedMessageItems reads items from the paginated envelope', () => {
  assert.deepEqual(
    getPaginatedMessageItems({
      items: [
        { id: 'msg-1', role: 'user', content: 'hello' },
        { id: 'msg-2', role: 'assistant', content: 'ok' },
      ],
      total: 2,
      page: 1,
      page_size: 200,
      pages: 1,
    }),
    [
      { id: 'msg-1', role: 'user', content: 'hello' },
      { id: 'msg-2', role: 'assistant', content: 'ok' },
    ],
  );
});

test('getPaginatedMessageItems rejects bare arrays to avoid guessing response shape', () => {
  assert.deepEqual(
    getPaginatedMessageItems([
      { id: 'msg-1', role: 'user', content: 'hello' },
    ]),
    [],
  );
});
