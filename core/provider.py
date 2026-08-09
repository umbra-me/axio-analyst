"""Provider contract shared by application logic and adapters."""

from abc import ABC, abstractmethod
from typing import Callable, Optional

from .models import ProviderResult

CancelCheck = Optional[Callable[[], bool]]
StreamCallback = Optional[Callable[[str], None]]


class Provider(ABC):
    @abstractmethod
    def complete(
        self,
        prompt: str,
        is_cancelled: CancelCheck = None,
        on_stream: StreamCallback = None,
    ) -> ProviderResult:
        raise NotImplementedError
