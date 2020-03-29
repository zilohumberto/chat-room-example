from uuid import uuid4
from asyncio import sleep, get_running_loop
from app.cache import CacheGateway
from json import dumps, loads


class Handler(object):
    uuid = str(uuid4())
    cache = None
    send = None
    task_end = False
    rooms = []
    user = None
    obj_user = None

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
            
            if self.task_end:
                break

            if message.get('type') == 'websocket.disconnect':
                for room in self.rooms:
                    await self.left_room(room)
                self.task_end = True
                raise Exception("task end")

            if message.get('type') == 'websocket.connect':
                continue
            text = message['text']
            await self.produce_message(text)
            await sleep(0.1)

    async def reader(self, channel):
        async for message in channel.iter():
            try:
                message = message.decode('utf-8')
            except:
                self.task_end = True
                raise Exception()
            self.cache.lset(self.uuid, message)
            await self.send({'type': 'websocket.send', 'text': message})

    async def produce_message(self, text):
        body = loads(text)
        actions_function = {
            'join_room': self.join_room,
            'left_room': self.left_room,
            'message_room': self.message_room,
            'writing_message_room': self.writing_message_room,
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
        self.obj_user = kwargs['user']
        self.user = f"{self.obj_user['name']['first']} {self.obj_user['name']['last']}" 
        self.thumbnail = self.obj_user['picture']['thumbnail']
        self.cache.publish_message(room, dict(action='joined_room', params=dict(room=room, user=self.user, image=self.thumbnail)))

    async def left_room(self, room, **kwargs):
        self.cache.publish_message(room, dict(action='left_room', params=dict(room=room, user=self.user, image=self.thumbnail)))

    async def message_room(self, room, message, **kwargs):
        self.cache.publish_message(room, dict(action='message_room', params=dict(room=room, user=self.user, message=message, image=self.thumbnail)))
        from app.wiki import split_msg
        msg = split_msg(message)
        if msg:
            self.cache.publish_message(
                room,
                dict(
                    action='message_room_bot', params=dict(
                        room=room, user='wikipedia chat bot!', message=msg, image='https://en.wikipedia.org/static/images/project-logos/enwiki.png')
                )
            )
            return
        from app.movies import search_reg
        movie_msg, movie_poster = search_reg(message)
        if movie_msg:
            self.cache.publish_message(
                room,
                dict(
                    action='message_room_bot', params=dict(
                        room=room, user='movie db chat bot!',
                        message=movie_msg,
                        image=movie_poster)
                )
            )

    async def writing_message_room(self, room, user, **kwargs):
        self.cache.publish_message(room, dict(action='writing_message_room', params=dict(room=room, user=self.user, image=self.thumbnail)))

    async def get_rooms(self, **kwargs):
        rooms = self.cache.lget('rooms')
        await self.send(
            {
                'type': 'websocket.send', 
                'text': dumps(
                            {'action': 'get_rooms',
                            'params': {'rooms': rooms}
                            })
            }
        )

    async def create_room(self, room, **kwargs):
        if room in self.rooms:
            await self.send(dict(type='websocket.send', text=f'{room} already exist'))
            return
        self.cache.lset('rooms', room)
        self.rooms.append(room)
        await self.send(dict(type='websocket.send', text=f'room {room} created'))

