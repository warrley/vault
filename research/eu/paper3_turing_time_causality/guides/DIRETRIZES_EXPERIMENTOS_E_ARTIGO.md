# Diretrizes de Experimentos, Modelagem e Redação do Artigo (Schnakenberg PINN vs MDF ADI)

Este documento sintetiza todas as diretrizes metodológicas, parâmetros exatos da tese de Pereira (2019), arquitetura de redes neurais, regras de visualização científica e normas de redação para o artigo submetido aos Encontros Universitários da UFC.

---

## 1. Parâmetros Físicos e Numéricos Exatos (Tese Pereira, 2019)

Os experimentos devem replicar com precisão matemática os parâmetros da **Tabela 27 e Equação 2.31** da tese de doutorado de Ricardo Reis Pereira (LNCC, 2019):

* **Sistema de EDPs:** Modelo de reação-difusão de Schnakenberg bidimensional:
  $$\frac{\partial u}{\partial t} = D_u \nabla^2 u + \kappa \left( a - u + u^2 v \right)$$
  $$\frac{\partial v}{\partial t} = D_v \nabla^2 v + \kappa \left( b - u^2 v \right)$$
* **Domínio Espacial:** $\Omega = [0, 1] \times [0, 1] = [0, 1]^2$ com $L = 1{,}0$.
* **Horizonte Temporal:** $t \in [0, 2{,}0\,\text{s}]$ (com $t_{\max} = 2{,}0$).
* **Parâmetros Cinéticos:** $a = 0{,}1305, \; b = 0{,}7695, \; \kappa = 100{,}0$.
* **Coeficientes de Difusão:** $D_u = D_1 = 0{,}05, \; D_v = D_2 = 1{,}0$ (Razão rígida $D_v / D_u = 20$).
* **Ponto de Equilíbrio Homogêneo:**
  $$u^* = a + b = 0{,}9000, \qquad v^* = \frac{b}{(a + b)^2} = 0{,}9500$$
* **Perturbação Inicial Exata (Eq. 2.31):**
  $$u(x, y, 0) = u^* + 10^{-3} e^{-100\left[\left(x - \frac{1}{3}\right)^2 + \left(y - \frac{1}{2}\right)^2\right]}, \quad v(x, y, 0) = v^*$$
* **Condições de Contorno:** Neumann homogêneo (fluxo nulo $\frac{\partial u}{\partial n} = \frac{\partial v}{\partial n} = 0$) nas 4 bordas do domínio.
* **Instantes de Amostragem (Snapshots da Tese):** $t \in \{0{,}02, \; 0{,}41, \; 0{,}81, \; 1{,}21, \; 1{,}60, \; 2{,}00\}\,\text{s}$.

---

## 2. Arquitetura da Rede Neural (PINN Vanilla - Pure MLP)

* **Topologia:** Perceptron Multicamadas puro (*Pure MLP*) sem camadas convolucionais ou blocos residuais.
* **Profundidade e Largura:** $5$ camadas ocultas com $128$ neurônios cada ($6$ camadas no total).
* **Entrada:** $(x, y, t) \in \mathbb{R}^3$.
* **Saída:** $(\hat{u}, \hat{v}) \in \mathbb{R}^2$.
* **Total de Parâmetros Treináveis:** $512 + 4 \times 16.512 + 258 = \mathbf{66.818}$.
* **Função de Ativação:**
  Definida genericamente como $\sigma(\cdot)$ na formulação geral e especificada como:
  $$\sigma(z) = \tanh(z) = \frac{e^z - e^{-z}}{e^z + e^{-z}} \in C^\infty(\mathbb{R})$$
  *(Obrigatória para garantir derivadas de 2ª ordem contínuas no cálculo do Laplaciano $\nabla^2 u$ via autograd).*
* **Inicialização de Pesos:** Xavier / Glorot Normal ($\mathbf{W} \sim \mathcal{N}(0, 2/(n_{\mathrm{in}} + n_{\mathrm{out}}))$) com bias nulo.
* **Pontos de Colocação:**
  * Interior do domínio: $N_f = 10.000$ pontos em $\Omega \times [0, T]$.
  * Condição inicial: $N_0 = 2.500$ pontos em $t = 0$.
  * Condições de contorno: $N_b = 2.000$ pontos nas 4 bordas ($500$ por face).
* **Treinamento e GPU:**
  * $20.000$ épocas completas em GPU NVIDIA com CUDA ativado.
  * Otimizador Adam ($\eta_0 = 10^{-3}$) com agendador `CosineAnnealingLR` decaindo até $\eta_{\min} = 10^{-5}$.
  * Salvamento obrigatório do histórico completo de perdas ($\mathcal{L}_{\mathrm{total}}, \mathcal{L}_{\mathrm{pde}, u}, \mathcal{L}_{\mathrm{pde}, v}, \mathcal{L}_{\mathrm{ic}}, \mathcal{L}_{\mathrm{bc}}$, lr) em `.npz` e `.csv`.

---

