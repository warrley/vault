# Guia Geral de Formatação, Citações, Equações e Redação Científica

Este guia estabelece as diretrizes universais e boas práticas para a escrita de artigos científicos e relatórios em LaTeX no contexto de modelagem computacional e redes neurais informadas por física (PINNs).

---

## 1. Diretrizes de Citações e Referências Bibliográficas

* **Estilo Autor-Data Obrigatório (ABNT NBR 10520):**
  * **Citação Indireta (entre parênteses):** `(LAST NAME, ANO)`
    * Comando LaTeX: `\parencite{chave}` $\to$ Ex.: `(PEREIRA, 2019)`, `(TURING, 1952)`, `(WANG et al., 2022)`.
  * **Citação Direta no Texto (fora de parênteses):** `Last Name (ANO)`
    * Comando LaTeX: `\textcite{chave}` $\to$ Ex.: `Pereira (2019) propôs...`, `Segundo Turing (1952)...`.
* **Hiperlinks Interativos (`hyperref`):**
  * Todas as citações bibliográficas, referências cruzadas a seções (`\ref{sec:...}`), equações (`\eqref{eq:...}`), figuras e tabelas devem ser hiperlinks clicáveis.
  * Recomenda-se coloração sutil e profissional para publicação (ex.: `linkcolor=blue!70!black`, `citecolor=blue!70!black`, `urlcolor=blue!70!black`).
* **Seção de Referências Bibliográficas:**
  * Deve ser formatada em **duas colunas compactas** (`\begin{multicols}{2} ... \end{multicols}`) com tamanho de fonte reduzido (`\fontsize{7.5pt}{8.5pt}\selectfont` ou `\scriptsize`) para otimização de espaço.

---

## 2. Tipografia e Formatação de Equações

* **Fontes Matemáticas Padrão do LaTeX:**
  * Utilizar sempre a **tipografia matemática padrão clássica do LaTeX** (Computer Modern / AMS Math via `amsmath`, `amssymb`, `amsfonts`).
  * Evitar pacotes que forçam fontes matemáticas não-padrão (como `mathptmx` puro para matemática), preservando o espaçamento correto de delimitadores, operadores diferenciais ($\nabla, \partial, \Delta$) e letras gregas.
* **Notação Exponencial:**
  * Utilizar expressamente a base natural com expoente sobrescrito $e^{(\cdot)}$:
    $$e^{-k \left[(x - x_0)^2 + (y - y_0)^2\right]}, \quad e^{\lambda t}, \quad e^{-\gamma \sum \mathcal{L}_j}$$
  * Evitar a grafia em texto `exp(...)` em equações formais.
* **Normas e Vetores:**
  * Utilizar a notação explícita de norma com subíndices de espaço funcional:
    $$\|\mathbf{u}(t) - \mathbf{u}^*\|_{L_2} = \sqrt{\frac{1}{|\Omega|} \int_\Omega \left(u(x,y,t) - u^*(x,y)\right)^2 \, \mathrm{d}\Omega}$$

---

## 3. Formalização Geral de Arquiteturas de Redes Neurais (MLP / PINNs)

Ao descrever redes neurais em artigos matemáticos e computacionais, deve-se adotar uma formalização hierárquica em duas etapas:

1. **Definição Algébrica Geral (com ativação genérica $\sigma$):**
   * **Camada de Entrada:**
     $$\mathbf{h}^{(0)} = \mathbf{z} \in \mathbb{R}^{d_{\mathrm{in}}}$$
   * **Camadas Ocultas ($\ell = 1, \dots, L$):**
     $$\mathbf{h}^{(\ell)} = \sigma\left(\mathbf{W}^{(\ell)}\mathbf{h}^{(\ell-1)} + \mathbf{b}^{(\ell)}\right), \quad \mathbf{W}^{(\ell)} \in \mathbb{R}^{d_\ell \times d_{\ell-1}}, \; \mathbf{b}^{(\ell)} \in \mathbb{R}^{d_\ell}$$
   * **Camada de Saída:**
     $$\hat{\mathbf{w}}_\theta(\mathbf{z}) = \mathbf{W}^{(L+1)}\mathbf{h}^{(L)} + \mathbf{b}^{(L+1)} \in \mathbb{R}^{d_{\mathrm{out}}}$$

2. **Especificação e Justificativa da Função de Ativação:**
   * Apresentar a expressão analítica da ativação adotada após a definição geral:
     $$\sigma(z) = \tanh(z) = \frac{e^z - e^{-z}}{e^z + e^{-z}} \in C^\infty(\mathbb{R})$$
   * **Justificativa Física:** Explicitar a classe de regularidade (ex.: $\tanh \in C^\infty$) necessária para que a diferenciação automática via *autograd* compute derivadas espaciais de 2ª ordem ($\nabla^2 \hat{u}$) sem descontinuidades.
3. **Contagem Total de Parâmetros:**
   * Apresentar o número exato de parâmetros treináveis da rede ($N_{\theta} = \sum (\text{pesos} + \text{bias})$) e o método de inicialização (ex.: Xavier / Glorot Normal).

---

## 4. Diretrizes de Nomenclatura e Uso de Acrônimos

* **Regra da Primeira Menção:**
  * Na primeira ocorrência de qualquer método, modelo ou técnica (tanto no **Resumo/Abstract** quanto no **corpo do texto**), deve-se escrever o **nome completo por extenso seguido do acrônimo entre parênteses**.
  * *Exemplo:*  
    > "... o **Método de Diferenças Finitas (MDF)** acoplado ao esquema de **Direções Alternadas Implícitas (ADI)**..."
    > "... as **Redes Neurais Informadas por Física (PINNs)**..."
* **Uso Estrito Posterior:**
  * Após a primeira menção, utilizar **exclusivamente o acrônimo** em todo o texto, tabelas, equações e legendas de figuras (`MDF`, `ADI`, `MDF ADI`, `PINN`, `EDP`, `EDO`).

---

## 5. Diretrizes de Extensão e Ajuste de Layout (Regra de Limite de Páginas)

* **Limite Rígido de Páginas:**
  * O documento deve respeitar estritamente o número exato de páginas estipulado pelo evento ou periódico (ex.: **exatamente 5 páginas** no modelo EU UFC / Prism).
* **Harmonização Visual:**
  * Ajustar proporcionalmente o espaçamento entre seções (`\titlespacing*`), margens (`\geometry`) e espaçamento entrelinhas (`\setstretch`) para que a última página seja preenchida até o final com as referências, sem deixar linhas órfãs nem transbordar para uma página extra.
