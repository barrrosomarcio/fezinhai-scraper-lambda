from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class PremiacaoDto:
    vencedores: int
    premio: float

@dataclass
class LotofacilPremiacaoDto:
    quinze: PremiacaoDto
    quatorze: PremiacaoDto
    treze: PremiacaoDto
    doze: PremiacaoDto
    onze: PremiacaoDto

@dataclass
class LotofacilResultDto:
    concurso: int
    data: datetime
    dezenas: List[str]
    premiacoes: LotofacilPremiacaoDto
    acumulou: bool
    acumuladaProxConcurso: float
    dataProxConcurso: str
    proxConcurso: int
    timeCoracao: str
    mesSorte: str

@dataclass
class SaveResultsDto:
    results: List[LotofacilResultDto] 