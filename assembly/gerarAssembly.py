# Crystofer samuel demetino, Gabriel marques simini, Vitor izidoro
# interpretadores B noite frank coelho de alcatara
#
#


#faz a leitura basica do(s) arquivo(s)
def lerArquivo(nomeArquivo, linhas):
    try:
        with open(nomeArquivo, 'r') as arquivo:
            for linha in arquivo:
                if linha.strip():
                    linhas.append(linha.strip())
    except FileNotFoundError:
        print(f"Erro: Nao foi possivel abrir o arquivo '{nomeArquivo}'.")

#Gera o assembly com o tokens

class Token:
    def __init__(self, tipo, valor):
        self.tipo = tipo
        self.valor = valor


def processarLinhas(linhas):
    tokens = []

    for linha in linhas:
        elementos = linha.replace("(", "").replace(")", "").split()

        for e in elementos:
            if e.replace('.', '', 1).isdigit():
                tokens.append(Token("NUMERO", e))
            else:
                tokens.append(Token("OPERADOR", e))

                return tokens


if __name__ == "__main__":
    linhas = []
    lerArquivo("simba.txt", linhas)

    tokens = processarLinhas(linhas)

    for t in tokens:
        print(t.tipo, t.valor)