import sys
import json
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Isso garante que o Python ache os arquivos nas subpastas, não importa de onde você rode
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "Maquina de Estado"))
sys.path.insert(0, str(ROOT_DIR / "assembly copy"))
# Se o executor estiver na raiz, ele já acha automático. Se estiver em outra pasta, adicione aqui.

# --- IMPORTS DOS MÓDULOS DOS ALUNOS ---
from lexer import parseExpressao              # Aluno 1
from executor import executarExpressao        # Aluno 2
from gerarAssembly import gerarAssembly, lerArquivo # Aluno 3

# --- FUNÇÕES DO ALUNO 4 ---

def exibirResultados(linhas_tokens):
    memoria_global = {}
    historico_resultados = []
    
    print("\n" + "="*40)
    print("   RESULTADOS DA EXECUÇÃO EM PYTHON")
    print("="*40)
    
    for idx, tokens_linha in enumerate(linhas_tokens):
        try:
            res = executarExpressao(tokens_linha, memoria_global, historico_resultados, idx)
            print(f"Linha {idx + 1:02d}: {res}")
        except Exception as e:
            print(f"Linha {idx + 1:02d}: ERRO -> {str(e)}")
            historico_resultados.append(0.0)
            
    print("="*40 + "\n")


def salvar_tokens_json(tokens_por_linha, nome_arquivo="tokens_gerados.json"):
    dados = []
    for linha_idx, tokens in enumerate(tokens_por_linha):
        linha_formatada = [{"tipo": t.tipo.name, "valor": t.valor} for t in tokens]
        dados.append({"linha": linha_idx + 1, "tokens": linha_formatada})
        
    with open(ROOT_DIR / nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print(f"[+] Tokens salvos em '{nome_arquivo}'")


# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso correto: python main.py <caminho_do_arquivo.txt>")
        sys.exit(1)

    caminho_arquivo = sys.argv[1]
    linhas = []
    
    # 1. Lê o arquivo
    lerArquivo(caminho_arquivo, linhas)
    
    # 2. Analisador Léxico (Aluno 1)
    tokens_por_linha = [parseExpressao(linha) for linha in linhas]
    
    # 3. Execução Matemática (Alunos 2 e 4)
    # exibirResultados(tokens_por_linha)
    
    # 4. Salvar tokens
    salvar_tokens_json(tokens_por_linha)
    
    # 5. Geração de Assembly (Aluno 3)
    # Salvando o .s na mesma pasta de onde o script foi chamado
    assembly_final = gerarAssembly(tokens_por_linha, nomeArquivoSaida="saida.s")
    
    print("[+] Código Assembly gerado com sucesso em 'saida.s'!")