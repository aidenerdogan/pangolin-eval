from __future__ import annotations

from abc import ABC, abstractmethod

from pangolin_eval.models import Completion, ModelTarget, PromptCase


class Provider(ABC):
    @abstractmethod
    def complete(self, model: ModelTarget, prompt: PromptCase) -> Completion:
        """Return a chat completion for the given model and prompt case."""
