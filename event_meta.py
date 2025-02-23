class EventProcessorType(type):
    """Metaclass for automatic event processor registration"""
    _processors = {}
    
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if hasattr(cls, 'event_type'):
            mcs._processors[cls.event_type] = cls
        return cls

    @classmethod
    def get_processor(mcs, event_type):
        return mcs._processors.get(event_type)

class BaseEventProcessor(metaclass=EventProcessorType):
    async def process(self, event):
        raise NotImplementedError 