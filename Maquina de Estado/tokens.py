# Vocabulario de tokens para a máquina de estado do interpretador de expressões matemáticas
# =============================================================================
#  Integrantes:
#    [Nome completo] - [GitHub]
#    Crystofer Demetino dos Santos - CrySamuel
#    Gabriel Simini - GalSimini
#    Vitor Rodrigues Izidoro - vitor-izidoro
#
#  Grupo no Canvas: RA1-4
#  Disciplina: Interpretadores B - Noite
#  Professor: Frank Coelho de Alcântara
# =============================================================================
from enum import Enum
from dataclasses import dataclass

class TokenType(Enum):
    PARENTESES = "PARENTESES"
    NUMERO_REAL = "NUMERO_REAL"
    OPERADOR = "OPERADOR"
    COMANDO = "COMANDO"  
    MEMORIA = "MEMORIA"  
    ERRO = "ERRO"
    EOF = "EOF"          

@dataclass # Armazenar informações sobre os tokens identificados
class Token:
    tipo: TokenType
    valor: str
    
    def __repr__(self):
        return f"Token({self.tipo.name}, '{self.valor}')"