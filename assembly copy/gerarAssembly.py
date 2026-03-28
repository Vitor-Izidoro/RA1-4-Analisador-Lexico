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

from tokens import Token, TokenType  
from lexer import parseExpressao     

# lerArquivo

def lerArquivo(nomeArquivo: str, linhas: list) -> None:
    """Lê o arquivo de expressões e popula linhas ignorando linhas vazias."""
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

# gerarAssembly

def gerarAssembly(tokens_por_linha, nomeArquivoSaida: str = "saida.s") -> str:
    """
    Traduz uma lista de linhas tokenizadas para Assembly ARMv7 (CPUlator DEC1-SOC v16.1).

    Registradores fixos durante toda a execução:
      r7  = SP base (restaurado no início de cada linha)
      r9  = contador do loop de potenciação (evita colidir com r1)
      r10 = &last_result
      r11 = &results[0]
      r12 = temporário para offset de results
    """

    if not tokens_por_linha:
        return ""

    linhas_tokens: List[List[Token]] = (
        tokens_por_linha if isinstance(tokens_por_linha[0], list) else [tokens_por_linha]
    )

    num_linhas = len(linhas_tokens)

    # Seção .data
    data_lines: List[str] = [
        ".global _start",
        ".section .data",
        ".balign 8",
        "last_result: .double 0.0",
        ".balign 8",
        f"results: .space {num_linhas * 8}",
        ".balign 4",
        "display_lut: .word 0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71",
        ".balign 8",   # garante alinhamento 8 bytes para todas as constantes double
    ]

    # Seção .text
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
    
    # Helpers .data

    def get_unique_label(prefix: str) -> str:
        nonlocal contador_rotulo
        lbl = f"{prefix}_{contador_rotulo}"
        contador_rotulo += 1
        return lbl

    def ensure_const_double(valor_str: str) -> str:
        """Cria a constante f64 no .data apenas uma vez; reutiliza nas demais."""
        nonlocal contador_const
        try:
            # Convertemos para float para garantir que o Python trate como decimal
            valor_numerico = float(valor_str)
            # 'repr' ou f-string com float garante o ".0" (ex: 1.0)
            normalizado = repr(valor_numerico)
        except ValueError:
            normalizado = valor_str

        if normalizado not in const_cache:
            nome = f"const_{contador_const}"
            const_cache[normalizado] = nome
            data_lines.extend([".balign 8", f"{nome}: .double {normalizado}"])
            contador_const += 1
        return const_cache[normalizado]
    def ensure_var_memoria(nome: str) -> str:
        """Reserva espaço f64 no .data para a variável, se ainda não existe."""
        if nome not in vars_memoria:
            label = f"var_{nome}"
            vars_memoria[nome] = label
            data_lines.extend([".balign 8", f"{label}: .double 0.0"])
        return vars_memoria[nome]

    # Emissores .text

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
        text_lines.extend([
            "    vpop.f64 {d1}",
            "    vpop.f64 {d0}",
            f"    {inst} d2, d0, d1",
            "    vpush.f64 {d2}",
        ])
        stack_depth -= 1

    def emit_idiv_trunc(linha_idx: int) -> None:
        """Divisão inteira truncada em direção a zero."""
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError(f"Linha {linha_idx + 1}: '//' com apenas {stack_depth} operando(s)")
        text_lines.extend([
            "    vpop.f64 {d1}",
            "    vpop.f64 {d0}",
            "    vdiv.f64 d2, d0, d1",
            "    vcvtr.s32.f64 s4, d2",
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
        """Potenciação por loop: base^exp (exp inteiro positivo); base^0 = 1.0.
           Usa r9 como contador para não colidir com r1 usado nos stores."""
        nonlocal stack_depth
        if stack_depth < 2:
            raise ValueError(f"Linha {linha_idx + 1}: '^' com apenas {stack_depth} operando(s)")
        loop_lbl = get_unique_label("pow_loop")
        done_lbl = get_unique_label("pow_done")
        one_lbl  = ensure_const_double("1.0")
        text_lines.extend([
            "    vpop.f64 {d1}",
            "    vpop.f64 {d0}",
            "    vcvtr.s32.f64 s4, d1",
            "    vmov r9, s4",            
            f"    ldr r0, ={one_lbl}",
            "    vldr.f64 d2, [r0]",
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
        """Carrega variável da memória e empilha.
           Usa r6 para o endereço (consistente com emit_store_var)."""
        nonlocal stack_depth
        label = ensure_var_memoria(nome)
        text_lines.extend([
            f"    ldr r6, ={label}",       
            "    vldr.f64 d0, [r6]",
            "    vpush.f64 {d0}",
        ])
        stack_depth += 1

    def emit_store_var(nome: str, linha_idx: int) -> None:
        """Pop → salva na variável → push de volta (não-destrutivo).
           Usa r6 para o endereço da variável (r1 pode ser usado pelo linker
           ao resolver literais longos e causar colisões silenciosas)."""
        nonlocal stack_depth
        if stack_depth < 1:
            raise ValueError(f"Linha {linha_idx + 1}: store em '{nome}' sem valor na pilha")
        label = ensure_var_memoria(nome)
        text_lines.extend([
            "    vpop.f64 {d0}",
            f"    ldr r6, ={label}",       # r6 em vez de r1
            "    vstr.f64 d0, [r6]",
            "    vpush.f64 {d0}",
        ])

    def emit_load_result(idx: int, linha_atual: int) -> None:
        """Carrega results[idx] na pilha usando r11 fixo (sem literal pool)."""
        nonlocal stack_depth
        if idx < 0:
            raise ValueError(
                f"Linha {linha_atual + 1}: (N RES) aponta para índice inválido ({idx})"
            )
        offset = idx * 8
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
        return next(
            (tokens[j] for j in range(start, len(tokens))
             if tokens[j].tipo not in (TokenType.PARENTESES, TokenType.EOF)),
            None,
        )

    # Loop principal-------------------------

    for linha_idx, tokens in enumerate(linhas_tokens):
        stack_depth = 0
        last_literal: Optional[str] = None
        pending_mem_var: Optional[str] = None

        text_lines.extend(["", f"    @ ---- linha {linha_idx + 1} ----"])
        text_lines.append("    mov sp, r7")   # restaura SP antes de qualquer vpush

        i = 0
        while i < len(tokens):
            t = tokens[i]

            if t.tipo == TokenType.ERRO:
                raise ValueError(f"Erro léxico: '{t.valor}' (linha {linha_idx + 1})")

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

            # --- Identificador de memória ---
            if t.tipo == TokenType.MEMORIA:
                if t.valor == "MEM":
                    if pending_mem_var is None:
                        raise ValueError(f"Linha {linha_idx + 1}: 'MEM' sem variável.")
                    emit_store_var(pending_mem_var, linha_idx)
                    pending_mem_var = None
                else:
                    proximo = peek_next_significant(tokens, i + 1)
                    # Se o próximo for 'MEM', preparamos para o Store
                    if proximo and proximo.tipo == TokenType.MEMORIA and proximo.valor == "MEM":
                        pending_mem_var = t.valor
                    else:
                        # Caso contrário, é um LOAD puro
                        emit_load_var(t.valor)
                i += 1
                continue

            # --- Comando RES Dinâmico ---
            if t.tipo == TokenType.COMANDO and t.valor == "RES":
                stack_depth -= 1 
                text_lines.extend([
                    "    @ --- COMANDO RES DINÂMICO ---",
                    "    vpop.f64 {d0}",
                    "    vcvtr.s32.f64 s0, d0",
                    "    vmov r1, s0",
                    f"    mov r2, #{linha_idx}",
                    "    subs r3, r2, r1",
                    "    cmp r3, #0",
                    "    movlt r3, #0",
                    "    add r4, r11, r3, lsl #3",
                    "    vldr.f64 d0, [r4]",
                    "    vpush.f64 {d0}",
                ])
                stack_depth += 1
                i += 1
                continue

            raise ValueError(f"Token inesperado: {t} (linha {linha_idx + 1})")

        if stack_depth != 1:
            raise ValueError(
                f"Linha {linha_idx + 1}: pilha com {stack_depth} valor(es) ao "
                f"final — esperado exatamente 1."
            )

        # Salva resultado em last_result (r10) e results[linha_idx] (r11+offset)
        # r12 é usado como temporário para o offset — r11 NUNCA é modificado
        offset = linha_idx * 8
        text_lines.append("    vpop.f64 {d0}")
        text_lines.append("    vstr.f64 d0, [r10]")   # last_result
        if offset > 0:
            text_lines.extend([
                f"    add r12, r11, #{offset}",
                "    vstr.f64 d0, [r12]",              # results[linha_idx]
            ])
        else:
            text_lines.append("    vstr.f64 d0, [r11]")  # results[0]
        text_lines.append("    dsb")


    # r10 ainda aponta para last_result — sem necessidade de literal pool e  decodificador para 4 displays de 7 segmentos
    # ------------------------------------------------------------------
    text_lines.extend([
        "",
        "    @ --- DECODIFICADOR PARA 4 DISPLAYS ---",
        "    vldr.f64 d0, [r10]",              # lê last_result via r10 (sem ldr literal)
        "    vcvt.s32.f64 s0, d0",             # converte double → inteiro (trunca)
        "    vmov r1, s0",
        "    ldr r2, =0xFF200020",             # endereço HEX3-HEX0
        "    ldr r3, =display_lut",
        "    mov r4, #0",                      # acumulador dos 4 dígitos
        "",
        "    @ HEX0 (unidades)",
        "    and r6, r1, #0xF",
        "    ldr r5, [r3, r6, lsl #2]",        # r5 em vez de r7 (preserva SP base)
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
        "    str r4, [r2]",                    # escreve nos 4 displays de uma vez
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
    print("=" * 60)
    print("TESTE: testarGerarAssembly()")
    print("=" * 60)

    casos: List[dict] = [
        {
            "desc": "Soma simples (3.5 + 2.0) = 5.5",
            "expr": ["(3.5 2.0 +)"],
            "esperado_em": ["vadd.f64", "last_result", "results"],
        },
        {
            "desc": "Subtração (10.0 - 3.5) = 6.5",
            "expr": ["(10.0 3.5 -)"],
            "esperado_em": ["vsub.f64"],
        },
        {
            "desc": "Multiplicação (1.5 * 2.0) = 3.0",
            "expr": ["(1.5 2.0 *)"],
            "esperado_em": ["vmul.f64"],
        },
        {
            "desc": "Divisão real (7.0 / 2.0) = 3.5",
            "expr": ["(7.0 2.0 /)"],
            "esperado_em": ["vdiv.f64"],
        },
        {
            "desc": "Divisão inteira (7.0 // 2.0) = 3.0",
            "expr": ["(7.0 2.0 //)"],
            "esperado_em": ["vcvtr.s32.f64"],
        },
        {
            "desc": "Resto (7.0 % 3.0) = 1.0",
            "expr": ["(7.0 3.0 %)"],
            "esperado_em": ["vsub.f64 d2, d0, d3"],
        },
        {
            "desc": "Potenciação (2.0 ^ 3) = 8.0",
            "expr": ["(2.0 3.0 ^)"],
            "esperado_em": ["pow_loop", "pow_done", "vmov r9, s4"],
        },
        {
            "desc": "Expressão aninhada ((1.5*2.0)/(3.0*4.0))",
            "expr": ["((1.5 2.0 *) (3.0 4.0 *) /)"],
            "esperado_em": ["vmul.f64", "vdiv.f64"],
        },
        {
            "desc": "Store explícito (5.0 TOTAL MEM)",
            "expr": ["(5.0 TOTAL MEM)"],
            "esperado_em": ["var_TOTAL", "vstr.f64"],
        },
        {
            "desc": "Load de variável após store",
            "expr": ["(5.0 TOTAL MEM)", "(TOTAL)"],
            "esperado_em": ["var_TOTAL", "vldr.f64"],
        },
        {
            "desc": "RES referenciando linha anterior",
            "expr": ["(3.0 2.0 +)", "(2 RES)"],
            "esperado_em": ["descarta N=2", "r11"],
        },
        {
            "desc": "(0 RES) retorna 0.0",
            "expr": ["(1.0 2.0 +)", "(0 RES)"],
            "esperado_em": ["(0 RES) → 0.0"],
        },
        {
            "desc": "FPU habilitada com CP10+CP11",
            "expr": ["(1.0 2.0 +)"],
            "esperado_em": ["vmsr fpexc, r0", "0xF00000"],
        },
        {
            "desc": "r10 e r11 carregados no prólogo",
            "expr": ["(1.0 2.0 +)"],
            "esperado_em": ["ldr r10, =last_result", "ldr r11, =results"],
        },
        {
            "desc": "Display usa r5 (não r7) e r10 direto",
            "expr": ["(1.0 2.0 +)"],
            "esperado_em": ["vldr.f64 d0, [r10]", "ldr r5, [r3"],
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
                print(f"    FALHOU: fragmento ausente: '{frag}'")
                ok = False
                falhas += 1
        if ok:
            print("    OK\n")
        else:
            print()

    # Casos inválidos
    print("  [Casos inválidos — devem lançar ValueError]")
    invalidos = [
        {"desc": "RES sem número precedente",
         "tokens": [Token(TokenType.COMANDO, "RES")]},
        {"desc": "Operador + com pilha vazia",
         "tokens": [Token(TokenType.OPERADOR, "+")]},
        {"desc": "Operador * com apenas 1 operando",
         "tokens": [Token(TokenType.NUMERO_REAL, "2.0"), Token(TokenType.OPERADOR, "*")]},
    ]
    for caso in invalidos:
        print(f"  [{caso['desc']}]")
        try:
            gerarAssembly([caso["tokens"]], nomeArquivoSaida=None)
            print("    FALHOU: deveria ter lançado ValueError\n")
            falhas += 1
        except ValueError as e:
            print(f"    OK — ValueError: {e}\n")
        except Exception as e:
            print(f"    FALHOU (excecao inesperada): {type(e).__name__}: {e}\n")
            falhas += 1

    print("=" * 60)
    total = len(casos) + len(invalidos)
    if falhas == 0:
        print(f"TODOS OS TESTES PASSARAM ({total} casos)")
    else:
        print(f"FALHAS: {falhas} de {total} casos")
    print("=" * 60)


# Ponto de entrada

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
    
