# RA1-4: Analisador Léxico e Gerador Assembly ARMv7 (RPN)

**Instituição:** [Substitua pelo Nome da Sua Instituição, ex: PUCPR]  
**Disciplina:** Interpretadores B - Noite  
**Professor:** Frank Coelho de Alcântara  
**Grupo no Canvas:** RA1-4  

---

## Equipe

Os membros responsáveis pelo desenvolvimento deste projeto são:

* **Crystofer Demetino dos Santos** - GitHub: [@CrySamuel](https://github.com/CrySamuel)
* **Gabriel Simini** - GitHub: [@GalSimini](https://github.com/GalSimini)
* **Vitor Rodrigues Izidoro** - GitHub: [@vitor-izidoro](https://github.com/vitor-izidoro)

---

## Sobre o Projeto

Este projeto é a Primeira Fase da construção de um compilador. Trata-se de um **Analisador Léxico** construído estritamente via **Autômatos Finitos Determinísticos (AFD)** em Python, sem o uso de expressões regulares. 

O programa lê arquivos de texto contendo expressões matemáticas aninhadas em **Notação Polonesa Reversa (RPN)**, realiza a avaliação matemática em Python e atua como um gerador de código, produzindo código **Assembly** perfeitamente compatível com a arquitetura **ARMv7 DEC1-SOC (v16.1)**.

### Características Principais:
- Precisão de cálculos em 64 bits de ponto flutuante (Norma **IEEE 754**).
- Suporte a aninhamento infinito de expressões delimitadas por parênteses.
- O código Assembly gerado utiliza o co-processador matemático (FPU) do ARM para realizar todas as operações diretamente na CPU.
- Geração de um arquivo `tokens_gerados.json` detalhando a análise léxica da última execução.

---

## Operações Suportadas

A linguagem RPN desenvolvida suporta os seguintes operadores e comandos:

* **Matemática Básica:** `+` (Soma), `-` (Subtração), `*` (Multiplicação), `/` (Divisão Real).
* **Matemática Avançada:** `//` (Divisão Inteira com truncamento), `%` (Resto da divisão), `^` (Potenciação com expoente inteiro).
* **Comandos de Memória:** * `(V VARNAME MEM)`: Guarda um valor em uma variável de memória.
  * `(VARNAME)`: Lê e carrega o valor da variável de memória.
* **Comando de Histórico:** * `(N RES)`: Retorna o resultado exato da expressão matemática avaliada `N` linhas anteriores no mesmo arquivo.

---

## Como Executar o Programa

O projeto possui um orquestrador central (`main.py`) que gerencia todo o fluxo de análise e geração.

**Pré-requisitos:**
* Python 3.8 ou superior instalado.

**Passo a passo:**
1. Clone este repositório para a sua máquina local.
2. Abra o terminal na pasta raiz do projeto (`RA1-4-Analisador-Lexico`).
3. Execute o script principal passando o caminho do arquivo de testes (`.txt`) como argumento de linha de comando. 

**Exemplo de comando:**
```bash
python main.py "assembly copy/arquivosTeste/teste1.txt"
