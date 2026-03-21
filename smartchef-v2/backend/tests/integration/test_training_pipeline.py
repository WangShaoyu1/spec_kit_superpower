"""Direct integration test for the training→inference→evaluation pipeline.

Bypasses the HTTP layer to test the core business logic directly.
Uses prajjwal1/bert-tiny for fast training (~10-30 seconds).
"""

import asyncio
import os
import uuid

import pytest

TINY_MODEL = "prajjwal1/bert-tiny"


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def db_session():
    os.environ["DEBUG"] = "false"
    from app.core.config import get_settings
    get_settings.cache_clear()
    from app.core import database as db_mod
    await db_mod.init_db()
    session = db_mod.async_session_factory()
    try:
        yield session
    finally:
        try:
            await session.close()
        except Exception:
            pass
        await db_mod.close_db()


async def _seed_library_and_data(db):
    """Create library, dataset, intents, similar questions in DB."""
    from app.models.intent_library import IntentLibrary
    from app.models.dataset import TrainingDataset, EvaluationDataset
    from app.models.intent import Intent, SimilarQuestion

    key = f"pipe_{uuid.uuid4().hex[:6]}"
    lib = IntentLibrary(
        library_key=key, name="Pipeline Test", language="en",
        default_confidence_threshold=0.7,
        default_intent_f1_threshold=0.5,
        default_slot_f1_threshold=0.5,
    )
    db.add(lib)
    await db.flush()

    ds = TrainingDataset(library_id=lib.id, name="Train", source_type="manual")
    db.add(ds)
    await db.flush()

    greet = Intent(dataset_id=ds.id, intent_key="greet", name_zh="问候")
    timer = Intent(dataset_id=ds.id, intent_key="set_timer", name_zh="设置计时", slot_keys=["duration"])
    recipe = Intent(dataset_id=ds.id, intent_key="ask_recipe", name_zh="菜谱", slot_keys=["dish"])
    db.add_all([greet, timer, recipe])
    await db.flush()

    greet_qs = [
        SimilarQuestion(intent_id=greet.id, text="Hello there", slot_annotations={}),
        SimilarQuestion(intent_id=greet.id, text="Hi good morning", slot_annotations={}),
        SimilarQuestion(intent_id=greet.id, text="Hey how are you", slot_annotations={}),
        SimilarQuestion(intent_id=greet.id, text="Good evening", slot_annotations={}),
    ]
    timer_qs = [
        SimilarQuestion(intent_id=timer.id, text="Set a timer for 5 minutes",
                        slot_annotations=[{"start": 20, "end": 29, "slot": "duration"}]),
        SimilarQuestion(intent_id=timer.id, text="Timer 10 mins please",
                        slot_annotations=[{"start": 6, "end": 13, "slot": "duration"}]),
        SimilarQuestion(intent_id=timer.id, text="Count down 3 minutes",
                        slot_annotations=[{"start": 11, "end": 20, "slot": "duration"}]),
        SimilarQuestion(intent_id=timer.id, text="Start a 15 minute timer",
                        slot_annotations=[{"start": 8, "end": 17, "slot": "duration"}]),
    ]
    recipe_qs = [
        SimilarQuestion(intent_id=recipe.id, text="How to cook pasta",
                        slot_annotations=[{"start": 12, "end": 17, "slot": "dish"}]),
        SimilarQuestion(intent_id=recipe.id, text="Recipe for fried rice",
                        slot_annotations=[{"start": 11, "end": 21, "slot": "dish"}]),
        SimilarQuestion(intent_id=recipe.id, text="Show me a salad recipe",
                        slot_annotations=[{"start": 10, "end": 15, "slot": "dish"}]),
        SimilarQuestion(intent_id=recipe.id, text="I want to make soup",
                        slot_annotations=[{"start": 15, "end": 19, "slot": "dish"}]),
    ]
    db.add_all(greet_qs + timer_qs + recipe_qs)
    ds.sample_count = 12
    ds.intent_count = 3
    await db.flush()

    eval_ds = EvaluationDataset(
        library_id=lib.id, name="Eval", source_type="manual",
        sample_count=4,
        samples=[
            {"utterance": "Hello!", "expected_result": "greet"},
            {"utterance": "Good morning!", "expected_result": "greet"},
            {"utterance": "Timer 8 minutes", "expected_result": "set_timer"},
            {"utterance": "Show me chicken recipe", "expected_result": "ask_recipe"},
        ],
    )
    db.add(eval_ds)
    await db.flush()
    await db.commit()

    return lib, ds, eval_ds


