import time

from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer, AsyncConsumer
import json
from .logic import Processing, Suggest
from .models import PositionInfo, Training
from channels.db import database_sync_to_async




class ChessConsumer(AsyncWebsocketConsumer):
     async def connect(self):
        print('ok')
        await self.accept()

     async def disconnect(self, code):
         pass


     async def receive(self, text_data=None, bytes_data=None):
        t1 = time.time()

        r = {}
        text_data_json = json.loads(text_data)

        print('request', text_data_json)


        if text_data_json['action'] == 'sendMove':
            r = await self.send_move(text_data_json)

        elif text_data_json['action'] == 'sendCP':
            r = await self.send_cp(text_data_json)

        elif text_data_json['action'] == 'hint':

            r = await self.hint(text_data_json)

        elif text_data_json['action'] == 'sendSuggest':
            r = await self.suggest(text_data_json)

        elif text_data_json['action'] == 'reset':
            r = await self.reset(text_data_json)

        t2 = time.time()
        r['time'] = f'{round(t2 - t1, 2)}s'
        print('response', r['time'], r)

        await self.send(text_data=json.dumps(r))




     @database_sync_to_async
     def hint(self, text_data_json):
        r = dict()
        r['status'] = 'hint'
        try:
            obj = Training.objects.filter(move__initial_fen__fen=text_data_json['fen']).get()
            r['move_uci'] = obj.move.uci
        except KeyError:
            r['move_uci'] = 'Not Found'
        return r


     @database_sync_to_async
     def reset(self, text_data_json):
        r = {}
        r['status'] = 'reset'
        obj = Training.objects.filter(move__initial_fen__fen=text_data_json['fen'])
        print(len(Training.objects.all()))
        r['record'] = len(obj) == 0

        return r


     @database_sync_to_async
     def send_move(self, text_data_json):
        r = {}
        processing_obj = Processing(text_data_json)
        processing_obj.get_response()

        r['record'] = processing_obj.record
        r['move_uci'] = processing_obj.response_move
        r['status'] = processing_obj.status
        r['stats'] = processing_obj.stats
        return r

     @database_sync_to_async
     def send_cp(self, text_data_json):
        r = {}
        r['status'] = 'cp'
        obj = PositionInfo.objects.filter(fen__fen=text_data_json['fen']).get()
        cp = obj.cp
        r['cp'] = cp

        return r


     @database_sync_to_async
     def suggest(self, text_data_json):
        r = {}
        x = Suggest(text_data_json)
        r['status'] = 'suggest'
        r['listMove'] = x.create_list()

        return r
