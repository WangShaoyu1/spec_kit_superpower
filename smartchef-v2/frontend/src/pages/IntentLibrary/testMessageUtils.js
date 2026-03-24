export function getDebugInfoFromMessage(message) {
  const result = message?.result ?? {};

  return {
    intent: message?.intent ?? message?.nlu?.intent ?? result.intent ?? null,
    confidence: message?.confidence ?? message?.nlu?.confidence ?? result.confidence ?? null,
    slots: message?.slots ?? message?.nlu?.slots ?? result.slots ?? null,
    latency_ms: message?.latency_ms ?? result.latency_ms ?? null,
    domain: message?.domain ?? message?.nlu?.domain ?? result.domain ?? null,
    fallback: message?.fallback ?? result.fallback ?? null,
    raw: message?.raw ?? result ?? null,
  };
}

export function getPaginatedMessageItems(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return [];
  }
  return Array.isArray(payload.items) ? payload.items : [];
}

export function removeTemporaryMessage(messages, tempId) {
  return (messages || []).filter((message) => message?.id !== tempId);
}
