from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    Strategy interface
    All strategies must implement generate_signal()
    """

    @abstractmethod
    def generate_signal(self, df):
        pass
