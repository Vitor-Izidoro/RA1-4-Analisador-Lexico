from tokens import TokenType

def estadoInicial(ctx):
    char = ctx.char_atual()

    if char == "":
        return None

    if char.isspace():
        ctx.avancar()
        return estadoInicial

    if char in "()":
        return estadoParenteses

    if char in "+-*%^":
        return estadoOperador

    if char == "/":
        ctx.buffer += char
        ctx.avancar()
        return estadoDivisao

    if char.isdigit():
        ctx.buffer += char
        ctx.avancar()
        return estadoNumero

    if char == ".":
        ctx.buffer += char
        ctx.avancar()
        return estadoDecimal

    if char.isalpha():
        ctx.buffer += char
        ctx.avancar()
        return estadoPalavra

    # qualquer outro símbolo inválido
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

    if char.isalpha():
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