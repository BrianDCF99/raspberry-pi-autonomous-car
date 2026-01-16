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
import queue

from carbot.data.models import Metadata

class DataSaver():
    def __init__(self, metadata: Metadata) -> None:
        self._meta = metadata
        self._q = queue.Queue
        self.done_saving = True

        self.frame_num = int

        self.curr_md = self.make_metadata_JSON()

    def make_metadata_JSON(self) -> None: #returns JSON object
        #load each important config individually
        #convert each of those important configs into a json file
        

        return

    def is_same_JSON_metadata(self, other: Metadata) -> bool:
        return False
        

