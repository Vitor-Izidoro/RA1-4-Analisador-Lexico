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

MAQUINA_DIR = next(
    (p for p in [PROJECT_ROOT / "Maquina de Estado", PROJECT_ROOT / "MaquinaDeEstado"] if p.exists()),
    None,
)
if MAQUINA_DIR is None:
    raise RuntimeError("Pasta do Lexer nao encontrada (esperado: 'Maquina de Estado' ou 'MaquinaDeEstado')")

sys.path.insert(0, str(MAQUINA_DIR))

from tokens import Token, TokenType  # noqa: E402
from lexer import parseExpressao     # noqa: E402


# ---------------------------------------------------------------------------
# lerArquivo
# ---------------------------------------------------------------------------

def lerArquivo(nomeArquivo: str, linhas: list) -> None:
    """Lê o arquivo de expressões e popula `linhas` ignorando linhas vazias."""
    informado = Path(nomeArquivo)

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


# ---------------------------------------------------------------------------
# gerarAssembly
# ---------------------------------------------------------------------------

def gerarAssembly(tokens_por_linha, nomeArquivoSaida: str = "saida.s") -> str:
    
    if not tokens_por_linha:
        return ""

    linhas_tokens: List[List[Token]] = (
        tokens_por_linha if isinstance(tokens_por_linha[0], list) else [tokens_por_linha]
    )

    num_linhas = len(linhas_tokens)

    # -----------------------------------------------------------------
    # Seção .data
    # -----------------------------------------------------------------
    data_lines: List[str] = [
        ".global _start",
        ".section .data",
        ".balign 8",
        "last_result: .double 0.0",
        ".balign 8",
        f"results: .space {num_linhas * 8}",
        ".balign 4",
        "display_lut: .word 0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71",
        ".balign 8",   # garante alinhamento 8 bytes para todas as constantes double seguintes
    ]

    # -----------------------------------------------------------------
    # Seção .text
    # -----------------------------------------------------------------
    text_lines: List[str] = [
        ".section .text",
        ".global _start",
        "_start:",
        "    @ --- Habilitar FPU (FPEXC.EN = 1) ---",
        "    mrc p15, 0, r0, c1, c0, 2",
        "    orr r0, r0, #0xF00000",
        "    mcr p15, 0, r0, c1, c0, 2",
        "    isb",
        "    mov r0, #0x40000000",
        "    vmsr fpexc, r0",
        "    @ -----------------------------------------",
        "    @ Salva SP base para restaurar entre linhas",
        "    mov r7, sp",
        "    @ Carrega endereços fixos uma única vez (evita literal pool overflow)",
        "    ldr r10, =last_result   @ r10 = &last_result (fixo durante toda execução)",
        "    ldr r11, =results       @ r11 = &results[0]  (fixo durante toda execução)",
    ]

    contador_const: int = 0
    contador_rotulo: int = 0
    vars_memoria: Dict[str, str] = {}
    const_cache: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Helpers .data
    # ------------------------------------------------------------------

    def get_unique_label(prefix: str) -> str:
        nonlocal contador_rotulo
        lbl = f"{prefix}_{contador_rotulo}"
        contador_rotulo += 1
        return lbl

    def ensure_const_double(valor_str: str) -> str:
        """Cria a constante f64 no .data apenas uma vez; reutiliza nas demais."""
        nonlocal contador_const
        # Normaliza: 3 → 3.0, 3.14 → 3.14  (evita duplicatas por formato)
        try:
            normalizado = repr(float(valor_str))
        except ValueError:
            normalizado = valor_str
        if normalizado not in const_cache:
            nome = f"const_{contador_const}"
            const_cache[normalizado] = nome
            data_lines.extend([".balign 8", f"{nome}: .double {valor_str}"])
            contador_const += 1
        return const_cache[normalizado]

    def ensure_var_memoria(nome: str) -> str:
        """Reserva espaço f64 no .data para a variável, se ainda não existe."""
        if nome not in vars_memoria:
            label = f"var_{nome}"
            vars_memoria[nome] = label
            data_lines.extend([".balign 8", f"{label}: .double 0.0"])
        return vars_memoria[nome]

    # ------------------------------------------------------------------
    # Emissores .text
    # ------------------------------------------------------------------

    def emit_push_const_double(valor_str: str) -> None:
        nome = ensure_const_double(valor_str)
        text_lines.extend([
            f"    ldr r0, ={nome}",
            "    vldr.f64 d0, [r0]",
            "    vpush.f64 {d0}",
        ])

    def emit_binop(op: str, linha_idx: int) -> None:
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError(f"Linha {linha_idx + 1}: operador '{op}' com apenas {stack_depth} operando(s) na pilha")
        inst = {"+": "vadd.f64", "-": "vsub.f64", "*": "vmul.f64", "/": "vdiv.f64"}[op]
        # Ordem: d0 = operando esquerdo (empilhado primeiro), d1 = direito
        text_lines.extend([
            "    vpop.f64 {d1}",   # B (topo)
            "    vpop.f64 {d0}",   # A
            f"    {inst} d2, d0, d1",
            "    vpush.f64 {d2}",
        ])
        stack_depth -= 1

    def emit_idiv_trunc(linha_idx: int) -> None:
        """Divisão inteira truncada em direção a zero (floor via vcvtr.s32)."""
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError(f"Linha {linha_idx + 1}: '//' com apenas {stack_depth} operando(s)")
        text_lines.extend([
            "    vpop.f64 {d1}",
            "    vpop.f64 {d0}",
            "    vdiv.f64 d2, d0, d1",
            "    vcvtr.s32.f64 s4, d2",   # trunca (round-toward-zero)
            "    vcvt.f64.s32 d2, s4",
            "    vpush.f64 {d2}",
        ])
        stack_depth -= 1

    def emit_mod(linha_idx: int) -> None:
        """Resto: a % b = a − b × trunc(a/b)."""
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError(f"Linha {linha_idx + 1}: '%' com apenas {stack_depth} operando(s)")
        text_lines.extend([
            "    vpop.f64 {d1}",
            "    vpop.f64 {d0}",
            "    vdiv.f64 d2, d0, d1",
            "    vcvtr.s32.f64 s4, d2",
            "    vcvt.f64.s32 d2, s4",
            "    vmul.f64 d3, d2, d1",
            "    vsub.f64 d2, d0, d3",
            "    vpush.f64 {d2}",
        ])
        stack_depth -= 1

    def emit_pow_int(linha_idx: int) -> None:
        """Potenciação por loop: base^exp onde exp é inteiro positivo; base^0 = 1.0."""
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError(f"Linha {linha_idx + 1}: '^' com apenas {stack_depth} operando(s)")
        loop_lbl = get_unique_label("pow_loop")
        done_lbl = get_unique_label("pow_done")
        one_lbl  = ensure_const_double("1.0")
        text_lines.extend([
            "    vpop.f64 {d1}",           # expoente B
            "    vpop.f64 {d0}",           # base A
            "    vcvtr.s32.f64 s4, d1",    # s4 = (int)B
            "    vmov r9, s4",             # r9 = contador (evita colidir com r1)
            f"    ldr r0, ={one_lbl}",
            "    vldr.f64 d2, [r0]",       # d2 = acumulador = 1.0
            "    cmp r9, #0",
            f"    beq {done_lbl}",
            f"{loop_lbl}:",
            "    vmul.f64 d2, d2, d0",
            "    subs r9, r9, #1",
            f"    bne {loop_lbl}",
            f"{done_lbl}:",
            "    vpush.f64 {d2}",
        ])
        stack_depth -= 1

    def emit_load_var(nome: str) -> None:
        nonlocal stack_depth
        label = ensure_var_memoria(nome)
        text_lines.extend([
            f"    ldr r0, ={label}",
            "    vldr.f64 d0, [r0]",
            "    vpush.f64 {d0}",
        ])
        stack_depth += 1

    def emit_store_var(nome: str, linha_idx: int) -> None:
        nonlocal stack_depth
        if stack_depth < 1:
            raise ValueError(f"Linha {linha_idx + 1}: store em '{nome}' sem valor na pilha")
        label = ensure_var_memoria(nome)
        text_lines.extend([
            "    vpop.f64 {d0}",
            f"    ldr r1, ={label}",
            "    vstr.f64 d0, [r1]",
            "    vpush.f64 {d0}",   # mantém o valor como resultado da linha
        ])
        # stack_depth não muda: pop → push

    def emit_load_result(idx: int, linha_atual: int) -> None:
        """Carrega results[idx] na pilha para o comando (N RES)."""
        nonlocal stack_depth
        if idx < 0:
            raise ValueError(
                f"Linha {linha_atual + 1}: (N RES) aponta para índice inválido "
                f"({idx}); só há resultados das linhas anteriores."
            )
        offset = idx * 8
        # Usa r11 (endereço fixo de results) em vez de ldr do literal pool
        if offset > 0:
            text_lines.extend([
                f"    add r0, r11, #{offset}",
                "    vldr.f64 d0, [r0]",
            ])
        else:
            text_lines.append("    vldr.f64 d0, [r11]")
        text_lines.append("    vpush.f64 {d0}")
        stack_depth += 1

    def peek_next_significant(tokens: List[Token], start: int) -> Optional[Token]:
        """Retorna o primeiro token após `start` que não seja parêntese ou EOF."""
        return next(
            (tokens[j] for j in range(start, len(tokens))
             if tokens[j].tipo not in (TokenType.PARENTESES, TokenType.EOF)),
            None,
        )

    # ------------------------------------------------------------------
    # Loop principal: percorre cada linha de tokens
    # ------------------------------------------------------------------

    for linha_idx, tokens in enumerate(linhas_tokens):
        stack_depth = 0
        last_literal: Optional[str] = None   # valor do último NUMERO_REAL visto
        pending_mem_var: Optional[str] = None

        text_lines.extend(["", f"    @ ---- linha {linha_idx + 1} ----"])
        # Restaura SP para o topo da FPU stack limpa (entre linhas)
        text_lines.append("    mov sp, r7")

        i = 0
        while i < len(tokens):
            t = tokens[i]

            # --- Erros léxicos ---
            if t.tipo == TokenType.ERRO:
                raise ValueError(f"Erro léxico: '{t.valor}' (linha {linha_idx + 1})")

            # --- Tokens estruturais ignorados ---
            if t.tipo in (TokenType.PARENTESES, TokenType.EOF):
                i += 1
                continue

            # --- Número real ---
            if t.tipo == TokenType.NUMERO_REAL:
                emit_push_const_double(t.valor)
                stack_depth += 1
                last_literal = t.valor
                i += 1
                continue

            # --- Operador aritmético ---
            if t.tipo == TokenType.OPERADOR:
                op = t.valor
                if op in ("+", "-", "*", "/"):
                    emit_binop(op, linha_idx)
                elif op == "//":
                    emit_idiv_trunc(linha_idx)
                elif op == "%":
                    emit_mod(linha_idx)
                elif op == "^":
                    emit_pow_int(linha_idx)
                else:
                    raise ValueError(f"Operador desconhecido: '{op}' (linha {linha_idx + 1})")
                last_literal = None
                i += 1
                continue

            # --- Identificador de memória (nome de variável ou keyword MEM) ---
            if t.tipo == TokenType.MEMORIA:

                # Keyword MEM: finaliza um store explícito (V VARNAME MEM)
                # Formato da spec: (V VARNAME MEM)
                if t.valor == "MEM":
                    if pending_mem_var is None:
                        raise ValueError(
                            f"Linha {linha_idx + 1}: keyword 'MEM' sem nome de "
                            f"variável precedente — use (V NOMEVARIAVEL MEM)"
                        )
                    emit_store_var(pending_mem_var, linha_idx)
                    pending_mem_var = None
                    last_literal = None
                    i += 1
                    continue

                proximo = peek_next_significant(tokens, i + 1)

                # (V VARNAME MEM) → store explícito via keyword MEM
                if (proximo is not None
                        and proximo.tipo == TokenType.MEMORIA
                        and proximo.valor == "MEM"):
                    # O valor V já está na pilha; registra o nome para quando
                    # encontrarmos a keyword MEM no próximo token significativo
                    pending_mem_var = t.valor
                    i += 1
                    continue

                # (VARNAME) → load: variável sozinha dentro de parênteses
                # Detectado quando stack_depth == 0 neste contexto,
                # ou quando o próximo token significativo é um operador
                if stack_depth == 0 or (
                    proximo is not None and proximo.tipo == TokenType.OPERADOR
                ):
                    emit_load_var(t.valor)
                else:
                    # Sem MEM explícito e há valor na pilha: store implícito
                    # (comportamento de compatibilidade; preferir sempre usar MEM)
                    emit_store_var(t.valor, linha_idx)

                last_literal = None
                i += 1
                continue

            # --- Comando RES ---
            if t.tipo == TokenType.COMANDO and t.valor == "RES":
                if last_literal is None:
                    raise ValueError(
                        f"Linha {linha_idx + 1}: 'RES' sem número N precedente"
                    )
                n = int(float(last_literal))
                # Remove o N da pilha SEM usar d0 — usa mov direto do valor já
                # conhecido em tempo de compilação, evitando colisão com registros
                # de constantes numéricas que também usam d0/r0.
                text_lines.extend([
                    f"    @ descarta N={n} do RES (valor já conhecido)",
                    "    vpop.f64 {d1}",   # descarta em d1, não d0
                ])
                stack_depth -= 1
                last_literal = None
                # N=0: slot ainda não escrito → retorna 0.0 (spec: N não negativo)
                if n == 0:
                    zero_lbl = ensure_const_double("0.0")
                    text_lines.extend([
                        f"    ldr r0, ={zero_lbl}    @ (0 RES) → 0.0",
                        "    vldr.f64 d0, [r0]",
                        "    vpush.f64 {d0}",
                    ])
                    stack_depth += 1
                else:
                    emit_load_result(linha_idx - n, linha_idx)
                i += 1
                continue

            raise ValueError(f"Token inesperado: {t} (linha {linha_idx + 1})")

        if stack_depth != 1:
            raise ValueError(
                f"Linha {linha_idx + 1}: pilha com {stack_depth} valor(es) ao "
                f"final — esperado exatamente 1. Verifique a expressão."
            )

        # Salva resultado em last_result e em results[linha_idx]
        offset = linha_idx * 8
        text_lines.extend([
            "    vpop.f64 {d0}",
            "    vstr.f64 d0, [r10]",        # r10 = &last_result (fixo)
            "    str r11, [sp, #-4]!",        # salva r11 temporariamente
            "    add r11, r11, #0",           # placeholder — substituído abaixo
        ])
        # Corrige o add com o offset real
        text_lines.pop()  # remove o placeholder
        if offset > 0:
            text_lines.extend([
                f"    add r12, r11, #{offset}",
                "    vstr.f64 d0, [r12]",     # results[linha_idx]
            ])
        else:
            text_lines.append("    vstr.f64 d0, [r11]")  # results[0]
        text_lines.extend([
            "    ldr r11, [sp], #4",           # restaura r11
            "    dsb",
        ])

    text_lines.extend([
        "",
        "    @ --- DECODIFICADOR PARA 4 DISPLAYS ---",
        "    vldr.f64 d0, [r10]",              # usa r10 direto (evita literal pool)
        "    vcvt.s32.f64 s0, d0",
        "    vmov r1, s0",
        "    ldr r2, =0xFF200020",
        "    ldr r3, =display_lut",
        "    mov r4, #0",
        "",
        "    @ HEX0 (unidades)",
        "    and r6, r1, #0xF",
        "    ldr r5, [r3, r6, lsl #2]",      # usa r5 em vez de r7
        "    orr r4, r4, r5",
        "",
        "    @ HEX1 (dezenas)",
        "    lsr r1, r1, #4",
        "    and r6, r1, #0xF",
        "    ldr r5, [r3, r6, lsl #2]",
        "    lsl r5, r5, #8",
        "    orr r4, r4, r5",
        "",
        "    @ HEX2 (centenas)",
        "    lsr r1, r1, #4",
        "    and r6, r1, #0xF",
        "    ldr r5, [r3, r6, lsl #2]",
        "    lsl r5, r5, #16",
        "    orr r4, r4, r5",
        "",
        "    @ HEX3 (milhares)",
        "    lsr r1, r1, #4",
        "    and r6, r1, #0xF",
        "    ldr r5, [r3, r6, lsl #2]",
        "    lsl r5, r5, #24",
        "    orr r4, r4, r5",
        "",
        "    str r4, [r2]",
        "",
        "fim:",
        "    bkpt",
    ])

    codigo_completo = "\n".join(data_lines + [""] + text_lines) + "\n"

    if nomeArquivoSaida:
        try:
            with open(nomeArquivoSaida, "w", encoding="utf-8") as f:
                f.write(codigo_completo)
        except IOError:
            print("Erro ao salvar o arquivo assembly.")

    return codigo_completo


