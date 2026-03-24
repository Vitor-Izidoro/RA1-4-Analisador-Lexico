# Crystofer samuel demetino, Gabriel marques simini, Vitor izidoro
# interpretadores B noite frank coelho de alcatara

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
MAQUINA_DIR = PROJECT_ROOT / "MaquinaDeEstado"
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

    if tokens_por_linha and isinstance(tokens_por_linha[0], list):
        tokens = [t for linha in tokens_por_linha for t in linha]
    else:
        tokens = tokens_por_linha

    data_lines = [
        ".global _start",
        ".section .data",
        ".balign 8",
        "var_MEM: .double 0.0",
    ]

    text_lines = [
        ".section .text",
        ".global _start",
        "_start:",
    ]

    contador_const = 0

    def emit_push_const_double(valor_str: str) -> None:
        nonlocal contador_const
        nome_const = f"const_{contador_const}"
        data_lines.append(f"{nome_const}: .double {valor_str}")
        text_lines.extend(
            [
                f"ldr r0, ={nome_const}",
                "vldr.f64 d0, [r0]",
                "vpush.f64 {d0}",
            ]
        )
        contador_const += 1

    for t in tokens:
        if t.tipo == TokenType.ERRO:
            raise ValueError(f"Erro Léxico no token: {t.valor}")

        if t.tipo == TokenType.PARENTESES or t.tipo == TokenType.EOF:
            continue

        if t.tipo == TokenType.NUMERO_REAL:
            emit_push_const_double(t.valor)
            continue

        if t.tipo == TokenType.OPERADOR:
            if t.valor == "+":
                text_lines.extend(
                    [
                        "vpop.f64 {d1}",
                        "vpop.f64 {d0}",
                        "vadd.f64 d2, d0, d1",
                        "vpush.f64 {d2}",
                    ]
                )
            elif t.valor == "-":
                text_lines.extend(
                    [
                        "vpop.f64 {d1}",
                        "vpop.f64 {d0}",
                        "vsub.f64 d2, d0, d1",
                        "vpush.f64 {d2}",
                    ]
                )
            elif t.valor == "*":
                text_lines.extend(
                    [
                        "vpop.f64 {d1}",
                        "vpop.f64 {d0}",
                        "vmul.f64 d2, d0, d1",
                        "vpush.f64 {d2}",
                    ]
                )
            elif t.valor == "/":
                text_lines.extend(
                    [
                        "vpop.f64 {d1}",
                        "vpop.f64 {d0}",
                        "vdiv.f64 d2, d0, d1",
                        "vpush.f64 {d2}",
                    ]
                )
            elif t.valor == "//":
                # trunc(a/b) como inteiro e converte de volta pra f64
                text_lines.extend(
                    [
                        "vpop.f64 {d1}",
                        "vpop.f64 {d0}",
                        "vdiv.f64 d2, d0, d1",
                        "vcvt.s32.f64 s4, d2",
                        "vcvt.f64.s32 d2, s4",
                        "vpush.f64 {d2}",
                    ]
                )
            else:
                raise ValueError(f"Operador ainda não implementado no Dia 1: {t.valor}")
            continue

        if t.tipo in (TokenType.MEMORIA, TokenType.COMANDO):
            raise ValueError(f"Funcionalidade ainda não implementada no Dia 1: {t.tipo.name} {t.valor}")

        raise ValueError(f"Token inesperado: {t}")

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