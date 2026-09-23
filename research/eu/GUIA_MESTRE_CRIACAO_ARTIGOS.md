# GUIA MESTRE PARA CRIAÇÃO DE ARTIGOS CIENTÍFICOS — ENCONTROS UNIVERSITÁRIOS (UFC)

> **Instrução para a IA/Agente**: Quando o usuário solicitar a criação de um artigo científico para os Encontros Universitários da UFC (ou qualquer resumo expandido de alto nível), leia e siga **RIGOROSAMENTE** todos os passos, padrões matemáticos, visuais, estruturais e de compilação definidos neste documento.

---

## 1. REGRAS FORMAIS E EDITALÍCIAS (Edital n.º 04/2026 - UFC Quixadá)

1. **Limite de Páginas**:
   - **Mínimo**: 3 páginas | **Máximo estrito**: 5 páginas.
   - **Meta de excelência**: O artigo deve preencher **exatamente 5 páginas** de forma equilibrada, sem deixar a 5ª página semipreenchida e **JAMAIS** estourar para a 6ª página.
2. **Avaliação Duplo-Cega (Anonimização Obrigatória)**:
   - Na versão inicial, os nomes de alunos e orientadores **NÃO** podem aparecer.
   - Usar no cabeçalho:
     ```latex
     \author{%
       \textit{Autoria omitida para avaliação duplo-cega}\\[0.2em]
       \small Campus da Universidade Federal do Ceará em Quixadá
     }
     ```
   - Em legendas de figuras e tabelas, utilizar: `Fonte: Elaboração própria (versão identificada).`
3. **Metadados Obrigatórios (Resumo + Abstract)**:
   - **Português**: `\qabstract{Resumo}{Palavras-chave}{ODS}{Texto...}{palavras; chave...}{indústria, inovação e infraestrutura}`
   - **Inglês**: `\qabstract{Abstract}{Keywords}{SDG}{Text...}{keywords; here...}{industry, innovation and infrastructure}`
4. **Normas de Formatação**:
   - Pacote obrigatório: `\usepackage{estilo}` (reprodução oficial do Prism/UFC Quixadá).
   - Conformidade ABNT NBR 6022:2018 (artigo impresso) e ABNT NBR 6023:2018 (referências).

---

## 2. ESTRUTURAÇÃO DO TEXTO E RIGOR CIENTÍFICO

O texto deve ter densidade científica de padrão internacional (estilo *Journal of Computational Physics* / *Nature Reviews Physics* adaptado para PT-BR).