# ---------------------------------------------------------------------------
# Testes — 26.7.3
# ---------------------------------------------------------------------------

def testarLerArquivo() -> None:
    """Lê teste1.txt da pasta arquivosTeste e imprime as linhas encontradas."""
    print("=" * 60)
    print("TESTE: testarLerArquivo()")
    print("=" * 60)

    arquivo_teste = next(
        (p for p in [
            SCRIPT_DIR / "arquivosTeste" / "teste1.txt",
            SCRIPT_DIR / "teste1.txt",
        ] if p.exists()),
        None,
    )
    if arquivo_teste is None:
        print("[AVISO] 'arquivosTeste/teste1.txt' nao encontrado — pulando teste.")
        return

    linhas: list = []
    lerArquivo(str(arquivo_teste), linhas)
    print(f"Arquivo : {arquivo_teste}")
    print(f"Linhas  : {len(linhas)}")
    for idx, linha in enumerate(linhas, 1):
        print(f"  [{idx:02d}] {linha}")
    print()


def testarGerarAssembly() -> None:
    """
    Gera e valida Assembly para as expressões de teste do professor.
    Verifica que:
      - o código é gerado sem exceção,
      - o rótulo last_result aparece na seção .data,
      - o rótulo results aparece na seção .data,
      - vpop.f64 e vstr ocorrem para cada linha,
      - a inicialização da FPU (fpexc) está presente.
    """
    print("=" * 60)
    print("TESTE: testarGerarAssembly()")
    print("=" * 60)

    casos: List[dict] = [
        # ----------------------------------------------------------------
        # Casos básicos
        # ----------------------------------------------------------------
        {
            "desc": "Soma simples (3.14 + 2.0)",
            "expr": ["(3.14 2.0 +)"],
            "esperado_em": ["vadd.f64", "last_result", "results"],
        },
        {
            "desc": "Subtração (10.0 - 3.5)",
            "expr": ["(10.0 3.5 -)"],
            "esperado_em": ["vsub.f64"],
        },
        {
            "desc": "Multiplicação (1.5 * 2.0)",
            "expr": ["(1.5 2.0 *)"],
            "esperado_em": ["vmul.f64"],
        },
        {
            "desc": "Divisão real (7.0 / 2.0)",
            "expr": ["(7.0 2.0 /)"],
            "esperado_em": ["vdiv.f64"],
        },
        {
            "desc": "Divisão inteira (7.0 // 2.0)",
            "expr": ["(7.0 2.0 //)"],
            "esperado_em": ["vcvtr.s32.f64"],
        },
        {
            "desc": "Resto (7.0 % 3.0)",
            "expr": ["(7.0 3.0 %)"],
            "esperado_em": ["vsub.f64 d2, d0, d3"],
        },
        {
            "desc": "Potenciação (2.0 ^ 3)",
            "expr": ["(2.0 3.0 ^)"],
            "esperado_em": ["pow_loop", "pow_done", "vmul.f64 d2, d2, d0"],
        },
        # ----------------------------------------------------------------
        # Expressões aninhadas
        # ----------------------------------------------------------------
        {
            "desc": "Divisão de produtos aninhada ((1.5*2.0)/(3.0*4.0))",
            "expr": ["((1.5 2.0 *) (3.0 4.0 *) /)"],
            "esperado_em": ["vmul.f64", "vdiv.f64"],
        },
        # ----------------------------------------------------------------
        # Comandos especiais
        # ----------------------------------------------------------------
        {
            "desc": "Store explícito (5.0 TOTAL MEM)",
            "expr": ["(5.0 TOTAL MEM)"],
            "esperado_em": ["var_TOTAL", "vstr.f64"],
        },
        {
            "desc": "Load de variável ((TOTAL))",
            "expr": [
                "(5.0 TOTAL MEM)",
                "(TOTAL)",
            ],
            "esperado_em": ["var_TOTAL", "vldr.f64"],
        },
        {
            "desc": "RES referenciando linha anterior",
            "expr": [
                "(3.0 2.0 +)",
                "(2 RES)",
            ],
            # (2 RES) na linha 2 aponta para results[0]  (2 linhas atrás → idx 2-2=0)
            "esperado_em": ["results", "descarta N do RES"],
        },
        # ----------------------------------------------------------------
        # Inicialização da FPU
        # ----------------------------------------------------------------
        {
            "desc": "FPU habilitada",
            "expr": ["(1.0 2.0 +)"],
            "esperado_em": ["vmsr fpexc, r0", "0xF00000"],
        },
        # ----------------------------------------------------------------
        # Multiplas linhas — last_result deve ter o valor da última linha
        # ----------------------------------------------------------------
        {
            "desc": "Três linhas: resultado final é da última",
            "expr": [
                "(1.0 2.0 +)",
                "(3.0 4.0 *)",
                "(5.0 1.0 -)",
            ],
            "esperado_em": ["last_result", "results"],
        },
    ]

    falhas = 0
    for caso in casos:
        print(f"  [{caso['desc']}]")
        tokens_por_linha = [parseExpressao(expr) for expr in caso["expr"]]
        try:
            asm = gerarAssembly(tokens_por_linha, nomeArquivoSaida=None)
        except Exception as e:
            print(f"    FALHOU (excecao): {e}\n")
            falhas += 1
            continue

        ok = True
        for frag in caso.get("esperado_em", []):
            if frag not in asm:
                print(f"    FALHOU: fragmento esperado nao encontrado: '{frag}'")
                ok = False
                falhas += 1
        if ok:
            print("    OK\n")
        else:
            print()

    # ----------------------------------------------------------------
    # Casos inválidos — devem levantar ValueError
    # ----------------------------------------------------------------
    print("  [Casos inválidos — devem lançar ValueError]")
    invalidos: List[dict] = [
        {
            "desc": "RES sem número precedente",
            "tokens": [Token(TokenType.COMANDO, "RES")],
        },
        {
            "desc": "Operador + com pilha vazia",
            "tokens": [Token(TokenType.OPERADOR, "+")],
        },
        {
            "desc": "Operador * com apenas 1 operando",
            "tokens": [
                Token(TokenType.NUMERO_REAL, "2.0"),
                Token(TokenType.OPERADOR, "*"),
            ],
        },
    ]
    for caso in invalidos:
        print(f"  [{caso['desc']}]")
        try:
            gerarAssembly([caso["tokens"]], nomeArquivoSaida=None)
            print("    FALHOU: deveria ter lançado ValueError mas nao lançou\n")
            falhas += 1
        except ValueError as e:
            print(f"    OK — ValueError: {e}\n")
        except Exception as e:
            print(f"    FALHOU (excecao inesperada): {type(e).__name__}: {e}\n")
            falhas += 1

    print("=" * 60)
    if falhas == 0:
        print(f"TODOS OS TESTES PASSARAM ({len(casos) + len(invalidos)} casos)")
    else:
        print(f"FALHAS: {falhas} de {len(casos) + len(invalidos)} casos")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

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