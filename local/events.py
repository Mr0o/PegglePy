"""Author: Owen Smith (Mr0)
\n Events module
\n This module is used to handle events and is an implementation of the observer pattern
"""

from collections import defaultdict

# get debug from user configs
from local.userConfig import configs
debug = configs["DEBUG_MODE"]

# Default value of the dictionary will be list
subscribers = defaultdict(list)

# Every event that is posted will be appended to this list
eventList: list['Event'] = []

def subscribe(event: 'Event', fn: callable):
    """
    Subscribe a function to an event\n
    This function will be called when the event is posted with `postEvent()`\n
    """
    subscribers[event].append(fn)

# post using an Event object
def postEvent(event: 'Event'):
    """
    Post an event object to the eventList\n
    """
    # append event to eventList
    eventList.append(event)
    
    if debug:
        print(f"DEBUG: Event Posted\nEvent: {event.eventType} args: {event.args} data: {event.eventData}")

    # call subcribers function
    if not event in subscribers:
        return
    for fn in subscribers[event]:
        if debug:
            print(f"DEBUG: Function called on event: {event.eventType}")
            print(f"DEBUG: Function: {fn.__name__}")

        fn()

# post without passing an Event object
def postEvent(eventType: str, args=None, eventData=None):
    """
    Post an event to the eventList\n
    Can optionally pass args and eventData to be included in the event\n
    """
    # create the Event object
    event = Event(eventType, args, eventData)
    # append event to eventList
    eventList.append(event)

    if debug:
        print(f"DEBUG: Event Posted\nEvent: {event.eventType} args: {event.args} data: {event.eventData}")

    # call subcribers function
    if not event in subscribers:
        return
    for fn in subscribers[event]:
        if debug:
            print(f"DEBUG: Function called on event: {event.eventType}")
            print(f"DEBUG: Function: {fn.__name__}")

        fn()


# clear the eventList (should be called at the beginning of every frame)
def clearEventList():
    eventList.clear()


# check if an event is in the eventList
def eventOccured(eventType: str) -> bool:
    """Returns True if the event has occured\n
    """
    # check if any of the event objects have the same eventType string
    for event in eventList:
        if event.getEventType() == eventType:
            return True
    
    return False


def getEvent(eventType: str) -> 'Event':
    """Returns the event object if it exists in the eventList\n
    \n Will return `None` if the event does not exist"""
    # check if any of the event objects have the same eventType string
    for event in eventList:
        if event.getEventType() == eventType:
            return event
        
    return None

# event class
class Event:
    """Every event in the eventList is an instance of this class
    \n For a barebones event, only the `eventType: str` is required
    \n Optionally, `args` and `eventData` can be passed to the event
    \n `args`: can be passed to any function that is subcribed to the event
    \n `eventData`: can be used to store any data that may be useful when handling the event
    """
    def __init__(self, eventType: str, args=None, eventData=None):
        self.eventType = eventType
        self.args = args

        # this can be used to store relevent event data such as x and y coords, etc.
        self.eventData = eventData

    def getEventType(self) -> str:
        return self.eventType

    def getArgs(self):
        return self.args
    
    def getData(self):
        return self.eventData

    def __str__(self):
        return self.eventType