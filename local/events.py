"""Author: Owen Smith (Mr0)
\n Events module
\n This module is used to handle events and is an implementation of the observer pattern
"""

from collections import defaultdict
from enum import Enum
from inspect import signature
from typing import Any, Callable, List, Optional, Union

# get debug from user configs
from local.userConfig import configs

# event class
subscribers = defaultdict(list)

# Every event that is posted will be appended to this list
eventList: List['Event'] = []


class EventType(str, Enum):
    ### INPUT EVENTS ###
    # controller events
    INPUT_BUTTON_PRESS_A = "INPUT_BUTTON_PRESS_A"
    INPUT_BUTTON_PRESS_B = "INPUT_BUTTON_PRESS_B"
    INPUT_BUTTON_PRESS_X = "INPUT_BUTTON_PRESS_X"
    INPUT_BUTTON_PRESS_Y = "INPUT_BUTTON_PRESS_Y"
    INPUT_BUTTON_PRESS_START = "INPUT_BUTTON_PRESS_START"
    INPUT_BUTTON_PRESS_SELECT = "INPUT_BUTTON_PRESS_SELECT"
    INPUT_BUTTON_PRESS_LB = "INPUT_BUTTON_PRESS_LB"
    INPUT_BUTTON_PRESS_RB = "INPUT_BUTTON_PRESS_RB"
    INPUT_BUTTON_PRESS_LT = "INPUT_BUTTON_PRESS_LT"
    INPUT_BUTTON_PRESS_RT = "INPUT_BUTTON_PRESS_RT"
    INPUT_BUTTON_PRESS_LS = "INPUT_BUTTON_PRESS_LS"
    INPUT_BUTTON_PRESS_RS = "INPUT_BUTTON_PRESS_RS"
    INPUT_JOYSTICK_AXIS_MOTION = "INPUT_JOYSTICK_AXIS_MOTION"
    INPUT_DPAD_UP = "INPUT_DPAD_UP"
    INPUT_DPAD_DOWN = "INPUT_DPAD_DOWN"
    INPUT_DPAD_LEFT = "INPUT_DPAD_LEFT"
    INPUT_DPAD_RIGHT = "INPUT_DPAD_RIGHT"
    # keyboard and mouse events
    INPUT_KEY_PRESS_SPACE = "INPUT_KEY_PRESS_SPACE"
    INPUT_KEY_PRESS_ESCAPE = "INPUT_KEY_PRESS_ESCAPE"
    INPUT_KEY_PRESS_1 = "INPUT_KEY_PRESS_1"
    INPUT_KEY_PRESS_2 = "INPUT_KEY_PRESS_2"
    INPUT_KEY_PRESS_3 = "INPUT_KEY_PRESS_3"
    INPUT_KEY_PRESS_4 = "INPUT_KEY_PRESS_4"
    INPUT_KEY_PRESS_5 = "INPUT_KEY_PRESS_5"
    INPUT_KEY_PRESS_6 = "INPUT_KEY_PRESS_6"
    INPUT_KEY_PRESS_7 = "INPUT_KEY_PRESS_7"
    INPUT_KEY_PRESS_8 = "INPUT_KEY_PRESS_8"
    INPUT_KEY_PRESS_9 = "INPUT_KEY_PRESS_9"
    INPUT_KEY_PRESS_0 = "INPUT_KEY_PRESS_0"
    INPUT_KEY_PRESS_L = "INPUT_KEY_PRESS_L"
    INPUT_KEY_PRESS_M = "INPUT_KEY_PRESS_M"
    INPUT_KEY_PRESS_N = "INPUT_KEY_PRESS_N"
    INPUT_KEY_PRESS_X = "INPUT_KEY_PRESS_X"
    INPUT_KEY_PRESS_T = "INPUT_KEY_PRESS_T"
    INPUT_KEY_PRESS_P = "INPUT_KEY_PRESS_P"
    INPUT_KEY_PRESS_V = "INPUT_KEY_PRESS_V"
    INPUT_KEY_PRESS_F = "INPUT_KEY_PRESS_F"
    INPUT_KEY_PRESS_Z = "INPUT_KEY_PRESS_Z"
    INPUT_LAUNCH_REQUESTED = "INPUT_LAUNCH_REQUESTED"

    # game events
    GAME_PEG_HIT = "GAME_PEG_HIT"
    GAME_PEG_REMOVED = "GAME_PEG_REMOVED"
    GAME_MULTIBALL_POWERUP_TRIGGERED = "GAME_MULTIBALL_POWERUP_TRIGGERED"
    GAME_NEW_GAME_ANIMATION_STARTED = "GAME_NEW_GAME_ANIMATION_STARTED"
    GAME_NEW_GAME_ANIMATION_COMPLETED = "GAME_NEW_GAME_ANIMATION_COMPLETED"
    GAME_PEG_REMOVAL_ANIMATION_STARTED = "GAME_PEG_REMOVAL_ANIMATION_STARTED"
    GAME_PEG_REMOVAL_ANIMATION_COMPLETED = "GAME_PEG_REMOVAL_ANIMATION_COMPLETED"

