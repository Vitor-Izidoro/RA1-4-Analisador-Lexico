# Crystofer samuel demetino, Gabriel marques simini, Vitor izidoro
# interpretadores B noite frank coelho de alcatara

import sys
from pathlib import Path
from typing import Optional, List, Dict


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

MAQUINA_DIR_CANDIDATOS = [
    PROJECT_ROOT / "MaquinaDeEstado",
]
MAQUINA_DIR = next((p for p in MAQUINA_DIR_CANDIDATOS if p.exists()), None)
if MAQUINA_DIR is None:
    raise RuntimeError(
        "Nao foi possivel localizar a pasta do Lexer"
    )

sys.path.insert(0, str(MAQUINA_DIR))

from tokens import Token, TokenType
from lexer import parseExpressao

#n foi na mão ent botei essa lib
def lerArquivo(nomeArquivo, linhas):
    informado = Path(nomeArquivo)

    candidatos = []
    if informado.is_absolute():
        candidatos.append(informado)
    else:
        # 1) relativo ao cwd
        candidatos.append(informado)
        # 2) relativo à pasta do script
        candidatos.append(SCRIPT_DIR / informado)
        # 3) relativo à raiz do projeto
        candidatos.append(PROJECT_ROOT / informado)
        # 4) se for só o nome do arquivo, tenta dentro de assembly/arquivosTeste/
        if informado.parent == Path("."):
            candidatos.append(SCRIPT_DIR / "arquivosTeste" / informado.name)
            candidatos.append(PROJECT_ROOT / "assembly" / "arquivosTeste" / informado.name)

    path = next((p for p in candidatos if p.exists()), None)
    if path is None:
        print(f"Erro: Nao foi possivel abrir o arquivo '{nomeArquivo}'.")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as arquivo:
            for linha in arquivo:
                if linha.strip():
                    linhas.append(linha.strip())
    except FileNotFoundError:
        print(f"Erro: Nao foi possivel abrir o arquivo '{nomeArquivo}'.")
        sys.exit(1)


