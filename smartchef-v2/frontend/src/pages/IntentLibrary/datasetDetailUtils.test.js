import test from 'node:test';
import assert from 'node:assert/strict';

import { shouldLoadTrainingDatasetChildren } from './datasetDetailUtils.js';

test('shouldLoadTrainingDatasetChildren returns false while dataset kind is unresolved', () => {
  assert.equal(
    shouldLoadTrainingDatasetChildren({ datasetId: 'ds-1', datasetKind: null, datasetLoading: true }),
    false,
  );
});

test('shouldLoadTrainingDatasetChildren returns false for evaluation datasets', () => {
  assert.equal(
    shouldLoadTrainingDatasetChildren({
      datasetId: 'eval-1',
      datasetKind: 'evaluation',
      datasetLoading: false,
    }),
    false,
  );
});

test('shouldLoadTrainingDatasetChildren returns true for loaded training datasets', () => {
  assert.equal(
    shouldLoadTrainingDatasetChildren({
      datasetId: 'train-1',
      datasetKind: 'training',
      datasetLoading: false,
    }),
    true,
  );
});
