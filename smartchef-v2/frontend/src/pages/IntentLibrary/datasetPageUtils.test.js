import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getCoverageDatasetId,
  normalizeDatasetCollections,
  isEvaluationDataset,
} from './datasetPageUtils.js';

test('normalizeDatasetCollections marks training and evaluation datasets explicitly', () => {
  const training = [{ id: 'train-1', name: '训练集 A', source_type: 'manual' }];
  const evaluation = [{ id: 'eval-1', name: '评估集 A', source_type: 'manual' }];

  const result = normalizeDatasetCollections(training, evaluation);

  assert.deepEqual(
    result.map((item) => ({
      id: item.id,
      dataset_kind: item.dataset_kind,
      source_type: item.source_type,
    })),
    [
      { id: 'train-1', dataset_kind: 'training', source_type: 'manual' },
      { id: 'eval-1', dataset_kind: 'evaluation', source_type: 'manual' },
    ],
  );
});

test('isEvaluationDataset only treats explicit evaluation datasets as evaluation targets', () => {
  assert.equal(
    isEvaluationDataset({ id: 'eval-1', dataset_kind: 'evaluation', source_type: 'manual' }),
    true,
  );
  assert.equal(
    isEvaluationDataset({ id: 'train-1', dataset_kind: 'training', source_type: 'manual' }),
    false,
  );
  assert.equal(
    isEvaluationDataset({ id: 'train-2', source_type: 'evaluation' }),
    false,
  );
});

test('getCoverageDatasetId falls back to linked training dataset for evaluation datasets', () => {
  assert.equal(
    getCoverageDatasetId({
      id: 'eval-1',
      dataset_kind: 'evaluation',
      config: { training_dataset_id: 'train-1' },
    }),
    'train-1',
  );
  assert.equal(
    getCoverageDatasetId({
      id: 'eval-2',
      dataset_kind: 'evaluation',
      config: { train_dataset_id: 'train-2' },
    }),
    'train-2',
  );
  assert.equal(
    getCoverageDatasetId({
      id: 'train-3',
      dataset_kind: 'training',
    }),
    'train-3',
  );
});