def gerarAssembly(tokens_por_linha, nomeArquivoSaida="saida.s"):

    if not tokens_por_linha:
        return ""

    # Aceita tanto lista de tokens (uma expressão) quanto lista de listas (várias linhas do arquivo).
    if tokens_por_linha and isinstance(tokens_por_linha[0], list):
        linhas_tokens = tokens_por_linha
    else:
        linhas_tokens = [tokens_por_linha]

    data_lines = [
        ".global _start",
        ".section .data",
        ".balign 8",
        "last_result: .double 0.0",
    ]

    text_lines = [
        ".section .text",
        ".global _start",
        "_start:",
        # Guardamos o valor inicial de SP para limpar a pilha entre linhas.
        "mov r7, sp",
    ]

    contador_const = 0

    # Variáveis de memória (TokenType.MEMORIA) viram labels na .data, criadas sob demanda.
    vars_memoria: Dict[str, str] = {}

    # Constantes em .data também são criadas sob demanda.
    const_cache: Dict[str, str] = {}

    contador_rotulo = 0

    def get_unique_label(prefix: str) -> str:
        nonlocal contador_rotulo
        label = f"{prefix}_{contador_rotulo}"
        contador_rotulo += 1
        return label

    def ensure_var_memoria(nome: str) -> str:
        # Lexer garante somente letras e uppercase para TokenType.MEMORIA.
        if nome not in vars_memoria:
            label = f"var_{nome}"
            vars_memoria[nome] = label
            data_lines.append(f"{label}: .double 0.0")
        return vars_memoria[nome]

    def ensure_const_double(valor_str: str) -> str:
        nonlocal contador_const
        if valor_str in const_cache:
            return const_cache[valor_str]
        nome_const = f"const_{contador_const}"
        const_cache[valor_str] = nome_const
        data_lines.append(f"{nome_const}: .double {valor_str}")
        contador_const += 1
        return nome_const

    def emit_push_const_double(valor_str: str) -> None:
        nome_const = ensure_const_double(valor_str)
        text_lines.extend(
            [
                f"ldr r0, ={nome_const}",
                "vldr.f64 d0, [r0]",
                "vpush.f64 {d0}",
            ]
        )

    # Rastreamento simples
    # da profundidade da pilha de valores.
    # Ajuda a acusar erros do arquivo de entrada já na geração.
    stack_depth = 0

    def peek_next_significant(tokens: List[Token], start_idx: int) -> Optional[Token]:
        for j in range(start_idx, len(tokens)):
            if tokens[j].tipo in (TokenType.PARENTESES, TokenType.EOF):
                continue
            return tokens[j]
        return None

    def emit_binop(op: str) -> None:
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError(f"Expressao invalida: operador '{op}' sem operandos suficientes")
        text_lines.extend(["vpop.f64 {d1}", "vpop.f64 {d0}"])
        if op == "+":
            text_lines.append("vadd.f64 d2, d0, d1")
        elif op == "-":
            text_lines.append("vsub.f64 d2, d0, d1")
        elif op == "*":
            text_lines.append("vmul.f64 d2, d0, d1")
        elif op == "/":
            text_lines.append("vdiv.f64 d2, d0, d1")
        else:
            raise ValueError(f"Operador inesperado em emit_binop: {op}")
        text_lines.append("vpush.f64 {d2}")
        stack_depth -= 1

    def emit_idiv_trunc() -> None:
        # trunc(a/b) para inteiro e converte de volta pra f64
        # Usamos VCVTR (round to zero) para evitar depender do rounding mode do FPSCR.
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError("Expressao invalida: operador '//' sem operandos suficientes")
        text_lines.extend(
            [
                "vpop.f64 {d1}",
                "vpop.f64 {d0}",
                "vdiv.f64 d2, d0, d1",
                "vcvtr.s32.f64 s4, d2",
                "vcvt.f64.s32 d2, s4",
                "vpush.f64 {d2}",
            ]
        )
        stack_depth -= 1

    def emit_mod() -> None:
        # a % b = a - (b * trunc(a/b))
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError("Expressao invalida: operador '%' sem operandos suficientes")
        text_lines.extend(
            [
                "vpop.f64 {d1}",  # b
                "vpop.f64 {d0}",  # a
                "vdiv.f64 d2, d0, d1",  # a/b
                "vcvtr.s32.f64 s4, d2",  # q = trunc(a/b)
                "vcvt.f64.s32 d2, s4",  # q como double
                "vmul.f64 d2, d2, d1",  # q*b
                "vsub.f64 d2, d0, d2",  # a - q*b
                "vpush.f64 {d2}",
            ]
        )
        stack_depth -= 1

    def emit_pow_int() -> None:
        # Expoente sempre inteiro positivo (ou zero).
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError("Expressao invalida: operador '^' sem operandos suficientes")

        loop_label = get_unique_label("pow_loop")
        done_label = get_unique_label("pow_done")
        one_label = ensure_const_double("1.0")

        text_lines.extend(
            [
                "vpop.f64 {d1}",  # exp
                "vpop.f64 {d0}",  # base
                "vcvtr.s32.f64 s4, d1",
                "vmov r1, s4",  # r1 = exp
                f"ldr r0, ={one_label}",
                "vldr.f64 d2, [r0]",  # result = 1.0
                "cmp r1, #0",
                f"beq {done_label}",
                f"{loop_label}:",
                "vmul.f64 d2, d2, d0",
                "subs r1, r1, #1",
                f"bne {loop_label}",
                f"{done_label}:",
                "vpush.f64 {d2}",
            ]
        )
        stack_depth -= 1

    def emit_load_var(nome: str) -> None:
        nonlocal stack_depth
        label = ensure_var_memoria(nome)
        text_lines.extend(
            [
                f"ldr r0, ={label}",
                "vldr.f64 d0, [r0]",
                "vpush.f64 {d0}",
            ]
        )
        stack_depth += 1

    def emit_store_var(nome: str) -> None:
        # Armazena o topo da pilha em var_<nome>.
        # Para facilitar composição em RPN, devolve o mesmo valor pro topo.
        nonlocal stack_depth
        if stack_depth < 1:
            raise ValueError(f"Expressao invalida: tentativa de gravar em '{nome}' sem valor na pilha")
        label = ensure_var_memoria(nome)
        text_lines.extend(
            [
                "vpop.f64 {d0}",
                f"ldr r0, ={label}",
                "vstr.f64 d0, [r0]",
                "vpush.f64 {d0}",
            ]
        )
        # depth não muda (pop + push)

    # Array com resultados por linha (base pro RES do Dia 3).
    results_count = len(linhas_tokens)
    if results_count > 0:
        data_lines.append(".balign 8")
        data_lines.append("results:")
        for _ in range(results_count):
            data_lines.append("  .double 0.0")

    for linha_idx, tokens in enumerate(linhas_tokens):
        stack_depth = 0

        for i, t in enumerate(tokens):
            if t.tipo == TokenType.ERRO:
                raise ValueError(f"Erro Lexico no token: {t.valor}")

            if t.tipo in (TokenType.PARENTESES, TokenType.EOF):
                continue

            if t.tipo == TokenType.NUMERO_REAL:
                emit_push_const_double(t.valor)
                stack_depth += 1
                continue

            if t.tipo == TokenType.OPERADOR:
                if t.valor in ("+", "-", "*", "/"):
                    emit_binop(t.valor)
                elif t.valor == "//":
                    emit_idiv_trunc()
                elif t.valor == "%":
                    emit_mod()
                elif t.valor == "^":
                    emit_pow_int()
                else:
                    raise ValueError(f"ignorar: {t.valor}")
                continue

            if t.tipo == TokenType.MEMORIA:
                # Heurística para diferenciar LOAD vs STORE:
                #   Se o próximo token significativo é operador => aqui é LOAD (ex: (X 2 +))
                #   Se o próximo token significativo é None/fecha-parênteses => STORE if já existe valor na pilha; else LOAD
                proximo = peek_next_significant(tokens, i + 1)
                if proximo is not None and proximo.tipo == TokenType.OPERADOR:
                    emit_load_var(t.valor)
                else:
                    if stack_depth > 0:
                        emit_store_var(t.valor)
                    else:
                        emit_load_var(t.valor)
                continue

            if t.tipo == TokenType.COMANDO:
                # RES 
                raise ValueError(f"n ta funcionando ainda: {t.valor}")

            raise ValueError(f"Token inesperado: {t}")

        # Ao final de cada linha, esperamos 1 valor como resultado.
        if stack_depth != 1:
            raise ValueError(
                f"Expressao invalida na linha {linha_idx + 1}: esperado 1 valor na pilha, obtido {stack_depth}"
            )

        text_lines.extend(
            [
                "vpop.f64 {d0}",
                "ldr r0, =last_result",
                "vstr.f64 d0, [r0]",
            ]
        )

        # results[linha_idx] = last_result
        offset = linha_idx * 8
        if offset == 0:
            text_lines.extend(
                [
                    "ldr r0, =results",
                    "vstr.f64 d0, [r0]",
                ]
            )
        else:
            text_lines.extend(
                [
                    "ldr r0, =results",
                    f"add r0, r0, #{offset}",
                    "vstr.f64 d0, [r0]",
                ]
            )

        # Limpa a pilha para a próxima linha.
        text_lines.append("mov sp, r7")

    text_lines.append("bkpt")

    codigo_completo = "\n".join(data_lines + [""] + text_lines) + "\n"

    if nomeArquivoSaida:
        try:
            with open(nomeArquivoSaida, "w", encoding="utf-8") as f:
                f.write(codigo_completo)
        except IOError:
            print("Erro ao salvar o arquivo assembly.")

    return codigo_completo


if __name__ == "__main__":
    # Garante que o arquivo seja passado por linha de comando
    if len(sys.argv) < 2:
        print("Uso correto: python gerarAssembly.py nome_do_arquivo.txt")
        sys.exit(1)

    nome_arquivo = sys.argv[1]
    linhas = []

    # 1. Lê o arquivo
    lerArquivo(nome_arquivo, linhas)

    tokens_por_linha = []

    # 2. Chama o Lexer cryyyysss para parsear as linhas reais do arquivo
    for linha in linhas:
        tokens_da_linha = parseExpressao(linha)
        tokens_por_linha.append(tokens_da_linha)

    # 3. Gera e exibe o Assembly
    assembly_final = gerarAssembly(tokens_por_linha)
    print(assembly_final)