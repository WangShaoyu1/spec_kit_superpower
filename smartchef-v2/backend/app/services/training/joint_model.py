"""Joint intent classification + slot filling model (DistilBERT/BERT encoder)."""

import torch.nn as nn
from transformers import AutoModel, BertModel


def _load_encoder(name: str):
    """Load a pretrained encoder, falling back to BertModel for repos missing model_type."""
    try:
        return AutoModel.from_pretrained(name)
    except ValueError:
        return BertModel.from_pretrained(name)


class IntentSlotModel(nn.Module):
    def __init__(
        self,
        base_model_name: str,
        num_intents: int,
        num_slot_tags: int,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.encoder = _load_encoder(base_model_name)
        hidden_size = self.encoder.config.hidden_size
        self.intent_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_intents),
        )
        self.slot_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_slot_tags),
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]
        intent_logits = self.intent_head(cls_output)
        slot_logits = self.slot_head(outputs.last_hidden_state)
        return intent_logits, slot_logits
