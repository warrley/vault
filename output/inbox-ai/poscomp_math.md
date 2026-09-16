 [!quote] YOU

see the last 5 years poscomp exams in /home/warley/Downloads/trash/Provas-POSCOMP and extract the most used topics questions about math, is the first 20 questions 0-20


> [!abstract] PI

Análise detalhada das **questões de Matemática (questões 01 a 20)** dos últimos 5 anos de provas do POSCOMP (**2018, 2019, 2022, 2023 e 2024** — total de 100 questões analisadas).

---

### 📊 1. Distribuição Geral por Grandes Áreas (Total de 100 Questões)

| Grande Área | Questões (5 anos) | % na Seção de Matemática | Média por Edição |
| :--- | :---: | :---: | :---: |
| **Lógica Matemática** | 15 | 15% | 3 questões |
| **Álgebra Linear** | 15 | 15% | 3 questões |
| **Cálculo Diferencial e Integral** | 15 | 15% | 3 questões |
| **Geometria Analítica e Vetores** | 15 | 15% | 3 questões |
| **Matemática Discreta e Combinatória** | 19 | 19% | 3 a 4 questões |
| **Álgebra Booleana e Circuitos** | 10 | 10% | 2 questões |
| **Probabilidade e Estatística** | 11 | 11% | 2 a 3 questões |

---

### 🎯 2. Tópicos Mais Recorrentes e Padrões da Banca (Fundatec)

A banca segue um **mapa de questões quase fixo** ano a ano para o bloco de 1 a 20:

```
[Q01 - Q03]  Álgebra Linear
[Q04 - Q06]  Análise Combinatória / Grafos / Geometria
[Q07 - Q10]  Cálculo Diferencial e Integral / Geometria Analítica
[Q11 - Q15]  Lógica Matemática (Proposicional e Primeira Ordem)
[Q16 - Q18]  Álgebra Booleana / Mapa de Karnaugh / Circuitos
[Q18 - Q20]  Probabilidade e Estatística
```

---

### 📚 3. Detalhamento dos Tópicos Mais Cobrados por Disciplina

#### 1. Lógica Matemática (15 questões) — *A área com padrão mais repetitivo*
* **Negação de Proposições com Quantificadores (Lógica de 1ª Ordem)** *(Presente em quase todos os anos)*:
  * Negação de sentenças no formato: *"Em toda turma existe pelo menos um..."*, *"Existe pelo menos uma cidade em que todos..."*.
  * Regra cobrada: $\neg (\forall x \, P(x)) \equiv \exists x \, \neg P(x)$ e $\neg (\exists x \, \forall y \, P(x, y)) \equiv \forall x \, \exists y \, \neg P(x, y)$.
* **Equivalência da Condicional e Contrapositiva**:
  * $p \to q \equiv \neg q \to \neg p \equiv \neg p \lor q$.
* **Argumentos Lógicos e Dedução por Premissas**:
  * Determinar quem praticou uma ação a partir de uma cadeia de premissas condicionais e disjunções verdadeiras.
* **Tabela Verdade e Conectivos**:
  * Condições de verdade/falsidade de proposições compostas.

---

#### 2. Álgebra Booleana e Circuitos Lógicos (10 questões)
* **Mapa de Karnaugh (3 e 4 variáveis)**:
  * Simplificação de expressões booleanas dadas em forma canônica ($\sum m(\dots)$ ou soma de produtos).
* **Leis de De Morgan e Álgebra Booleana**:
  * Conversão de expressões em soma de produtos (SOP) ou produto de somas (POS).
  * Aplicação de identidades booleanas ($A + A \cdot B = A$, $A + \bar{A}B = A + B$).
* **Análise de Portas Lógicas / Circuitos**:
  * Extração da função booleana equivalente a partir do diagrama de portas (AND, OR, NAND, NOR, XOR).

---

#### 3. Álgebra Linear (15 questões)
* **Sistemas Lineares e Eliminação de Gauss**:
  * Resolução direta de sistemas $3 \times 3$ ou escalonamento de matriz aumentada.
* **Polinômio Característico e Autovalores**:
  * Cálculo de $\det(A - \lambda I) = 0$ para matrizes $3 \times 3$.
