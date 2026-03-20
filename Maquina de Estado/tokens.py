# Vocabulario de tokens para a máquina de estado do interpretador de expressões matemáticas

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