## 3. Diretrizes de Nomenclatura e Uso de Acrônimos (MDF e ADI)

* **Primeira Menção no Texto (Resumo e Introdução):**
  Definir expressamente os termos por extenso acompanhados dos acrônimos entre parênteses:
  > *"... o **Método de Diferenças Finitas (MDF)** com **Direções Alternadas Implícitas (ADI)** linearizado de Pereira (2019)..."*
* **Uso Posterior em Todo o Documento:**
  Utilizar **estritamente apenas os acrônimos**:
  * `MDF` para Método de Diferenças Finitas.
  * `ADI` para Direções Alternadas Implícitas.
  * `MDF ADI` para o método numérico acoplado.

---

## 4. Diretrizes de Notação Matemática e Citações

* **Notação Exponencial:**
  * Utilizar expressamente $e^{(\cdot)}$ (ex.: $e^{-100\left[(\dots)^2 + (\dots)^2\right]}$ e $e^{\lambda t}$), evitando a grafia em texto `exp(...)`.
* **Fontes Matemáticas no LaTeX:**
  * Utilizar a tipografia matemática padrão clássica do LaTeX (Computer Modern / AMS Math), sem sobrecarregar símbolos com fontes exóticas.
* **Estilo de Citação Autor-Data (ABNT NBR 10520):**
  * Citações indiretas entre parênteses: `(LAST NAME, ANO)` $\to$ `\parencite{pereira2019}` produz **(PEREIRA, 2019)**, `(TURING, 1952)`, `(WANG et al., 2022)`.
  * Citações diretas no texto: `\textcite{pereira2019}` produz **Pereira (2019)**.
* **Links Clicáveis:**
  * Todas as citações bibliográficas, seções, tabelas e figuras devem conter hiperlinks interativos sutis configurados via `hyperref` (`linkcolor=blue!70!black, citecolor=blue!70!black`).

---

## 5. Diretrizes de Visualização Científica e Figuras

### A. Figura 1: Diagnóstico de Causalidade e Convergência (Painel $1 \times 2$)
* **Painel (a) — Convergência das Perdas:**
  * **Título:** `(a) Convergência da função de perda (PINN)`
  * **Eixo $y$:** `MSE` (escala logarítmica $\log_{10}$).
  * **Eixo $x$:** `Épocas`.
  * **Legenda das componentes com $\mathcal{L}$ caligráfico:** $\mathcal{L}_{\mathrm{total}}$, $\mathcal{L}_{\mathrm{pde}, u}$, $\mathcal{L}_{\mathrm{pde}, v}$, $\mathcal{L}_{\mathrm{ic}}$, $\mathcal{L}_{\mathrm{bc}}$.
* **Painel (b) — Evolução Temporal da Heterogeneidade:**
  * **Título:** `(b) Evolução da Heterogeneidade Temporal`
  * **Eixo $x$:** `t (s)`.
  * **Eixo $y$:** $\|u(t) - u^*\|_{L_2} \quad \mathbf{(Amplitude)}$.
  * **Legenda:** estritamente `MDF ADI` e `PINN`.
  * **Anotações:** Setas limpas com caixas de fundo translúcido apontando para:
    1. *Crescimento Exponencial (Modos Instáveis)* no MDF ADI.
    2. *Saturação de Spots (Padrão Estável)* no MDF ADI.
    3. *Colapso Homogêneo (Falha de Padrão)* na PINN.

### B. Figura 2: Confronto Espaço-Temporal Direto ($2 \times 3$)
* **Estrutura:** 2 linhas $\times$ 3 colunas para os instantes $t \in \{0{,}02, \; 0{,}41, \; 2{,}00\}\,\text{s}$.
* **Título Principal:** `MDF ADI x PINN: Campo de Concentração do Ativador u(x,y,t) / [X]`.
* **Identificação das Linhas:**
  * **Linha 1:** `MDF ADI (Pereira, 2019)`
  * **Linha 2:** `PINN (20.000 epochs)`
* **Colormap:** Paleta clássica `jet` do MATLAB com interpolação bicúbica suave.
* **Escala Dinâmica Adaptativa por Instante de Tempo:**
  * Em $t = 0{,}02$\,s: normalizada para evidenciar a perturbação gaussiana pontual em $(1/3, 1/2)$ no MDF ADI e comprovar sua ausência na PINN.
  * Em $t = 0{,}41$\,s: captura da quebra de simetria.
  * Em $t = 2{,}00$\,s: revelação da rede hexagonal completa de spots no MDF ADI versus o campo plano da PINN.
* **Tipografia:** Regular serif sem sobrepeso de negrito artificial e sem símbolos `$` órfãos.

---

## 6. Regra Estrutural de Extensão do Artigo

* **Limite Rígido:** O artigo deve ter **exatamente 5 páginas** (modelo oficial dos Encontros Universitários UFC / Prism).
* Todo o corpo de texto, resumo/abstract, equações, tabelas comparativas, figuras de alta resolução e referências em 2 colunas devem se ajustar harmoniosamente sem transbordar para a página 6.
