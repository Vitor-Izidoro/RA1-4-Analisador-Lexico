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

import sys
from pathlib import Path
from typing import Optional, List, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Suporta o nome com e sem espaço pq eu n consegui mudar o nome da pasta no github
MAQUINA_DIR = next(
    (p for p in [PROJECT_ROOT / "Maquina de Estado", PROJECT_ROOT / "MaquinaDeEstado"] if p.exists()),
    None,
)
if MAQUINA_DIR is None:
    raise RuntimeError("Pasta do Lexer nao encontrada (esperado: 'Maquina de Estado' ou 'MaquinaDeEstado')")

sys.path.insert(0, str(MAQUINA_DIR))

from tokens import Token, TokenType  # noqa: E402
from lexer import parseExpressao  # noqa: E402


def lerArquivo(nomeArquivo: str, linhas: list) -> None:
    #Lê o arquivo de expressões e popula `linhas` ignorando linhas vazias.
    informado = Path(nomeArquivo)

    # Tenta o caminho em múltiplas posições relativas ao projeto
    candidatos: List[Path] = [informado, SCRIPT_DIR / informado, PROJECT_ROOT / informado]
    if informado.parent == Path("."):
        candidatos.append(SCRIPT_DIR / "arquivosTeste" / informado.name)

    path = next((p for p in candidatos if p.exists()), None)
    if path is None:
        print(f"Erro: arquivo '{nomeArquivo}' nao encontrado.")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            if linha.strip():
                linhas.append(linha.strip())


