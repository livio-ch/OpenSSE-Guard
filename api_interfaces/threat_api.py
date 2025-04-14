from abc import ABC, abstractmethod

class ThreatIntelAPI(ABC):
    @abstractmethod
    def check_domain(self, domain: str):
        pass

    @abstractmethod
    def check_hash(self, file_hash: str):
        pass
