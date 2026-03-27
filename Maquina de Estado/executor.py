from tokens import TokenType

# Função auxiliar idêntica à do gerarAssembly.py para olhar o próximo token
def peek_next_significant(tokens, start):
    for j in range(start, len(tokens)):
        if tokens[j].tipo not in (TokenType.PARENTESES, TokenType.EOF):
            return tokens[j]
    return None

def executarExpressao(tokens, memoria_global, historico_resultados, linha_atual):
    pilha = []
    pending_mem_var = None
    
    i = 0
    while i < len(tokens):
        t = tokens[i]
        
        # 1. Ignora parênteses, ERROS e EOF (o Lexer já validou antes)
        if t.tipo in (TokenType.PARENTESES, TokenType.EOF, TokenType.ERRO):
            i += 1
            continue
            
        # 2. Números vão direto para a pilha (como float para simular IEEE 754 de 64 bits)
        if t.tipo == TokenType.NUMERO_REAL:
            pilha.append(float(t.valor))
            i += 1
            continue
            
        # 3. Operadores desempilham os últimos 2 números e calculam
        if t.tipo == TokenType.OPERADOR:
            if len(pilha) < 2:
                raise ValueError(f"Faltam operandos para o operador '{t.valor}'")
            
            b = pilha.pop() # Último da pilha
            a = pilha.pop() # Penúltimo da pilha
            
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
                # int(a/b) trunca em direção ao zero, imitando a instrução vcvtr.s32 do ARM
                resultado = float(int(a / b)) 
            elif op == '%':
                if b == 0: raise ValueError("Erro: Divisão por zero")
                # Lógica do ARM: a - (b * trunc(a/b))
                resultado = a - (b * float(int(a / b)))
            elif op == '^':
                resultado = float(a ** int(b))
                
            pilha.append(resultado)
            i += 1
            continue
            
        # 4. Memória (Load ou Store) - Usando sua heurística do Assembly
        if t.tipo == TokenType.MEMORIA:
            if t.valor == "MEM":
                if pending_mem_var is None:
                    raise ValueError("Comando 'MEM' sem variável precedente")
                
                # STORE explícito: guarda o topo da pilha no dicionário (sem dar pop!)
                memoria_global[pending_mem_var] = pilha[-1] 
                pending_mem_var = None
                i += 1
                continue
                
            proximo = peek_next_significant(tokens, i + 1)
            
            # Checa se o próximo token será a keyword MEM
            if proximo is not None and proximo.tipo == TokenType.MEMORIA and proximo.valor == "MEM":
                pending_mem_var = t.valor
                i += 1
                continue
                
            # Heurística implícita: Se o próximo é operador, é um Load
            if proximo is not None and proximo.tipo == TokenType.OPERADOR:
                pilha.append(memoria_global.get(t.valor, 0.0))
            # Se tem valor na pilha e não tem operador pela frente, é um Store
            elif len(pilha) > 0:
                memoria_global[t.valor] = pilha[-1] 
            # Caso contrário, é um Load
            else:
                pilha.append(memoria_global.get(t.valor, 0.0))
                
            i += 1
            continue
            
        # 5. Comando RES (Busca no histórico de linhas)
        if t.tipo == TokenType.COMANDO and t.valor == "RES":
            if len(pilha) < 1:
                raise ValueError("Comando 'RES' precisa de um número de offset antes")
            
            n_linhas = int(pilha.pop())
            idx_alvo = linha_atual - n_linhas
            
            if idx_alvo < 0 or idx_alvo >= len(historico_resultados):
                raise ValueError(f"RES tentou acessar a linha de índice {idx_alvo}, que é inválida.")
            
            # Carrega o resultado antigo para a pilha atual
            pilha.append(historico_resultados[idx_alvo])
            i += 1
            continue
            
        raise ValueError(f"Token desconhecido ou não tratado: {t}")

    # No final de cada linha, o resultado deve ser o ÚNICO item na pilha
    if len(pilha) == 1:
        resultado_final = pilha[0]
        historico_resultados.append(resultado_final) # Salva para futuros (N RES)
        return resultado_final
    else:
        raise ValueError(f"Expressão incompleta: sobraram {len(pilha)} itens na pilha.")