### Estrutura das Seções:
1. **1 INTRODUÇÃO**:
   - Contextualização do fenômeno físico e das EDPs que o modelam.
   - Discussão sobre os métodos numéricos clássicos de malha (Diferenças Finitas - MDF, Elementos Finitos - MEF, Volumes Finitos - MVF), destacando suas limitações (geração de malhas em geometrias complexas, erro de escadeamento/*staircasing*, custo computacional).
   - **Citação da Tese do Orientador** (`pereira2019`) como fundamentação clássica de MDF para difusão/reação e EDPs não-lineares.
   - Introdução às *Physics-Informed Neural Networks* (PINNs) de Raissi et al. (2019) e o paradigma livre de malha (*meshless*).
   - Delimitação clara do escopo e das contribuições do artigo.

2. **2 DESENVOLVIMENTO**:
   - **2.1 Fundamentação Teórica**:
     - Formulação matemática completa das EDPs tratadas, com condições de contorno (Dirichlet/Neumann) e iniciais explícitas.
     - Solução analítica exata (se houver, ex: Série de Fourier) com todos os termos e coeficientes.
     - **Arquitetura Neural Explícita**: Formalização da propagação camada a camada:
       $$\mathbf{h}^{(0)} = \mathbf{z}, \quad \mathbf{h}^{(\ell)} = \sigma(\mathbf{W}^{(\ell)}\mathbf{h}^{(\ell-1)} + \mathbf{b}^{(\ell)}), \quad \mathbf{u}_\theta(\mathbf{z}) = \mathbf{W}^{(L+1)}\mathbf{h}^{(L)} + \mathbf{b}^{(L+1)}$$
       com ativação suave $\sigma(s) = \tanh(s) \in C^\infty(\mathbb{R})$ para assegurar derivadas contínuas de ordem arbitrária.
     - **Diferenciação Automática (Autograd)**: Equações exatas para derivadas espaciais e temporais via modo reverso (*Vector-Jacobian Products*, VJP), destacando a ausência de erro de truncamento de malha ($\mathcal{O}(\Delta x^2)$).
     - **Função de Perda Multiobjetivo (MSE)** detalhada:
       $$\mathcal{L}(\theta) = \mathcal{L}_{\mathrm{pde}}(\theta) + \lambda_{\mathrm{ic}}\mathcal{L}_{\mathrm{ic}}(\theta) + \lambda_{\mathrm{bc}}\mathcal{L}_{\mathrm{bc}}(\theta)$$
       com as somas quadráticas médias explícitas sobre os pontos de colocação $N_f$, fronteira $N_b$ e iniciais $N_0$.
   - **2.2 Metodologia**:
     - **Tabela de Hiperparâmetros**: Camadas, neurônios, ativação, otimizador (Adam, taxa $\eta$), épocas, número de pontos de colocação ($N_f, N_b, N_0$), parâmetros físicos ($\alpha, \nu, D_u, D_v, \dots$).
     - Descrição do domínio espaço-temporal $\Omega \times [0, T]$ e do esquema de amostragem.
   - **2.3 Resultados e Discussão**:
     - **Convergência das Perdas**: Análise detalhada das curvas de perda (PDE, BC, IC, Total).
     - **Validação Física / Analítica**: Comparação quantitativa ponto a ponto com solução analítica ou numérica de referência (erro absoluto $|u_\theta - u^\star|$, erro relativo $\mathcal{L}_2$).
     - **Comportamento Espaçotemporal**: Descrição da evolução dos campos 2D/3D, isotermas, perfis de velocidade ou formação de padrões.
     - **Tabela Comparativa de Desempenho**: Épocas, perdas finais por componente, erros absolutos, tipos de condição de contorno.

3. **3 CONSIDERAÇÕES FINAIS**:
   - Síntese dos resultados quantitativos obtidos.
   - Confronto das vantagens da PINN (representação contínua avaliável em $\mathcal{O}(\text{ms})$, formulação unificada, sem malha) versus métodos clássicos.
   - Limitações reais identificadas (ex: *spectral bias* de MLPs em gradientes abruptos, tempo de treinamento inicial).
   - Trabalhos futuros claros e realizáveis.

4. **REFERÊNCIAS**:
   - **Poucas e de alto impacto (3 a 7 referências no máximo)**.
   - Disposição contínua em formato compacto (`\small` ou `\scriptsize`) para não transbordar páginas.
   - **Obrigatório incluir**:
     1. Tese do Orientador (`pereira2019`): *Métodos de Diferenças Finitas para Problemas de Difusão e Reação Não Lineares* (LNCC, 2019).
     2. Raissi et al. (2019): *Physics-informed neural networks* (JCP).
     3. Artigo clássico da equação tratada (ex: Burgers 1948, Turing 1952, Schnakenberg 1979, Peaceman & Rachford 1955).
   - **NÃO inflar a bibliografia** com citações de bibliotecas genéricas (PyTorch, Adam, etc.) — esses termos devem ser apenas mencionados no texto.

---

## 3. PADRÃO VISUAL E GERAÇÃO DE FIGURAS (gen_figures.py)

Para gerar artigos visualmente impressionantes e científicos:

1. **Configuração Padrão do Matplotlib (`gen_figures.py`)**:
   ```python
   import matplotlib
   matplotlib.use('Agg')
   import matplotlib.pyplot as plt
   
   plt.rcParams.update({
       'font.family':        'serif',
       'font.serif':         ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
       'font.size':          8.5,
       'axes.labelsize':     8.5,
       'axes.titlesize':     9.0,
       'xtick.labelsize':    7.5,
       'ytick.labelsize':    7.5,
       'figure.dpi':         300,
       'savefig.dpi':        300,
       'savefig.bbox':       'tight',
       'savefig.pad_inches': 0.03,
   })
   ```
2. **Figuras Obrigatórias por Artigo**:
   - **Figura 1**: Arquitetura da Rede e Fluxo PINN (MLP profunda + Autograd + Perdas).
   - **Figura 2**: Curvas de Convergência Semilogarítmica ($\log_{10} \mathcal{L}$ por época).
   - **Figura 3**: Resultados do Problema 1 (ex: Superfícies 3D temporais da temperatura $u(x,y,t)$ ou validação analítica com mapa de erros).
   - **Figura 4**: Resultados do Problema 2 (ex: Superfícies 3D + magnitude do campo de velocidade $\|\mathbf{u}\|$ ou evolução de padrões de Turing).
3. **Formatos de Saída**:
   - Salvar sempre em `.pdf` (vetorial para inclusão no LaTeX) e `.png` (para pré-visualização).

---

## 4. FLUXO DE EXECUÇÃO ITERATIVO PARA O AGENTE (Passo a Passo)

Quando solicitado a redigir um novo artigo:

1. **Investigação do Repositório de Código**:
   - Localizar os arquivos de dados, códigos PyTorch e figuras geradas no repositório base (ex: `/home/warley/development/projects/pinns/...`).
   - Identificar equações exatas, condições iniciais/contorno, parâmetros ($\alpha, \nu, a, b, d$), épocas e perdas finais.

2. **Geração e Curadoria das Figuras**:
   - Criar ou ajustar `gen_figures.py` na pasta do artigo.
   - Executar `python3 gen_figures.py` e gerar os PDFs em `figures/`.

3. **Redação do Manuscrito (`paper_*.tex`)**:
   - Utilizar a classe `article` com `\usepackage{estilo}`.
   - Ajustar a geometria e espaçamento para garantir encaixe perfeito em 5 páginas:
     ```latex
     \geometry{
       a4paper,
       left   = 1.9cm, right = 1.9cm,
       top    = 1.5cm, bottom = 1.5cm,
       headheight = 14.5pt
     }
     \setstretch{1.0}
     \setlength{\parindent}{0.7cm}
     \setlength{\abovedisplayskip}{3pt plus 1pt minus 1pt}
     \setlength{\belowdisplayskip}{3pt plus 1pt minus 1pt}
     ```

4. **Compilação e Auditoria de Páginas**:
   - Executar ciclo de compilação:
     ```bash
     pdflatex -interaction=nonstopmode paper_*.tex
     biber paper_*
     pdflatex -interaction=nonstopmode paper_*.tex
     pdflatex -interaction=nonstopmode paper_*.tex
     ```
   - **Verificar com Python (`pypdf`)**:
     ```python
     import pypdf
     r = pypdf.PdfReader('paper_*.pdf')
     print(f"Total de páginas: {len(r.pages)}")
     ```
   - Se resultar em 6 páginas: encolher ligeiramente o texto de conclusões/metodologia ou reduzir `\bibitemsep` e tamanho das figuras até bater **exatamente 5 páginas**.
   - Se resultar em 4 páginas: expandir a fundamentação matemática, adicionar detalhes da arquitetura neural ou detalhar a discussão dos resultados.

---

## 5. TEMPLATE BIBLIOGRÁFICO BASE (`referencias.bib`)

```bibtex
@phdthesis{pereira2019,
  author  = {Pereira, Ricardo Reis},
  title   = {M{\'e}todos de Diferen{\c{c}}as Finitas para Problemas de Difus{\~a}o e Rea{\c{c}}{\~a}o N{\~a}o Lineares},
  school  = {Laborat{\'o}rio Nacional de Computa{\c{c}}{\~a}o Cient{\'\i}fica (LNCC)},
  year    = {2019},
  address = {Petr{\'o}polis, RJ}
}

@article{raissi2019pinns,
  author    = {Raissi, Maziar and Perdikaris, Paris and Karniadakis, George Em},
  title     = {Physics-informed neural networks: {A} deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations},
  journal   = {Journal of Computational Physics},
  year      = {2019},
  volume    = {378},
  pages     = {686--707},
  doi       = {10.1016/j.jcp.2018.10.045}
}

@article{burgers1948model,
  author    = {Burgers, Johannes Martinus},
  title     = {A mathematical model illustrating the theory of turbulence},
  journal   = {Advances in Applied Mechanics},
  year      = {1948},
  volume    = {1},
  pages     = {171--199}
}

@article{turing1952chemical,
  author    = {Turing, Alan Mathison},
  title     = {The chemical basis of morphogenesis},
  journal   = {Philosophical Transactions of the Royal Society of London. Series B},
  year      = {1952},
  volume    = {237},
  number    = {641},
  pages     = {37--72}
}

@article{schnakenberg1979simple,
  author    = {Schnakenberg, J{\"u}rgen},
  title     = {Simple chemical reaction systems with limit cycle behaviour},
  journal   = {Journal of Theoretical Biology},
  year      = {1979},
  volume    = {81},
  number    = {3},
  pages     = {389--400}
}
```
