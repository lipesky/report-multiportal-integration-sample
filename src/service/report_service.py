from math import floor
import re
import logging
import dateutil
import dateutil.tz
from openpyxl.workbook import Workbook
from openpyxl.cell import Cell
from openpyxl.styles import Font, Color, colors
from datetime import datetime
from functools import lru_cache
from typing import Annotated, List

from fastapi import Depends
from src.multiportal_client.model.dto.identification_dto import IdentificationDto
from src.multiportal_client.model.dto.vehicle_occupation_dto import VehicleOccupationDto
from src.model.settings import Settings, get_settings
from src.multiportal_client.model.multiportal_vehicle import Vehicle
from src.multiportal_client.model.multiportal_posicao import MultiportalPosicao
from src.service.multiportal_api_client import MultiportalApiClient, get_multiportal_client
# from src.service.mocked_occupation_data import mocked_occupation_data

shifts = {
    'A': {
        'start': '03:00:00',
        'end': '06:00:00'
    },
    'B': {
        'start': '13:00:00',
        'end': '16:00:00'
    }
}
branches = [
    'MTX', 'TQT'
]
class ReportService():

    def __init__(self, api_client: MultiportalApiClient, settings: Settings):
        self.api_client = api_client
        self.settings = settings
        self.plate_capacity_pattern = re.compile(r'^.*[^0-9]([0-9]+)l$', re.IGNORECASE)

    '''builds occupation report in csv format'''
    async def occupation_report_xlsx(self, date: str, shift_id: str):
        # date_str = date[0:10]
        # start_date = datetime.fromisoformat('{date} {time}'.format(date=date_str, time=shifts[shift_id]['start']))
        # end_date = datetime.fromisoformat('{date} {time}'.format(date=date_str, time=shifts[shift_id]['end']))
        occupation_data = await self.build_data_for_ocuppation_report(date, shift_id)
        # mock
        # occupation_data = list(
        #     map(
        #         lambda x: VehicleOccupationDto.model_validate(x),
        #         mocked_occupation_data
        #     )
        # )
        book = Workbook()
        sheet = book.active
        index = 3
        title = 'Relatório de ocupação para {date} - {shift_id}'.format(
            date=datetime.fromisoformat(date).strftime('%d/%m/%Y'), 
            shift_id=shift_id
        )
        sheet['A1'] = title
        cell: Cell = sheet.cell(1, 1)
        title_font = Font(bold=True, size=14)
        cell.font = title_font
        sheet.merge_cells('A1:I1')
        for vehicle in occupation_data:
            sheet['A'+str(index)] = 'Veículo:'
            sheet['B'+str(index)] = vehicle.plate
            if vehicle.city_zone:
                sheet['E'+str(index)] = 'Zona:'
                sheet['F'+str(index)] = vehicle.city_zone
            sheet.merge_cells('B{index}:D{index}'.format(index=index))
            sheet['H'+str(index)] = 'Filiais:'
            sheet['I'+str(index)] = ', '.join(vehicle.branches)
            index = index+1
            sheet['A'+str(index)] = 'Capacidade:'
            sheet['B'+str(index)] = vehicle.capacity
            sheet['D'+str(index)] = 'Passageiros:'
            sheet['E'+str(index)] = vehicle.quantity_identifications
            sheet['G'+str(index)] = 'Ocupação:'
            sheet['H'+str(index)] = '{:.2f}'.format(vehicle.occupation * 100.0)+ r'%'
            index = index+1
            sheet['A'+str(index)] = 'Qntd. esperada:'
            if vehicle.expected_quantity:
                sheet['B'+str(index)] = vehicle.expected_quantity
            sheet['D'+str(index)] = 'Tempo de viagem:'
            if vehicle.travel_time_seconds:
                hours = floor((vehicle.travel_time_seconds or 0) / 3600)
                minutes = floor(((vehicle.travel_time_seconds or 0) % 3600) / 60)
                seconds = vehicle.travel_time_seconds % 60
                sheet['E'+str(index)] = '{h}:{m}:{s}'.format(h=hours,m=minutes,s=seconds)
            sheet['G'+str(index)] = 'Ocup. esperada'
            if vehicle.expected_occupation: 
                sheet['H'+str(index)] = '{:.2f}'.format(vehicle.expected_occupation * 100.0)+ r'%'
            index = index+1
            sheet['A'+str(index)] = 'Identificações:'
            index = index+1
            for identification in vehicle.identifications:
                sheet.merge_cells('B{index}:D{index}'.format(index=index))
                sheet['B'+str(index)] = datetime.fromisoformat(identification.date).strftime('%d/%m/%Y %H:%M:%S')
                sheet['E'+str(index)] = identification.text
                index = index+1
            index = index+2
        return (book, title)

    '''Fetchs and process data for ocuppation report'''
    async def build_data_for_ocuppation_report(self, date: str, shift_id: str) -> List[VehicleOccupationDto]:
        date_str = date[0:10]
        start_date = datetime.fromisoformat('{date} {time}'.format(date=date_str, time=shifts[shift_id]['start']))
        end_date = datetime.fromisoformat('{date} {time}'.format(date=date_str, time=shifts[shift_id]['end']))
        print('start_date', start_date)
        vehicles_occupation: List[VehicleOccupationDto] = []
        all_vehicles = await self.api_client.get_vehicle_list()
        vehicles = list(
            filter(
                lambda x: x.proprietarioId == self.settings.multiportal_empresa_target_id,
                all_vehicles
            )
        )
        for vehicle in vehicles:
            capacity = self.get_capacity_from_vehicle(vehicle)
            if capacity:
                identifications: List[MultiportalPosicao] = await self.get_identifications_for_vehicle(vehicle.id, start_date, end_date)
                travel_time_seconds = None
                if len(identifications) > 0:
                    travel_time_seconds = (identifications[len(identifications) - 1].dataEquipamento/1000) - (identifications[0].dataEquipamento/1000)
                expected_quantity = vehicle.get_expected_occupations().get(shift_id)
                expected_occupation = None
                if expected_quantity is not None:
                    expected_occupation = float(len(identifications)) / float(expected_quantity)
                vehicles_occupation.append(
                    VehicleOccupationDto(
                        vehicle_id=vehicle.id,
                        plate=vehicle.placa,
                        capacity=capacity,
                        identifications=list(
                            map(
                                lambda x: IdentificationDto(
                                    text=x.evento,
                                    date=datetime.fromtimestamp(
                                        x.dataEquipamento/1000,
                                        #tz=dateutil.tz.tzoffset(None, (vehicle.fuso if vehicle.fuso else -3) * (3600))
                                    ).isoformat(),
                                ),
                                identifications,
                            )
                        ),
                        quantity_identifications=len(identifications),
                        occupation=(float(len(identifications))/float(capacity)),
                        expected_quantity=expected_quantity,
                        expected_occupation=expected_occupation,
                        travel_time_seconds=travel_time_seconds,
                        city_zone=vehicle.get_city_zone().get(shift_id),
                        branches=vehicle.get_branches()
                    )
                )
            else:
                logging.warning(
                    'skipping vehicle without capacity in plate: {id} - {plate}'.format(
                        id=vehicle.id,
                        plate=vehicle.placa
                    )
                )
        return vehicles_occupation

    def get_capacity_from_vehicle(self, vehicle: Vehicle) -> int | None:
        _match: re.Match[str] | None = self.plate_capacity_pattern.match(vehicle.placa)
        if _match is not None:
            return int(_match.group(1))
        return None
    
    async def get_identifications_for_vehicle(self, vehicle_id: int, start_date: datetime, end_date: datetime) -> List[MultiportalPosicao]:
        all_positions = await self.api_client.get_vehicle_positions(
            vehicle_id, 
            start_date=start_date, 
            end_date=end_date,
        )
        if all_positions is None or len(all_positions) == 0:
            logging.info('no positions for vehicle {vehicle_id}'.format(vehicle_id=vehicle_id))
            return []
        all_identifications = list(
            sorted(
                filter(
                    lambda x: x.evento.lower().startswith('identifica'),
                    all_positions 
                ),
                key=lambda x: x.dataEquipamento,
            )            
        )
        identifications: List[MultiportalPosicao] = []
        for ident in all_identifications:
            if not any(
                map(
                    lambda x: x.evento == ident.evento, 
                    identifications
                )
            ):
                identifications.append(ident)

        del all_positions
        del all_identifications
        if identifications is None or len(identifications) == 0:
            logging.info('no identifications for vehicle {vehicle_id}'.format(vehicle_id=vehicle_id))
        return identifications

@lru_cache()
def get_report_service(api_client: Annotated[MultiportalApiClient, Depends(get_multiportal_client)],
                       settings: Annotated[Settings, Depends(get_settings)]):
    return ReportService(api_client, settings)