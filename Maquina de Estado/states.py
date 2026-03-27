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

def estadoInicial(ctx):
    char = ctx.char_atual()

    # 1. Fim do ficheiro (EOF)
    if char == "":
        return None

    # 2. Ignorar espaços em branco
    if char.isspace():
        ctx.avancar()
        return estadoInicial

    # 3. Parênteses de abertura e fecho
    if char in "()":
        return estadoParenteses

    # 4. Tratamento de números negativos e operador de subtração
    if char == "-":
        # Verificamos o próximo carácter sem avançar o ponteiro do contexto
        proximo = ctx.texto[ctx.posicao + 1] if ctx.posicao + 1 < len(ctx.texto) else ""
        
        if proximo.isdigit():
            # Se for seguido de um dígito, é o início de um número real negativo
            ctx.buffer += char
            ctx.avancar()
            return estadoNumero
        else:
            # Caso contrário, é apenas o operador aritmético de subtração
            return estadoOperador

    # 5. Outros operadores (+, *, %, ^)
    # Nota: O '-' foi removido daqui para ser tratado na lógica acima
    if char in "+*%^":
        return estadoOperador

    # 6. Operadores de divisão (/ ou //)
    if char == "/":
        ctx.buffer += char
        ctx.avancar()
        return estadoDivisao

    # 7. Início de números positivos
    if char.isdigit():
        ctx.buffer += char
        ctx.avancar()
        return estadoNumero

    # 8. Ponto decimal (início de número real sem parte inteira)
    if char == ".":
        ctx.buffer += char
        ctx.avancar()
        return estadoDecimal

    # 9. Início de palavras (RES, MEM ou nomes de variáveis)
    if char.isalpha():
        ctx.buffer += char
        ctx.avancar()
        return estadoPalavra

    # 10. Qualquer outro símbolo não reconhecido (Cai no estado de erro)
    ctx.buffer += char
    ctx.avancar()
    return estadoErro

def estadoParenteses(ctx):
    char = ctx.char_atual()

    if char == "(":
        ctx.parenteses += 1
    elif char == ")":
        ctx.parenteses -= 1

    ctx.adicionar_token(TokenType.PARENTESES, char)
    ctx.avancar()
    return estadoInicial


def estadoOperador(ctx):
    char = ctx.char_atual()

    ctx.adicionar_token(TokenType.OPERADOR, char)
    ctx.avancar()
    return estadoInicial


def estadoDivisao(ctx):
    char = ctx.char_atual()

    if char == "/":  # operador //
        ctx.buffer += char
        ctx.adicionar_token(TokenType.OPERADOR, ctx.buffer)
        ctx.avancar()
    else:  # operador /
        ctx.adicionar_token(TokenType.OPERADOR, ctx.buffer)

    return estadoInicial


def estadoNumero(ctx):
    char = ctx.char_atual()

    if char.isdigit():
        ctx.buffer += char
        ctx.avancar()
        return estadoNumero

    elif char == ".":
        if "." in ctx.buffer:  
            ctx.buffer += char
            ctx.avancar()
            return estadoErro

        ctx.buffer += char
        ctx.avancar()
        return estadoDecimal

    elif char == ",":
        ctx.buffer += char
        ctx.avancar()
        return estadoErro

    elif char.isspace() or char in "()":
        ctx.adicionar_token(TokenType.NUMERO_REAL, ctx.buffer)
        return estadoInicial

    else:
        ctx.buffer += char
        ctx.avancar()
        return estadoErro


def estadoDecimal(ctx):
    char = ctx.char_atual()

    if char.isdigit():
        ctx.buffer += char
        ctx.avancar()
        return estadoDecimal

    elif char == ".":
        ctx.buffer += char
        ctx.avancar()
        return estadoErro

    elif char == ",":
        ctx.buffer += char
        ctx.avancar()
        return estadoErro

    elif char.isspace() or char in "()":
        if ctx.buffer.endswith("."):
            return estadoErro

        ctx.adicionar_token(TokenType.NUMERO_REAL, ctx.buffer)
        return estadoInicial

    else:
        ctx.buffer += char
        ctx.avancar()
        return estadoErro


def estadoPalavra(ctx):
    char = ctx.char_atual()

    # Adicionamos a permissão explícita para o underscore
    if char.isalpha() or char == "_":
        ctx.buffer += char
        ctx.avancar()
        return estadoPalavra

    elif char.isspace() or char in "()":
        if ctx.buffer == "RES":
            ctx.adicionar_token(TokenType.COMANDO, ctx.buffer)
        elif ctx.buffer.isupper():
            ctx.adicionar_token(TokenType.MEMORIA, ctx.buffer)
        else:
            return estadoErro
        return estadoInicial

    else:
        ctx.buffer += char
        ctx.avancar()
        return estadoErro


def estadoErro(ctx):
    char = ctx.char_atual()

    if char != "" and not char.isspace() and char not in "()":
        ctx.buffer += char
        ctx.avancar()
        return estadoErro

    ctx.adicionar_token(TokenType.ERRO, ctx.buffer)
    return estadoInicial