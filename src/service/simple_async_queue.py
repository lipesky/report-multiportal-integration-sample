from asyncio import Task, create_task, sleep, Lock
from asyncio.futures import Future
    

class SimpleTrottleQueue():
    _queue = []
    _active: bool = True
    _min_interval_seconds: int = 2
    _queue_processor_lock: Lock = Lock()


    def __init__(self, min_interval_seconds: int):
        self._min_interval_seconds = min_interval_seconds
        #self._initialize_processing()

    def _initialize_processing(self):
        create_task(self.process_queue())

    def activate(self):
        self._active = True
        create_task(self.process_queue())

    def deactivate(self):
        self._active = False
    
    def is_active(self) -> bool:
        return self._active

    async def func_wrapper(self, cb, **kargs):
        future = Future()
        async def callback():
            try:
                result = await cb(**kargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

        return (callback, future)

    async def add_queue(self, cb, **kargs):
        (callback, task) = await self.func_wrapper(cb, **kargs)
        self._queue.append(callback)
        self._initialize_processing()
        return task
    
    async def process_queue(self):
        try: 
            await self._queue_processor_lock.acquire()
            while self.is_active() and len(self._queue) > 0:
                callback = self._queue.pop(0)
                try: 
                    await callback()
                except Exception as e:
                    print(e)
                await sleep(self._min_interval_seconds)
        finally:
            self._queue_processor_lock.release()