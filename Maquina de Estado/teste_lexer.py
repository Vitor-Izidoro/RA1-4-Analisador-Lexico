# Este arquivo contém testes unitários para o analisador léxico (lexer) da máquina de estados.
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
import unittest
from tokens import TokenType
from lexer import parseExpressao

class TestAnalisadorLexico(unittest.TestCase):

    def test_operacao_basica(self):
        linha = "(3.14 2.0 +)"
        tokens = parseExpressao(linha)
        
        self.assertEqual(len(tokens), 5)
        
        self.assertEqual(tokens[0].tipo, TokenType.PARENTESES)
        self.assertEqual(tokens[1].tipo, TokenType.NUMERO_REAL)
        self.assertEqual(tokens[2].tipo, TokenType.NUMERO_REAL)
        self.assertEqual(tokens[3].tipo, TokenType.OPERADOR)
        self.assertEqual(tokens[4].tipo, TokenType.PARENTESES)
        
        # Verifica os valores lidos
        self.assertEqual(tokens[1].valor, "3.14")
        self.assertEqual(tokens[3].valor, "+")

    def test_comando_res(self):
        linha = "(5 RES)"
        tokens = parseExpressao(linha)
        
        self.assertEqual(tokens[1].tipo, TokenType.NUMERO_REAL)
        self.assertEqual(tokens[1].valor, "5")
        self.assertEqual(tokens[2].tipo, TokenType.COMANDO)
        self.assertEqual(tokens[2].valor, "RES")

    def test_comando_memoria(self):
        linha = "(10.5 CONTADOR)"
        tokens = parseExpressao(linha)
        
        self.assertEqual(tokens[1].tipo, TokenType.NUMERO_REAL)
        self.assertEqual(tokens[1].valor, "10.5")
        self.assertEqual(tokens[2].tipo, TokenType.MEMORIA)
        self.assertEqual(tokens[2].valor, "CONTADOR")

    def test_divisao_inteira(self):
        linha = "(10 3 //)"
        tokens = parseExpressao(linha)
        
        self.assertEqual(tokens[3].tipo, TokenType.OPERADOR)
        self.assertEqual(tokens[3].valor, "//")


    def test_caractere_invalido(self):
        linha = "(3.14 2.0 &)"
        tokens = parseExpressao(linha)
        
        token_erro = tokens[3]
        self.assertEqual(token_erro.tipo, TokenType.ERRO)
        self.assertEqual(token_erro.valor, "&")

    def test_numero_malformado_multiplos_pontos(self):
        linha = "(3.14.5 2.0 +)"
        tokens = parseExpressao(linha)
        
        self.assertEqual(tokens[1].tipo, TokenType.ERRO)
        self.assertEqual(tokens[1].valor, "3.14.5")

    def test_numero_malformado_virgula(self):
        linha = "(3,45 2.0 +)"
        tokens = parseExpressao(linha)
        
        self.assertEqual(tokens[1].tipo, TokenType.ERRO)

    def test_parenteses_desbalanceados_lexico(self):
        linha = "((3.14 2.0 +)"
        tokens = parseExpressao(linha)
        
        self.assertEqual(tokens[-1].tipo, TokenType.ERRO)
        self.assertEqual(tokens[-1].valor, "PARENTESES_DESBALANCEADOS")


if __name__ == '__main__':
    unittest.main(verbosity=2)