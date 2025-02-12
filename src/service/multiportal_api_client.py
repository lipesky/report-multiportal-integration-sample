# import os, json
import httpx
import logging
from asyncio import Lock, sleep, create_task
from datetime import datetime
from functools import lru_cache, reduce
from typing import Annotated, Any, List
from fastapi import Depends
from time import time

from src.service.simple_async_queue import SimpleTrottleQueue
from src.service.queue_thottle import TrottleQueue
from src.multiportal_client.model.multiportal_posicao import MultiportalPosicao
from src.multiportal_client.model.multiportal_vehicle import Vehicle
from src.model.settings import Settings, get_settings
from src.multiportal_client.model.multiportal_respose_wrapper import MultiportalResponseWrapper
from src.multiportal_client.model.multiportal_handshake import MultiportalHandShake


class MultiportalApiClient():
    token: str | None = None
    expiration: int | None = None
    max_retries = 5
    queue_processing_min_interval_seconds = 2
    trottle_queue = SimpleTrottleQueue(queue_processing_min_interval_seconds)

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.Client(
            base_url=settings.multiportal_service_url,
            timeout=None
        )
        self.client.event_hooks = {
            'request': [self.on_request],
            'response': [self.on_response],
        }

    def on_request(self, request: httpx.Request):
        if self.token is None or (time() >= self.expiration and not request.extensions.get('is_reauth')):
            self._authenticate()
        request.headers['token'] = self.token        
        request.headers['Content-Type'] = 'application/json'
        return request
        #     print('token expirated, reauthenticaticating')
        #     def cb():
        #         request.headers['token'] = self.token        
        #         request.headers['Content-Type'] = 'application/json'
        #         self.client.send(request)
        #     create_task(self.authenticate()).add_done_callback(cb)
        #     request.a
        # request.headers['token'] = self.token        
        # request.headers['Content-Type'] = 'application/json'
        # return request
    
    def on_response(self, response: httpx.Response):
        if response.status_code == 400 and not response.request.extensions.get('is_reauth'):
            self.expiration = 0 # to force reauth
            request = response.request
            request.extensions = {
                'is_reauth': True,
            }
            return self.client.send(request)
        return response
    
    async def _retry_method(self, cb: Any, **kargs):
        count = 0
        while count < self.max_retries:
            try:
                result = await self.trottle_queue.add_queue(cb, **kargs)
                return await result
            except Exception as e:
                result = await self.trottle_queue.add_queue(self.authenticate)
                await result
                count = count + 1
                logging.exception(e)
        logging.error('could not execute method with retry police')
        raise Exception('could not execute method with retry police') 

    async def authenticate(self) -> None:
        return self._retry_method(self._authenticate)

    def _authenticate(self) -> None:
        try:
            data = MultiportalHandShake(
                    username=self.settings.multiportal_service_username,
                    password=self.settings.multiportal_service_password,
                    appid=self.settings.multiportal_service_app_id,
                    token=None,
                    expiration=None
                ).model_dump()
            response: httpx.Response = httpx.post(
                '{base_url}/seguranca/logon'.format(base_url=self.settings.multiportal_service_url),
                json=data,
                headers={
                    'Content-Type':  'application/json'
                }
            )        
            failed = False
            if response.status_code == 200:
                wrapper = MultiportalResponseWrapper[MultiportalHandShake].model_validate(response.json())
                if wrapper.status == "OK" and wrapper.responseMessage == "logon.ok":
                    self.token = wrapper.object.token
                    self.expiration = wrapper.object.expiration
                else:
                    failed = True
            else:
                failed = True
            
            if failed:
                raise Exception('failed to authenticate - status: {status}. content: {content}'.format(
                    status=response.status_code, content=response.content)
                )
        except:
            raise
    
    async def get_vehicle_list(self) -> List[Vehicle] | None:
        return await self._retry_method(self._get_vehicle_list)
    
    async def _get_vehicle_list(self) -> List[Vehicle] | None:
        #self.authenticate()
        response: httpx.Response = self.client.post(
            '{base_url}/veiculos'.format(base_url=self.settings.multiportal_service_url),
        )
        if response.status_code == 200:
            body = MultiportalResponseWrapper[List[Vehicle]].model_validate(response.json())
            if body.status == "OK":
                return body.object
            else:
                failed = True
        else:
            failed = True
        
        if failed:
            raise Exception('failed to get vehicle list - status: {status}. content: {content}'.format(
                status=response.status_code, content=response.content)
            )
    
    async def get_vehicle_positions(self, vehicle_id: int, start_date: datetime, end_date: datetime) -> List[MultiportalPosicao] | None:
        return await self._retry_method(self._get_vehicle_positions, vehicle_id=vehicle_id, start_date=start_date, end_date=end_date)
        
    
    async def _get_vehicle_positions(self, vehicle_id: int, start_date: datetime, end_date: datetime) -> List[MultiportalPosicao] | None:
        #self.authenticate()
        # print('trying to get positions for {id}'.format(id=vehicle_id))
        # Test cache: begin
        # filename = os.path.join(os.path.dirname(__file__), '../../cache/positions/{id}.json'.format(id=vehicle_id))
        # if not os.path.exists(os.path.dirname(filename)):
        #     os.makedirs(os.path.dirname(filename))
        # if os.path.exists(filename):
        #     print('cache found ', filename)
        #     with open(filename, 'r') as fopen:
        #         content = reduce(
        #             lambda a,b: a + b,
        #             fopen.readlines()
        #         )
        #         print('returning cached version for vehicle {id}'.format(id=vehicle_id))
        #         return json.loads(content)
        # Test cache: end
        print('start_hour', start_date.isoformat(sep=' ', timespec='seconds'))
        print('end_hour', end_date.isoformat(sep=' ', timespec='seconds'))
        response: httpx.Response = self.client.post(
            '{base_url}/posicoes/veiculo'.format(base_url=self.settings.multiportal_service_url),
            json={
                'id': vehicle_id,
            },
            headers={
                'dataInicial': start_date.isoformat(sep=' ', timespec='seconds')[0:19],
                'dataFinal': end_date.isoformat(sep=' ', timespec='seconds')[0:19],
            }
        )        
        if response.status_code == 200:
            wrapper = MultiportalResponseWrapper[Any].model_validate(response.json())
            
            if wrapper.status == "OK":
                result = list(
                    map(
                        lambda x: MultiportalPosicao.model_validate(x), 
                        reduce(
                            lambda a, b: a + b,
                            map(
                                lambda x: x['posicoes'], 
                                wrapper.object['dispositivos']
                            )
                        )
                    )
                )
                # Test cache: begin
                # with open(filename, 'w') as fopen:
                #     fopen.write(
                #         json.dumps(
                #             list(
                #                 map(
                #                     lambda x: x.model_dump(),
                #                     result
                #                 )
                #             )
                #         )
                #     )
                # Test cache: end
                return result
            else:
                logging.error('status was not OK - {res}'.format(res=response.json()))
                failed = True
        else:
            logging.error('status was not 200 - {status}'.format(status=response.status_code))
            failed = True
        
        if failed:
            raise Exception('failed to get positions list for vehicle {vehicle_id} - status: {status}. content: {content}'.format(
                vehicle_id=vehicle_id, status=response.status_code, content=response.content)
            )


@lru_cache()
def get_multiportal_client(settings: Annotated[Settings, Depends(get_settings)] = Settings()):
    return MultiportalApiClient(
        settings=settings,
    )