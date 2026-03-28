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
from tokens import TokenType

# Nova função auxiliar: resolve o valor apenas na hora exata de usar
def resolver_valor(item, memoria_global):
    """
    Se o item for uma referência a uma variável (ex: ("VAR", "TOTAL")),
    busca o valor real no dicionário. Caso contrário, retorna o próprio número.
    """
    if isinstance(item, tuple) and item[0] == "VAR":
        return memoria_global.get(item[1], 0.0) # Retorna 0.0 se a variável não existir (spec do professor)
    return float(item)


def executarExpressao(tokens, memoria_global, historico_resultados, linha_atual):
    pilha = []
    
    i = 0
    while i < len(tokens):
        t = tokens[i]
        
        # 1. Ignora parênteses, ERROS e EOF
        if t.tipo in (TokenType.PARENTESES, TokenType.EOF, TokenType.ERRO):
            i += 1
            continue
            
        # 2. Números vão direto para a pilha
        if t.tipo == TokenType.NUMERO_REAL:
            pilha.append(float(t.valor))
            i += 1
            continue
            
        # 3. Operadores desempilham os últimos 2 itens (resolvem variáveis se houver) e calculam
        if t.tipo == TokenType.OPERADOR:
            if len(pilha) < 2:
                raise ValueError(f"Faltam operandos para o operador '{t.valor}'")
            
            b_raw = pilha.pop() # Último da pilha
            a_raw = pilha.pop() # Penúltimo da pilha
            
            # Resolve os valores reais ANTES da matemática (caso sejam variáveis)
            b = resolver_valor(b_raw, memoria_global)
            a = resolver_valor(a_raw, memoria_global)
            
            op = t.valor
            if op == '+':
                resultado = a + b
            elif op == '-':
                resultado = a - b
            elif op == '*':
                resultado = a * b
            elif op == '/':
                if b == 0: raise ValueError("Erro: Divisão por zero")
                resultado = a / b
            elif op == '//':
                if b == 0: raise ValueError("Erro: Divisão por zero")
                # Trunca em direção ao zero, imitando vcvtr.s32 do ARM
                resultado = float(int(a / b)) 
            elif op == '%':
                if b == 0: raise ValueError("Erro: Divisão por zero")
                # a - (b * trunc(a/b))
                resultado = a - (b * float(int(a / b)))
            elif op == '^':
                resultado = float(a ** int(b))
                
            pilha.append(resultado)
            i += 1
            continue
            
        # 4. Memória (Load ou Store) - Agora usando regras de Pilha RPN
        if t.tipo == TokenType.MEMORIA:
            if t.valor == "MEM":
                # É um comando de STORE explícito. 
                # O formato esperado é (V VARNAME MEM), logo a pilha tem que ter o NOME no topo e o VALOR embaixo.
                if len(pilha) < 2:
                    raise ValueError("Comando 'MEM' requer um valor e uma variável na pilha (Ex: 5.0 TOTAL MEM)")
                
                nome_var_raw = pilha.pop()
                valor_raw = pilha.pop()
                
                # Extrai a string do nome da variável
                if isinstance(nome_var_raw, tuple) and nome_var_raw[0] == "VAR":
                    nome_var = nome_var_raw[1]
                else:
                    raise ValueError(f"Comando 'MEM' esperava um nome de variável, mas recebeu: {nome_var_raw}")
                
                # Resolve o valor (caso V seja fruto de outra variável ou conta)
                valor = resolver_valor(valor_raw, memoria_global)
                
                # Salva na memória global
                memoria_global[nome_var] = valor
                
                # Mantém o valor salvo na pilha para que a linha tenha um resultado (compatibilidade com seu Assembly)
                pilha.append(valor)
                
            else:
                # É apenas o NOME de uma variável (ex: X, TOTAL). 
                # Empilha como. Não tentamos ler nem escrever agora.
                pilha.append(("VAR", t.valor))
                
            i += 1
            continue
            
        # 5. Comando RES (Busca no histórico de linhas)
        if t.tipo == TokenType.COMANDO and t.valor == "RES":
            if len(pilha) < 1:
                raise ValueError("Comando 'RES' precisa de um número de offset antes")
            
            n_raw = pilha.pop()
            n_linhas = int(resolver_valor(n_raw, memoria_global))
            
            # Tratamento rigoroso e compatível com o Assembly
            if n_linhas == 0:
                # Se N=0, a linha atual ainda não acabou. Retorna 0.0 por segurança.
                pilha.append(0.0)
            else:
                idx_alvo = linha_atual - n_linhas
                
                if idx_alvo < 0 or idx_alvo >= len(historico_resultados):
                    raise ValueError(f"RES tentou acessar a linha de índice {idx_alvo}, que é inválida.")
                
                # Carrega o resultado antigo para a pilha atual
                pilha.append(historico_resultados[idx_alvo])
                
            i += 1
            continue
            
        raise ValueError(f"Token desconhecido ou não tratado: {t}")

    # Final da execução da linha
    if len(pilha) == 1:
        # Pega o item que sobrou e resolve ele de forma definitiva (caso seja só (VARNAME))
        resultado_final = resolver_valor(pilha[0], memoria_global)
        
        historico_resultados.append(resultado_final) # Salva para futuros (N RES)
        return resultado_final
    else:
        raise ValueError(f"Expressão incompleta: sobraram {len(pilha)} itens na pilha.")
