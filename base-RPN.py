def calculadora_pilha_espacos():
    pilha_numeros = []
    pilha_sinais = []

    print("Insira os números e operações separados por ESPAÇO.")
    print("Exemplo: para calcular 1 + (3 * 4), digite: 1 3 4 * +")
    entrada = input("-> ")

    # O método split() quebra o texto onde tem espaço. 
    # "1 34 5 +" se transforma na lista ["1", "34", "5", "+"]
    itens = entrada.split()

    for item in itens:
        # Tenta converter o item para um número inteiro
        # Usamos try/except porque é a forma mais segura de testar se uma string 
        # é um número (inclusive números negativos, como "-5")
        try:
            numero = int(item)
            pilha_numeros.append(numero)
            
        except ValueError:
            # Se der erro (ValueError), significa que não é um número. 
            # Então verificamos se é um sinal matemático.
            if item in ["+", "-", "*", "/"]:
                pilha_sinais.append(item)
                
                # Garante que temos pelo menos 2 números na pilha
                if len(pilha_numeros) < 2:
                    print(f"Erro: Faltam números na pilha para usar o '{item}'.")
                    return

                # Esquema LIFO: tira o último e o penúltimo
                ultimo = pilha_numeros.pop()
                penultimo = pilha_numeros.pop()

                # Lógica de operação
                if item == '+':
                    resultado = penultimo + ultimo
                elif item == '-':
                    resultado = penultimo - ultimo
                elif item == '*':
                    resultado = penultimo * ultimo
                elif item == '/':
                    if ultimo == 0:
                        print("Erro: Impossível dividir por zero.")
                        return
                    # Usamos divisão inteira (//) para manter tudo como 'int',
                    # ou você pode usar (/) se não se importar em virar 'float'
                    resultado = penultimo // ultimo 
                
                # Devolve o resultado para o topo da pilha
                pilha_numeros.append(resultado)
                
            else:
                print(f"Aviso: O item '{item}' não é um número nem um sinal válido e foi ignorado.")

    # Exibe os resultados
    print("\n--- RESULTADO FINAL ---")
    if len(pilha_numeros) == 1:
        print(f"Resultado: {pilha_numeros[0]}")
        print(f"Sinais na ordem em que apareceram: {pilha_sinais}")
    elif len(pilha_numeros) > 1:
        print(f"Aviso: Faltaram sinais! A conta não terminou.")
        print(f"Números que sobraram na pilha: {pilha_numeros}")
    else:
        print("Nenhuma operação válida foi feita.")

# Executa o programa
calculadora_pilha_espacos()
