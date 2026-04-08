export const DEFAULT_THRESHOLDS = {
  command_intent_accuracy_min: 0.95,
  slot_f1_min: 0.9,
  response_p95_ms: 2000,
}

export function getFirstTrainingDataset(detail) {
  return detail?.datasets?.find((item) => item.dataset_type === 'training') ?? null
}

export function getFirstEvaluationDataset(detail) {
  return detail?.datasets?.find((item) => item.dataset_type === 'evaluation') ?? null
}

export function getTestableModel(detail) {
  if (!detail?.models?.length) {
    return null
  }

  return detail.models.find((item) => item.is_testable || item.is_published) ?? null
}

export function getPublishableModel(detail) {
  return (
    detail?.models?.find((item) => item.is_published)
    ?? detail?.models?.find((item) => item.is_testable && item.status === 'testable')
    ?? null
  )
}

export function getPrimaryModel(detail) {
  if (!detail?.models?.length) {
    return null
  }

  return (
    getTestableModel(detail)
    ?? detail.models[detail.models.length - 1]
  )
}
