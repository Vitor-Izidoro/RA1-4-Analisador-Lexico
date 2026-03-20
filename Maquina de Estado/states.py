from tokens import TokenType

def estadoInicial(ctx):
    char = ctx.char_atual()

    if char == "" or char is None:
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

    if char.isalpha():
        ctx.buffer += char
        ctx.avancar()
        return estadoPalavra

    ctx.buffer += char
    ctx.avancar()
    return estadoErro

def estadoParenteses(ctx):
    char = ctx.char_atual()

    ctx.adicionar_token(TokenType.PARENTESES, char)
    ctx.avancar()
    return estadoInicial

def estadoOperador(ctx):
    char = ctx.char_atual()

    if char in "+-*%^/":
        ctx.adicionar_token(TokenType.OPERADOR, char)
        ctx.avancar()
        return estadoInicial
    else:
        ctx.buffer += char
        ctx.avancar()
        return estadoErro

def estadoNumero(ctx):
    char = ctx.char_atual()

    if char.isdigit():
        ctx.buffer += char
        ctx.avancar()
        return estadoNumero
    elif char == ".":
        ctx.buffer += char
        ctx.avancar()
        return estadoDecimal
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
    elif char.isspace() or char in "()":
        ctx.adicionar_token(TokenType.NUMERO_REAL, ctx.buffer)
        return estadoInicial
    else:
        ctx.buffer += char
        ctx.avancar()
        return estadoErro

def estadoDivisao(ctx):
    char = ctx.char_atual()

    if char == "/": # Divisão inteira
        ctx.buffer += char
        ctx.adicionar_token(TokenType.OPERADOR, ctx.buffer)
        ctx.avancar()
        return estadoInicial
    else: # Divisão real
        ctx.adicionar_token(TokenType.OPERADOR, ctx.buffer)
        return estadoInicial

def estadoPalavra(ctx):
    char = ctx.char_atual()

    if char.isalpha():
        ctx.buffer += char
        ctx.avancar()
        return estadoPalavra
    elif char.isspace() or char in "()":
        # Verifica se é a keyword RES ou apenas uma variável de Memória
        if ctx.buffer == "RES":
            ctx.adicionar_token(TokenType.COMANDO, ctx.buffer)
        elif ctx.buffer.isupper():
            ctx.adicionar_token(TokenType.MEMORIA, ctx.buffer)
        else:
            # Se for minúsculo ou misto, tratamos como erro
            return estadoErro
        return estadoInicial
    else:
        ctx.buffer += char
        ctx.avancar()
        return estadoErro

def estadoErro(ctx):
    # Consome os caracteres até encontrar um espaço ou parêntese para isolar o erro
    char = ctx.char_atual()
    
    if not char.isspace() and char not in "()" and char != "":
        ctx.buffer += char
        ctx.avancar()
        return estadoErro
    else:
        ctx.adicionar_token(TokenType.ERRO, ctx.buffer)
        return estadoInicial