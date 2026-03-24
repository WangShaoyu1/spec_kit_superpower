export function shouldLoadTrainingDatasetChildren({
  datasetId,
  datasetKind,
  datasetLoading,
}) {
  return Boolean(datasetId) && datasetKind === 'training' && datasetLoading === false;
}
