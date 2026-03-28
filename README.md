# RA1-4: Analisador Léxico e Gerador Assembly ARMv7 (RPN)

**Instituição:** PUCPR  
**Disciplina:** Construção de interpretadores - Turma B - Noite  
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
- **Precisão de cálculos** em 64 bits de ponto flutuante (Norma **IEEE 754**).
- **Arquitetura de Máquina de Pilha Pura:** O interpretador e o gerador de código operam com avaliação tardia (*lazy evaluation*), sem o uso de heurísticas de *lookahead* para decisões semânticas, respeitando rigorosamente a arquitetura RPN autêntica.
- Suporte a aninhamento infinito de expressões delimitadas por parênteses.
- O código Assembly gerado utiliza o co-processador matemático (FPU) do ARM para realizar todas as operações aritméticas e os cálculos dinâmicos de ponteiros de memória diretamente no hardware.
- Geração de um arquivo `tokens_gerados.json` detalhando a análise léxica da última execução.

---

## Operações Suportadas

A linguagem RPN desenvolvida suporta os seguintes operadores e comandos:

* **Matemática Básica:** `+` (Soma), `-` (Subtração), `*` (Multiplicação), `/` (Divisão Real).
* **Matemática Avançada:** `//` (Divisão Inteira com truncamento), `%` (Resto da divisão), `^` (Potenciação com expoente inteiro).
* **Comandos de Memória:** * `(V VARNAME MEM)`: Guarda um valor `V` (que pode ser fruto de uma expressão) em uma variável de memória.
  * `(VARNAME)`: Lê e carrega o valor da variável de memória para a pilha.
  * *Regras Lexicais para `VARNAME`:* O identificador da variável deve ser escrito **estritamente em letras maiúsculas** (podendo conter o caractere sublinhado `_`). Não é permitido o uso de números ou caracteres especiais, e não pode assumir o nome da palavra reservada `RES`.
* **Comando de Histórico:** * `(N RES)`: Retorna o resultado exato da expressão matemática avaliada `N` linhas anteriores no mesmo arquivo.
  * *Comportamento Dinâmico:* O valor de `N` não precisa ser um literal rígido. O compilador gera código Assembly capaz de calcular o endereço e o deslocamento (*offset*) da memória em tempo de execução, permitindo que `N` seja resultado de equações matemáticas complexas e uso de variáveis.

---

## Como Executar o Programa

O projeto possui um orquestrador central (`main.py`) que gerencia todo o fluxo de análise e geração.

**Pré-requisitos:**
* Python 3.8 ou superior instalado.
* Simulador **CPULATOR** (arquitetura ARMv7 DEC1-SOC) para testar o código Assembly final gerado.

**Passo a passo:**
1. Clone este repositório para a sua máquina local.
2. Abra o terminal na pasta raiz do projeto (`RA1-4-Analisador-Lexico`).
3. Execute o script principal passando o caminho do arquivo de testes (`.txt`) como argumento de linha de comando. 

**Exemplo de comando:**
```bash
python main.py "assembly copy/arquivosTeste/teste1.txt"
```
##  Regras Estritas de Sintaxe (Aviso para Testes)

Devido à natureza determinística do Autômato Finito construído, a linguagem exige **separação explícita por espaços** entre todos os operandos, operadores e parênteses que não façam parte do mesmo identificador.
*  **Incorreto:** `(2.0 3.0+)` ou `(1.0RES)`
*  **Correto:** `( 2.0 3.0 + )` ou `( 1.0 RES )`

A ausência de espaços fará com que a Máquina de Estados interprete a cadeia como um token inválido, disparando um Erro Léxico e abortando a compilação por segurança.

---

## Testando no Simulador (CPULATOR)

1. Acesse o [CPULATOR ARMv7]([https://cpulator.01xz.net/?sys=arm-de1soc](https://cpulator.01xz.net/?sys=arm-de1soc&d_audio=48000)).
2. Limpe o editor padrão e cole todo o conteúdo do arquivo `saida.s`.
3. Pressione **F5** (Compile and Load) para invocar o montador.
4. Pressione **F2** (Run) para executar.
