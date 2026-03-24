export function normalizeDatasetCollections(trainingDatasets = [], evaluationDatasets = []) {
  const training = (trainingDatasets || []).map((dataset) => ({
    ...dataset,
    dataset_kind: 'training',
  }));
  const evaluation = (evaluationDatasets || []).map((dataset) => ({
    ...dataset,
    dataset_kind: 'evaluation',
  }));

  return [...training, ...evaluation];
}

export function isEvaluationDataset(dataset) {
  return dataset?.dataset_kind === 'evaluation';
}

export function getCoverageDatasetId(dataset) {
  if (!dataset) return null;
  if (!isEvaluationDataset(dataset)) return dataset.id ?? null;
  return dataset.config?.training_dataset_id ?? dataset.config?.train_dataset_id ?? null;
}
