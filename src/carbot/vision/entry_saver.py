"""
consumer thread with a queue to save jpegs and a flag to say its 
done saving the queue so that the main class can wait for this to 
be done before closing and exiting the program 

Producer-consumer   thread 

requested_end: ..

push_jpeg:
    lock
        add
    unlock

save jpeg 
    while not requested_end
    lock
        pop
    unlock 
        
    save
    if queue is empty:
        self.done = True
    
"""
from __future__ import annotations

from dataclasses import dataclass
import queue

IMG_PATH = "src/data/images"

@dataclass(frozen=True, slots=True)
class DataEntry:
    jpeg: bytes
    throttle: int
    steer: int
    pan: int
    tilt: int
    ts: int
    infrared: int = 0
    ultrasonic: int = 0

@dataclass(frozen=True, slots=True)
class MetaData:
    

class DataSaver():
    def __init__(self) -> None:
        self.q = queue.Queue

        
