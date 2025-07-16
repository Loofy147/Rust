from enum import Enum, auto

class ArchitectureEventType(Enum):
    CODE_CHANGE = auto()
    ARCHITECTURE_UPDATE = auto()
    PERFORMANCE_ALERT = auto()
    SECURITY_ALERT = auto()
    DOC_UPDATE = auto()
    TEST_RESULT = auto()
    DEPLOYMENT = auto()