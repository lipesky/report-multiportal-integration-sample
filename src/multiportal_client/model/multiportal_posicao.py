from typing import Any, List
from pydantic import BaseModel

class MultiportalPosicaoComponent(BaseModel):
    id: int | None = None
    nome: str | None = None
    valor: str | None = None

class MultiportalPosicao(BaseModel):
    online: bool | None = None
    eventoId: int | None = None
    evento: str | None = None
    sequencia: int | None = None
    referencia: str | None = None
    dataEquipamento: int | None = None
    dataGPS: int | None = None
    dataGateway: int | None = None
    dataProcessamento: int | None = None
    tipo: str | None = None 
    id: str | None = None
    texto: str | None = None
    binario: str | None = None
    validade: bool | None = None
    latitude: float | None = None
    longitude: float | None = None
    velocidade: int | None = None
    proa: int | None = None
    altitude: int | None = None
    hdop: int | None = None
    satelites: int | None = None
    livre: str | None = None
    endereco: str | None = None
    motorista: str | None = None
    dispositivoid: int | None = None
    numerostr: str | None = None
    fabricante: int | None = None
    bateria_perc: Any | None = None
    componentes: List[MultiportalPosicaoComponent] | None = None
