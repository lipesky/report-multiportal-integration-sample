from collections import namedtuple
from typing import Any, Iterator, List
from pydantic import BaseModel
import re

class Vehicle(BaseModel):
    id: int | None = None
    codigorf: Any | None = None
    odometroGps: Any | None = None
    dataAquisicao: int | None = None
    distanciaKmFrete: Any | None = None
    kmManual: Any | None = None
    horimetroManual: Any | None = None
    horimetroAtual: Any | None = None
    kmAtual: Any | None = None
    statusVenda: Any | None = None
    dataAtivado: Any | None = None
    dataCadastrado: int | None = None
    dataCancelado: int | None = None
    fuso: int | None = None
    deletado: Any | None = None
    status: str | None = None
    finalizado: Any | None = None
    renavam: int | None = None
    vin: str | None = None
    anoFabricacao: int | None = None
    anoModelo: int | None = None
    placa: str | None = None
    dataInstalacao: Any | None = None
    tipoMonitoramento: str | None = None
    marca: str | None = None
    modelo: str | None = None
    cor: str | None = None
    descricao: str | None = None
    frota: str | None = None
    tipo: str | None = None
    assistencia: Any | None = None
    usuarioCriacao: int | None = None
    proprietarioId: int | None = None
    proprietario: str | None = None
    grupos: List[Any] | None = None
    motoristas: Any | None = None
    dispositivos: List[Any] | None = None
    empresaId: int | None = None


    '''Parses information filled in frota field to a dict, once multiportal does not have support for this field
    Information is stored as examples: 'A-12' 'A-20 B-23'
    '''
    def get_expected_occupations(self) -> dict:
        if self.frota is None or self.frota == '':
            return {}
        matches_iter = re.finditer(
            r'([a-zA-Z]+)\s*-([0-9]+)',
            self.frota,
        )
        result = {}
        for x in matches_iter:
            result[x.group(1)] = x.group(2)
        return result
    
    def get_city_zone(self) -> dict:
        if self.descricao is None or self.descricao == '':
            return {}
        matches_iter: Iterator[re.Match] = re.finditer(
            r'([a-z])-([a-zA-Z-]+)',
            self.descricao,
            re.IGNORECASE
        )
        result = {}
        for x in matches_iter:
            result[x.group(1)] = x.group(2)
        return result
    
    def get_branches(self) -> List[str]:
        if self.descricao is None or self.descricao == '':
            return {}
        matches_iter: Iterator[re.Match] = re.finditer(
            r'FILIAL-((?:[a-zA-ZãÃ-0-9çÇ])+)',
            self.descricao,
            re.IGNORECASE
        )
        result = []
        for x in matches_iter:
            result.append(x.group(1))
        return result