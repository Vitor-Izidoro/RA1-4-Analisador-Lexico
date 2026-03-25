# Codigo principal da maquina de estado

from lexer_context import LexerContext
from states import estadoInicial
from tokens import TokenType
import json

def parseExpressao(linha: str) -> list:
    ctx = LexerContext(linha)
    
    estado_atual = estadoInicial
    
    while estado_atual is not None:
        estado_atual = estado_atual(ctx)
        
        if ctx.tokens and ctx.tokens[-1].tipo == TokenType.ERRO:
            print(f"Erro Léxico encontrado na palavra: {ctx.tokens[-1].valor}")
            break
            
    return ctx.tokens

def salvar_tokens_json(dados_para_salvar: dict, nome_arquivo: str = "tokens_ultima_execucao.txt"):

    with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
        json.dump(dados_para_salvar, arquivo, indent=4, ensure_ascii=False)
    print(f"\n[+] Última execução salva com sucesso no arquivo '{nome_arquivo}'")

if __name__ == "__main__":
    testes = [
        "(3.14 2.0 +)",
        "(5 RES)",
        "(10.5 CONTADOR MEM)",
        "(3.14.5 2.0 +)",
        "(4.0 2.0 //)",
        "(10.5 CONTADOR MEM)",
        "(((10.0.0 5,5 +) (var MINUSCULA MEM) 123@456) (3.14 0.001 /) (7.0 0.0 //) (A B +) (999.999 ERRO_MACRO MEM) (2 RES))",
        "((((((12345.6789 9876.5432 *) (0.0001 2.0 /) +) (100.0 3.0 //) -) (45.0 6.0 %) *) 2.0 ^) (MEGA_VAR MEM) (1 RES))"
    ]

    ultimo_bloco = {}

    for linha in testes:
        print(f"\nAnalisando: {linha}")
        
        tokens = parseExpressao(linha)
        
        for t in tokens:
            print(f"  -> {t}")
            
        tokens_formatados = [{"tipo": t.tipo.name, "valor": t.valor} for t in tokens]
        

        ultimo_bloco = {
            "expressao": linha,
            "tokens": tokens_formatados
        }

    if ultimo_bloco:
        salvar_tokens_json(ultimo_bloco)