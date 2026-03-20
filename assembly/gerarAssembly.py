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