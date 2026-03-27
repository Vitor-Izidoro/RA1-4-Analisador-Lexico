# Memoria de curto prazo para o lexer: armazena o texto, a posição atual, o buffer de construção do token e a lista de tokens finalizados
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
from tokens import Token

class LexerContext:
    def __init__(self, texto: str):
        self.texto = texto
        self.posicao = 0
        self.buffer = ""
        self.tokens = []
        self.parenteses = 0

    def char_atual(self) -> str:
        if self.posicao < len(self.texto):
            return self.texto[self.posicao]
        return ""

    def avancar(self):
        self.posicao += 1

    def adicionar_token(self, tipo, valor):
        self.tokens.append(Token(tipo, valor))
        self.buffer = ""