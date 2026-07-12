"""
Minimal Strategy interface for use INSIDE the sandbox. Deliberately does NOT
import the real Portfolio — strategy code here only ever talks to an
OrderIntentRecorder, so it can never touch real cash/positions.
"""
from abc import ABC, abstractmethod
import pandas as pd


class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bar: pd.Series, recorder) -> None:
        raise NotImplementedError