def _normalize_event_key(ev_type: Union[EventType, str]) -> str:
    """Return a consistent string key for an event type or EventType."""
    if isinstance(ev_type, EventType):
        return ev_type.value
    return str(ev_type)


# event class
class Event:
    """Every event in the eventList is an instance of this class
    \n For a barebones event, only the `eventType: str` is required
    \n Optionally, `args` and `eventData` can be passed to the event
    \n `args`: can be passed to any function that is subcribed to the event
    \n `eventData`: can be used to store any data that may be useful when handling the event
    """
    def __init__(self, eventType: Union[EventType, str], args=None, eventData=None):
        self.eventType = eventType
        self.args = args

        # this can be used to store relevent event data such as x and y coords, etc.
        self.eventData = eventData

    def getEventType(self) -> str:
        return _normalize_event_key(self.eventType)

    def getArgs(self):
        return self.args

    def getData(self):
        return self.eventData

    def __str__(self):
        return self.eventType

# subscribe a function to an event
def subscribe(event: Union['Event', EventType, str], fn: Callable[..., Any]):
    """
    Subscribe a function to an event\n
    This function will be called when the event is posted with `postEvent()`\n
    """
    # accept either EventType or raw string
    key = _normalize_event_key(event)
    subscribers[key].append(fn)

# post using an Event object
def postEvent(event: Union['Event', EventType, str], args=None, eventData=None):
    """
    Post an event. Accepts either an `Event` instance or an `event` type (EventType/str)
    with optional `args` and `eventData`.
    Subscribers with no required parameters receive no arguments when `args` is
    omitted; subscribers requiring an argument receive the event object.
    Subscriber exceptions propagate to the caller.
    """
    # create or reuse Event object
    if isinstance(event, Event):
        ev = event
    else:
        ev = Event(event, args, eventData)

    # append event to eventList
    eventList.append(ev)

    if configs["DEBUG_MODE"]:
        print(f"DEBUG: Event Posted\nEvent: {ev.eventType} args: {ev.args} data: {ev.eventData}")

    # call subscribers for this event type
    key = _normalize_event_key(ev.eventType)
    if key not in subscribers:
        return
    for fn in subscribers[key]:
        if configs["DEBUG_MODE"]:
            print(f"DEBUG: Function called on event: {ev.eventType}")
            print(f"DEBUG: Function: {getattr(fn, '__name__', type(fn).__name__)}")

        # call the subscriber; preserve previous behavior (no args) unless args provided
        if ev.args is None:
            try:
                signature(fn).bind()
            except TypeError:
                fn(ev)
            else:
                fn()
        else:
            # if args is an iterable (but not str/bytes), expand it
            if isinstance(ev.args, (list, tuple)):
                fn(*ev.args)
            else:
                fn(ev.args)


# clear the eventList (should be called at the beginning of every frame)
def clearEventList():
    eventList.clear()


# check if an event is in the eventList
def eventOccured(eventType: Union[EventType, str]) -> bool:
    """Returns True if the event has occured\n
    """
    key = _normalize_event_key(eventType)
    return any(event.getEventType() == key for event in eventList)


def consumeEvent(eventType: Union[EventType, str]) -> bool:
    """Remove all events of this type from the current frame and report whether any existed."""
    key = _normalize_event_key(eventType)
    matching_events = [event for event in eventList if event.getEventType() == key]
    if not matching_events:
        return False

    eventList[:] = [event for event in eventList if event.getEventType() != key]
    return True


def getEvent(eventType: Union[EventType, str]) -> Optional['Event']:
    """Returns the event object if it exists in the eventList\n
    \n Will return `None` if the event does not exist"""
    key = _normalize_event_key(eventType)
    for event in eventList:
        if event.getEventType() == key:
            return event
        
    return None