def gerarAssembly(tokens_por_linha, nomeArquivoSaida: str = "saida.s") -> str:
    #Traduz uma lista de linhas tokenizadas para Assembly

    # Operações validas:
    #    +  -  *  /    binop f64
    #    //             divisão inteira truncada (s32)
    #    %              resto: a - b * trunc(a/b)
    #    ^              potência com expoente inteiro positivo
    #    VARNAME        load (se precede operador) ou store (se há valor na pilha)
    #    VARNAME MEM    store explícito
    #    N RES          recupera o resultado da linha N posições atrás
    

    if not tokens_por_linha:
        return ""

    linhas_tokens: List[List[Token]] = (
        tokens_por_linha if isinstance(tokens_por_linha[0], list) else [tokens_por_linha]
    )

    data_lines: List[str] = [
        ".global _start",
        ".section .data",
        ".balign 8",
        "last_result: .double 0.0",
    ]

    text_lines: List[str] = [
        ".section .text",
        ".global _start",
        "_start:",
        "    mov r7, sp",
    ]

    contador_const: int = 0
    contador_rotulo: int = 0
    stack_depth: int = 0
    vars_memoria: Dict[str, str] = {}
    const_cache: Dict[str, str] = {}

    # --- helpers de .data -------------------------------------------------

    def get_unique_label(prefix: str) -> str:
        nonlocal contador_rotulo
        label = f"{prefix}_{contador_rotulo}"
        contador_rotulo += 1
        return label

    def ensure_const_double(valor_str: str) -> str:
        #Cria a constante f64 no .data na primeira vez; reutiliza nas demais.
        nonlocal contador_const
        if valor_str not in const_cache:
            nome = f"const_{contador_const}"
            const_cache[valor_str] = nome
            data_lines.extend([".balign 8", f"{nome}: .double {valor_str}"])
            contador_const += 1
        return const_cache[valor_str]

    def ensure_var_memoria(nome: str) -> str:
        #Reserva espaço f64 no .data para a variável, se ainda não existe.
        if nome not in vars_memoria:
            label = f"var_{nome}"
            vars_memoria[nome] = label
            data_lines.extend([".balign 8", f"{label}: .double 0.0"])
        return vars_memoria[nome]

    # --- emissores de instruções .text -----------------------------------

    def emit_push_const_double(valor_str: str) -> None:
        nome = ensure_const_double(valor_str)
        text_lines.extend(
            [
                f"    ldr r0, ={nome}",
                "    vldr.f64 d0, [r0]",
                "    vpush.f64 {d0}",
            ]
        )

    def emit_binop(op: str) -> None:
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError(f"Operador '{op}' sem operandos suficientes")
        inst = {"+": "vadd.f64", "-": "vsub.f64", "*": "vmul.f64", "/": "vdiv.f64"}[op]
        text_lines.extend(
            [
                "    vpop.f64 {d1}",
                "    vpop.f64 {d0}",
                f"    {inst} d2, d0, d1",
                "    vpush.f64 {d2}",
            ]
        )
        stack_depth -= 1

    def emit_idiv_trunc() -> None:
        #Divisão inteira: truncamento em direção a zero.
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError("Operador '//' sem operandos suficientes")
        text_lines.extend(
            [
                "    vpop.f64 {d1}",
                "    vpop.f64 {d0}",
                "    vdiv.f64 d2, d0, d1",
                "    vcvtr.s32.f64 s4, d2",
                "    vcvt.f64.s32 d2, s4",
                "    vpush.f64 {d2}",
            ]
        )
        stack_depth -= 1

    def emit_mod() -> None:
        #Resto: a % b = a - b * trunc(a/b).
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError("Operador '%' sem operandos suficientes")
        text_lines.extend(
            [
                "    vpop.f64 {d1}",
                "    vpop.f64 {d0}",
                "    vdiv.f64 d2, d0, d1",
                "    vcvtr.s32.f64 s4, d2",
                "    vcvt.f64.s32 d2, s4",
                "    vmul.f64 d2, d2, d1",
                "    vsub.f64 d2, d0, d2",
                "    vpush.f64 {d2}",
            ]
        )
        stack_depth -= 1

    def emit_pow_int() -> None:
        #Potenciação por loop: multiplica a base exp vezes; base^0 = 1.0.
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError("Operador '^' sem operandos suficientes")
        loop_lbl = get_unique_label("pow_loop")
        done_lbl = get_unique_label("pow_done")
        one_lbl = ensure_const_double("1.0")
        text_lines.extend(
            [
                "    vpop.f64 {d1}",
                "    vpop.f64 {d0}",
                "    vcvtr.s32.f64 s4, d1",
                "    vmov r1, s4",
                f"    ldr r0, ={one_lbl}",
                "    vldr.f64 d2, [r0]",
                "    cmp r1, #0",
                f"    beq {done_lbl}",
                f"{loop_lbl}:",
                "    vmul.f64 d2, d2, d0",
                "    subs r1, r1, #1",
                f"    bne {loop_lbl}",
                f"{done_lbl}:",
                "    vpush.f64 {d2}",
            ]
        )
        stack_depth -= 1

    def emit_load_var(nome: str) -> None:
        nonlocal stack_depth
        label = ensure_var_memoria(nome)
        text_lines.extend(
            [
                f"    ldr r0, ={label}",
                "    vldr.f64 d0, [r0]",
                "    vpush.f64 {d0}",
            ]
        )
        stack_depth += 1

    def emit_store_var(nome: str) -> None:
        #Store não-destrutivo: pop -> salva -> push, mantendo o valor na pilha.
        nonlocal stack_depth
        if stack_depth < 1:
            raise ValueError(f"Store em '{nome}' sem valor na pilha")
        label = ensure_var_memoria(nome)
        text_lines.extend(
            [
                "    vpop.f64 {d0}",
                f"    ldr r0, ={label}",
                "    vstr.f64 d0, [r0]",
                "    vpush.f64 {d0}",
            ]
        )

    def emit_load_result(idx: int, linha_atual: int) -> None:
        #Carrega results[idx] na pilha para o comando RES.
        nonlocal stack_depth
        if idx < 0:
            raise ValueError(
                f"Linha {linha_atual + 1}: RES aponta para índice inexistente ({idx})"
            )
        text_lines.append("    ldr r0, =results")
        if idx > 0:
            text_lines.append(f"    add r0, r0, #{idx * 8}")
        text_lines.extend(["    vldr.f64 d0, [r0]", "    vpush.f64 {d0}"])
        stack_depth += 1

    def peek_next_significant(tokens: List[Token], start: int) -> Optional[Token]:
        #Primeiro token apos `start` que não seja parêntese ou EOF.
        return next(
            (
                tokens[j]
                for j in range(start, len(tokens))
                if tokens[j].tipo not in (TokenType.PARENTESES, TokenType.EOF)
            ),
            None,
        )

    # Reserva uma entrada por linha no array de resultados
    data_lines.extend([".balign 8", "results:"])
    data_lines.extend(["    .double 0.0"] * len(linhas_tokens))

    # --- loop principal --------------------------------------------------

    for linha_idx, tokens in enumerate(linhas_tokens):
        stack_depth = 0
        last_literal: Optional[str] = None
        pending_mem_var: Optional[str] = None

        text_lines.extend(["", f"    @ linha {linha_idx + 1}"])

        i = 0
        while i < len(tokens):
            t = tokens[i]

            if t.tipo == TokenType.ERRO:
                raise ValueError(f"Erro léxico: '{t.valor}' (linha {linha_idx + 1})")

            if t.tipo in (TokenType.PARENTESES, TokenType.EOF):
                i += 1
                continue

            if t.tipo == TokenType.NUMERO_REAL:
                emit_push_const_double(t.valor)
                stack_depth += 1
                last_literal = t.valor
                i += 1
                continue

            if t.tipo == TokenType.OPERADOR:
                op = t.valor
                if op in ("+", "-", "*", "/"):
                    emit_binop(op)
                elif op == "//":
                    emit_idiv_trunc()
                elif op == "%":
                    emit_mod()
                elif op == "^":
                    emit_pow_int()
                else:
                    raise ValueError(
                        f"Operador desconhecido: '{op}' (linha {linha_idx + 1})"
                    )
                last_literal = None
                i += 1
                continue

            if t.tipo == TokenType.MEMORIA:
                if t.valor == "MEM":
                    if pending_mem_var is None:
                        raise ValueError(
                            f"Linha {linha_idx + 1}: MEM sem variável precedente"
                        )
                    emit_store_var(pending_mem_var)
                    pending_mem_var = None
                    last_literal = None
                    i += 1
                    continue

                proximo = peek_next_significant(tokens, i + 1)

                if (
                    proximo is not None
                    and proximo.tipo == TokenType.MEMORIA
                    and proximo.valor == "MEM"
                ):
                    pending_mem_var = t.valor
                    i += 1
                    continue

                # Heurística load/store sem MEM explícito:
                # - operador a seguir -> operando (load)
                # - há valor na pilha -> destino (store)
                if proximo is not None and proximo.tipo == TokenType.OPERADOR:
                    emit_load_var(t.valor)
                elif stack_depth > 0:
                    emit_store_var(t.valor)
                else:
                    emit_load_var(t.valor)

                last_literal = None
                i += 1
                continue

            if t.tipo == TokenType.COMANDO and t.valor == "RES":
                if last_literal is None:
                    raise ValueError(
                        f"Linha {linha_idx + 1}: RES sem número precedente"
                    )
                n = int(float(last_literal))
                text_lines.append("    vpop.f64 {d0}")
                stack_depth -= 1
                last_literal = None
                emit_load_result(linha_idx - n, linha_idx)
                i += 1
                continue

            raise ValueError(f"Token inesperado: {t} (linha {linha_idx + 1})")

        if stack_depth != 1:
            raise ValueError(
                f"Linha {linha_idx + 1}: pilha com {stack_depth} valor ao final (esperado 1)"
            )

        # Salva o resultado em last_result e em results[linha_idx]
        offset = linha_idx * 8
        text_lines.extend(
            [
                "    vpop.f64 {d0}",
                "    ldr r1, =last_result",
                "    vstr.f64 d0, [r1]",
                "    ldr r1, =results",
            ]
        )
        if offset > 0:
            text_lines.append(f"    add r1, r1, #{offset}")
        text_lines.extend(["    vstr.f64 d0, [r1]", "    mov sp, r7"])

    text_lines.extend(["", "    bkpt"])

    codigo_completo = "\n".join(data_lines + [""] + text_lines) + "\n"

    if nomeArquivoSaida:
        try:
            with open(nomeArquivoSaida, "w", encoding="utf-8") as f:
                f.write(codigo_completo)
        except IOError:
            print("Erro ao salvar o arquivo assembly.")

    return codigo_completo



