from asyncio import AbstractEventLoop, Lock, Queue, Task, create_task, sleep, new_event_loop, set_event_loop
from threading import Thread
from queue import SimpleQueue

    

class TrottleQueue():
    _queue: SimpleQueue = SimpleQueue()
    _active: bool = True
    _min_interval_seconds: int = 2
    _queue_processor_task: Task
    _event_loop: AbstractEventLoop
    _thread: Thread

    def __init__(self, min_interval_seconds: int):
        self._min_interval_seconds = min_interval_seconds
        self._initialize_processing()

    def _initialize_processing(self):
        self._thread = Thread(target=self._thread_runner, kwargs={
            'process_queue': self.process_queue 
        })
        self._thread.daemon = True
        self._thread.start()
        print('queue event loop initialized')

    def _thread_runner(self, process_queue):
        event_loop = new_event_loop()
        set_event_loop(event_loop)
        event_loop.create_task(process_queue())
        event_loop.run_forever()

    def activate(self):
        self._active = True
        create_task(self.process_queue())

    def deactivate(self):
        self._active = False
    
    def is_active(self) -> bool:
        return self._active

    async def func_wrapper(self, cb, **kargs):
        lock = Lock()
        await lock.acquire()
        async def callback():
            await cb(**kargs)
            lock.release()
        
        async def cb_task():
            await lock.acquire()
            lock.release()
        
        task = create_task(cb_task())
        return (callback, task)

    async def add_queue(self, cb, **kargs):
        (callback, task) = await self.func_wrapper(cb, **kargs)
        self._queue.put(callback)
        return task
    
    async def process_queue(self):
        print('starting processing queue')
        while self.is_active():
            callback = self._queue.get()
            print('got call')
            try: 
                await callback()
            except Exception as e:
                print(e)
            await sleep(self._min_interval_seconds)
        print('finished processing queue')