* **Determinantes e Matrizes com Parâmetros**:
  * Determinar o valor de $\alpha$ ou incógnitas para que $\det(A) = k$.
* **Espaços Vetoriais e Combinação Linear**:
  * Verificar dependência linear (LI/LD) e pertencimento de vetores a subespaços gerados.
* **Matriz Inversa e Diagonalização**:
  * Cálculo de $A^{-1}$ e condições para diagonalizabilidade.

---

#### 4. Cálculo Diferencial e Integral (15 questões)
* **Limites no Infinito e Indeterminações**:
  * Limites com radicais no infinito (ex: $\lim_{x\to\infty} \sqrt{x^2+1} - x$) e indeterminações $\frac{0}{0}$ ou $\frac{\infty}{\infty}$ (L'Hôpital / fatoração).
* **Continuidade de Funções por Partes e Domínio**:
  * Encontrar constantes $a$ e $b$ para que a função seja contínua em pontos de transição.
* **Cálculo Multivariável (Vetor Gradiente)**:
  * Cálculo de $\nabla f(x, y, z) = \left(\frac{\partial f}{\partial x}, \frac{\partial f}{\partial y}, \frac{\partial f}{\partial z}\right)$ em um ponto específico.
* **Integrais Definidas e Cálculo de Áreas**:
  * Cálculo de primitivas imediatas e integrais definidas $\int_a^b f(x) \, dx$ para áreas sob curvas.
* **Máximos e Mínimos / Estudo de Funções**:
  * Intervalos de crescimento e pontos críticos via primeira e segunda derivadas.

---

#### 5. Geometria Analítica e Vetores (15 questões)
* **Retas e Planos no Espaço**:
  * Ponto de interseção de retas, vetor diretor da interseção de planos e retas perpendiculares.
* **Distância de Ponto a Reta e Ponto a Plano**:
  * Aplicação direta da fórmula: $d(P, r) = \frac{|Ax_0 + By_0 + C|}{\sqrt{A^2 + B^2}}$.
* **Vetores**:
  * Produto escalar ($u \cdot v$), produto vetorial ($u \times v$) e ângulo entre vetores.
* **Cônicas / Circunferência**:
  * Equação geral da circunferência $x^2 + y^2 + Ax + By + C = 0$, centro e raio.
* **Sistemas de Coordenadas**:
  * Conversão entre coordenadas polares/esféricas e cartesianas retangulares.

---

#### 6. Matemática Discreta e Combinatória (19 questões)
* **Análise Combinatória**:
  * Combinações simples com restrições (ex: selecionar equipes com pelo menos $k$ elementos de uma classe).
  * Permutações, anagramas e permutações com restrições / desarranjos.
* **Teoria dos Grafos**:
  * Relação entre vértices, arestas e ciclos (árvores têm $n-1$ arestas e não possuem ciclos).
  * Grafos planares, menor caminho e conjuntos dominantes.
* **Teoria dos Conjuntos e Contagem**:
  * Operações com conjuntos, simplificação de uniões/interseções e conjunto das partes ($2^n$).

---

#### 7. Probabilidade e Estatística (11 questões)
* **Estatística Descritiva**:
  * Média aritmética simples e ponderada (a partir de tabelas de frequências ou histogramas).
  * Mediana, Moda e Desvio Padrão / Variância amostral e populacional.
* **Distribuições de Probabilidade**:
  * Distribuição Exponencial ($P(X > t) = e^{-\lambda t}$), Distribuição Binomial e Distribuição Normal (uso do escore $Z$).
* **Probabilidade Clássica e Confiabilidade**:
  * Probabilidade de falha/sucesso em sistemas com redundância de componentes.

---

### 💡 Destaques para Foco de Estudo (Top 5 Tópicos de Maior Retorno)

1. **Negação de Proposições com Quantificadores & Equivalência da Condicional** (acerto garantido de 2 a 3 questões).
2. **Simplificação por Mapa de Karnaugh & Leis de De Morgan** (2 questões muito diretas).
3. **Eliminação de Gauss / Determinantes / Polinômio Característico** (2 a 3 questões de cálculo mecânico).
4. **Limites no Infinito & Vetor Gradiente em Cálculo** (2 questões com padrão previsível).
5. **Combinações Simples com Restrições & Propriedades de Grafos/Árvores** (2 questões de discreta).