# --- 26.7.3 ---------------------------------------------------

def testarLerArquivo() -> None:
    #Lê teste1.txt da pasta arquivosTeste e imprime as linhas encontradas.
    print("=" * 60)
    print("TESTE: testarLerArquivo()")
    print("=" * 60)

    arquivo_teste = next(
        (p for p in [SCRIPT_DIR / "arquivosTeste" / "teste1.txt", SCRIPT_DIR / "teste1.txt"] if p.exists()),
        None,
    )
    if arquivo_teste is None:
        print("[AVISO] 'arquivosTeste/teste1.txt' nao encontrado")
        print()
        return

    linhas: list = []
    lerArquivo(str(arquivo_teste), linhas)
    print(f"Arquivo : {arquivo_teste}")
    print(f"Linhas  : {len(linhas)}")
    for idx, linha in enumerate(linhas, 1):
        print(f"  [{idx:02d}] {linha}")
        print()


def testarGerarAssembly() -> None:
    #Gera Assembly para as expressões do professor usando o lexer do crys
    print("=" * 60)
    print("TESTE: testarGerarAssembly()")
    print("=" * 60)

    expressoes = [
        "(3.14 2.0 +)",
        "((1.5 2.0 *) (3.0 4.0 *) /)",
        "(5.0 TOTAL MEM)",
        "(2 RES)",
    ]

    print("Expressões de entrada:")
    for idx, expr in enumerate(expressoes, 1):
        print(f"  Linha {idx}: {expr}")
    print()

    tokens_por_linha = [parseExpressao(expr) for expr in expressoes]

    try:
        assembly = gerarAssembly(tokens_por_linha, nomeArquivoSaida=None)
        print("Assembly gerado:")
        print("-" * 60)
        print(assembly)
        print("-" * 60)
    except Exception as e:
        print(f"[ERRO] {e}")
        print()



# --- Ponto de entrada --------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nenhum arquivo informado. Executando testes internos...\n")
        testarLerArquivo()
        testarGerarAssembly()
        sys.exit(0)

    linhas: list = []
    lerArquivo(sys.argv[1], linhas)
    tokens_por_linha = [parseExpressao(linha) for linha in linhas]
    print(gerarAssembly(tokens_por_linha))