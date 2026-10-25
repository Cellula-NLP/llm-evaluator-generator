from abc import ABC, abstractmethod

from langchain_core.language_models.chat_models import BaseChatModel


class ILLMProvider(ABC):
    @property
    @abstractmethod
    def generator(self) -> BaseChatModel: ...

    @property
    @abstractmethod
    def evaluator(self) -> BaseChatModel: ...