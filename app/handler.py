from uuid import uuid4
from asyncio import sleep, get_running_loop
from app.cache import CacheGateway


class Handler(object):
    uuid = uuid4()
    cache = None
    send = None
    taks_end = False

    def __init__(self, send):
        self.send = send

    async def consumer(self, receive):
        self.cache = CacheGateway()
        await self.cache.get_pool()
        while True:
            try:
                message = await receive()
            except Exception as e:
                raise Exception("consumer error")

            if message.get('type') == 'websocket.disconnect':
                self.task_end = True
                raise Exception("task end")

            if message.get('type') == 'websocket.connect':
                continue
            text =  message['text']
            await self.produce_message(text)
            await sleep(0.1)

    async def reader(self, channel):
        async for message in channel.iter():
            try:
                message = message.decode('utf-8')
            except:
                self.taks_end = True
                raise Exception()
            await self.send({'type': 'websocket.send', 'text': message})


    async def produce_message(self, text):
        from json import loads
        try:
            body = loads(text)
        except:
            import pdb; pdb.set_trace()
            print(text) # is a normal message
            return

        if body.get('action') == 'join_room':
            await self.join_room(**body.get('params'))
        if body.get('action') == 'left_room':
            self.left_room(**body.get('params'))
        if body.get('action') == 'message_room':
            self.message_room(**body.get('params'))

    async def join_room(self, room, **kwargs):
        subscription, = await self.cache.subscribe(room)
        get_running_loop().create_task(self.reader(subscription))

    def left_room(self, **kwargs):
        pass

    def message_room(self, room, message, **kwargs):
        self.cache.publish_message(room, message)

