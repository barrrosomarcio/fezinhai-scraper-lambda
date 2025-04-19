from typing import List
from datetime import datetime
import pandas as pd
from dto import (
    PremiacaoDto,
    LotofacilPremiacaoDto,
    LotofacilResultDto,
    SaveResultsDto
)

def convert_money_to_float(valor: str) -> float:
    """Converte um valor monetário no formato R$ X.XXX,XX para float"""
    if not valor or pd.isna(valor):
        return 0.0
    # Remove o símbolo da moeda e espaços
    valor_limpo = valor.replace('R$', '').replace(' ', '')
    # Substitui vírgula por ponto e remove pontos de milhar
    valor_numerico = valor_limpo.replace('.', '').replace(',', '.')
    return float(valor_numerico)

def create_premiacao(vencedores: int, premio: str) -> PremiacaoDto:
    return PremiacaoDto(
        vencedores=int(vencedores),
        premio=convert_money_to_float(premio)
    )

def map_excel_to_dto(df: pd.DataFrame) -> SaveResultsDto:
    results: List[LotofacilResultDto] = []
    
    for _, row in df.iterrows():
        dezenas = [str(num).zfill(2) for num in sorted([
            row['Bola1'], row['Bola2'], row['Bola3'], row['Bola4'], row['Bola5'],
            row['Bola6'], row['Bola7'], row['Bola8'], row['Bola9'], row['Bola10'],
            row['Bola11'], row['Bola12'], row['Bola13'], row['Bola14'], row['Bola15']
        ])]
        
        premiacoes = LotofacilPremiacaoDto(
            quinze=create_premiacao(row['Ganhadores 15 acertos'], row['Rateio 15 acertos']),
            quatorze=create_premiacao(row['Ganhadores 14 acertos'], row['Rateio 14 acertos']),
            treze=create_premiacao(row['Ganhadores 13 acertos'], row['Rateio 13 acertos']),
            doze=create_premiacao(row['Ganhadores 12 acertos'], row['Rateio 12 acertos']),
            onze=create_premiacao(row['Ganhadores 11 acertos'], row['Rateio 11 acertos'])
        )
        
        # Calcula a data do próximo concurso (assumindo que será no próximo dia útil)
        data_sorteio = pd.to_datetime(row['Data Sorteio'], dayfirst=True)
        data_prox_concurso = data_sorteio + pd.Timedelta(days=1)
        
        result = LotofacilResultDto(
            concurso=int(row['Concurso']),
            data=data_sorteio,
            dezenas=dezenas,
            premiacoes=premiacoes,
            acumulou=row['Ganhadores 15 acertos'] == 0,
            acumuladaProxConcurso=convert_money_to_float(row['Acumulado 15 acertos']),
            dataProxConcurso=data_prox_concurso.strftime('%Y-%m-%d'),
            proxConcurso=int(row['Concurso']) + 1,
            timeCoracao='',  # Campo não existe mais no Excel
            mesSorte=''      # Campo não existe mais no Excel
        )
        
        results.append(result)
    
    return SaveResultsDto(results=results) 