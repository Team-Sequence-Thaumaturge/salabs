from abc import ABC, abstractmethod

class BaseTensorState(ABC):
    @property
    @abstractmethod
    def S_matrix(self):
        pass

    @property
    @abstractmethod
    def timestamp(self):
        pass

    @property
    @abstractmethod
    def dimension(self):
        pass

    @property
    @abstractmethod
    def entropy_density(self):
        pass

    @property
    @abstractmethod
    def invariants(self):
        pass
