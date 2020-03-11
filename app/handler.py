from uuid import uuid4
from asyncio import sleep, get_running_loop
from app.cache import CacheGateway
from json import dumps

class Handler(object):
    uuid = str(uuid4())
    cache = None
    send = None
    taks_end = False
    rooms = []

    def __init__(self, send):
        self.send = send

    async def consumer(self, receive):
        self.cache = CacheGateway()
        await self.cache.get_pool()
        self.rooms = self.cache.lget('rooms')
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
            self.cache.lset(self.uuid, message)
            await self.send({'type': 'websocket.send', 'text': dumps({
                'action': 'room_message',
                'params': {'message': message }
                })})

    async def produce_message(self, text):
        from json import loads
        try:
            body = loads(text)
        except:
            import pdb; pdb.set_trace()
            print(text) # is a normal message
            return
        actions_function = {
            'join_room': self.join_room,
            'left_room': self.left_room,
            'message_room': self.message_room,
            'writting_message_room': self.writting_message_room,
            'get_rooms': self.get_rooms,
            'create_room': self.create_room,
        }
        action = body.get('action', None)
        if action in actions_function:
            await actions_function[action](**body.get('params'))

    async def join_room(self, room, **kwargs):
        if room not in self.rooms:
            await self.send(dict(type='websocket.send', text='room dont exist, use create_room'))
            return
        subscription, = await self.cache.subscribe(room)
        get_running_loop().create_task(self.reader(subscription))
        user = kwargs.get('user', 'None')
        self.cache.publish_message(room, f"{user} join room")

    async def left_room(self, room, user, **kwargs):
        self.cache.publish_message(room, f"{user} left room")
        # pendding unsubscribe!

    async def message_room(self, room, message, **kwargs):
        self.cache.publish_message(room, message)

    async def writting_message_room(self, room, user, **kwargs):
        self.cache.publish_message(room, f"{user} is writting a message")

    async def get_rooms(self, **kwargs):
        rooms = self.cache.lget('rooms')
        await self.send({'type': 'websocket.send', 'text': dumps(
            {'action': 'get_rooms',
            'params': {'rooms': rooms}
             })})

    async def create_room(self, room, **kwargs):
        if room in self.rooms:
            await self.send(dict(type='websocket.send', text=f'{room} already exist'))
            return
        self.cache.lset('rooms', room)
        self.rooms.append(room)
        await self.send(dict(type='websocket.send', text=f'room {room} created'))