@pytest.mark.asyncio(loop_scope="module")
async def test_training_pipeline_end_to_end(db_session):
    """Full pipeline: create data → train model → inference → evaluate → publish."""
    from app.models.model_version import LibraryModelVersion
    from app.models.evaluation import EvaluationRun
    from app.core.config import get_settings, resolve_artifact_path

    lib, train_ds, eval_ds = await _seed_library_and_data(db_session)

    model = LibraryModelVersion(
        library_id=lib.id,
        version_name="v-pipeline-test",
        train_dataset_id=train_ds.id,
        train_config={
            "base_model": TINY_MODEL,
            "max_seq_length": 32,
            "batch_size": 4,
            "learning_rate": 3e-4,
            "max_epochs": 2,
            "early_stopping_patience": 2,
            "train_val_split": 0.8,
            "intent_loss_weight": 0.7,
        },
        status="draft",
    )
    db_session.add(model)
    await db_session.flush()
    await db_session.commit()
    model_id = model.id

    model.status = "training"
    model.progress = 0
    await db_session.commit()

    from app.services.training.trainer import execute_training
    await execute_training(model_id, get_settings().DATABASE_URL)

    await db_session.refresh(model)
    assert model.status == "trained", f"Training failed: {model.notes}"
    assert model.artifact_uri is not None
    assert model.artifact_uri.endswith(".onnx")
    assert model.progress == 100
    assert model.metrics.get("best_val_intent_f1") is not None
    assert model.trained_at is not None

    resolved = resolve_artifact_path(model.artifact_uri)
    assert os.path.isfile(resolved), f"ONNX file missing: {resolved}"
    model_dir = os.path.dirname(resolved)
    for f in ["label_map.json", "slot_map.json", "metadata.json", "package.zip"]:
        assert os.path.isfile(os.path.join(model_dir, f)), f"Missing: {f}"

    from app.services.inference import ModelCache
    engine = ModelCache.get_or_load(model_dir)

    result_hello = engine.classify_intent("Hello there")
    assert result_hello.intent in ("greet", "set_timer", "ask_recipe")
    assert result_hello.confidence > 0
    assert result_hello.latency_ms >= 0
    assert len(result_hello.all_scores) == 3

    result_slots = engine.extract_slots("Set a timer for 5 minutes")
    assert isinstance(result_slots.slots, list)

    model.status = "evaluating"
    eval_run = EvaluationRun(
        library_id=lib.id,
        model_version_id=model.id,
        dataset_id=eval_ds.id,
        status="pending",
        threshold_intent_f1=0.1,
        threshold_slot_f1=0.1,
        total_samples=eval_ds.sample_count,
        snapshot={
            "model_status": "trained",
            "model_version_name": model.version_name,
        },
    )
    db_session.add(eval_run)
    await db_session.commit()

    from app.services.training.evaluator import execute_batch_evaluation
    await execute_batch_evaluation(eval_run.id, get_settings().DATABASE_URL)

    await db_session.refresh(eval_run)
    assert eval_run.status == "completed", f"Eval failed: {eval_run.result_summary}"
    summary = eval_run.result_summary
    assert summary["total_samples"] == 4
    assert "intent_accuracy" in summary
    assert "intent_f1" in summary
    assert "confusion_pairs" in summary

    await db_session.refresh(model)
    assert model.status == "trained"

    model.is_testable = True
    model.status = "testable"
    await db_session.commit()
    await db_session.refresh(model)
    assert model.status == "testable"
    assert model.is_testable is True

    model.status = "published"
    model.is_published = True
    await db_session.commit()
    await db_session.refresh(model)
    assert model.status == "published"
    assert model.is_published is True

    print(f"\n  Full lifecycle passed! Model {model_id}")
    print(f"   Intent F1: {model.metrics.get('best_val_intent_f1', 'N/A')}")
    print(f"   Eval accuracy: {summary.get('intent_accuracy', 'N/A')}")
    print(f"   Artifacts: {model_dir}")

    ModelCache.clear()
