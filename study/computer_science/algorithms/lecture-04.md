---
tags:
  - study/algorithms
  - complexity-analysis
  - asymptotic-notation
aliases:
  - Asymptotic Analysis of Basic Summations
  - Summations in Basic Form Theta Simplification
pdf: "[[ufc/4s/algorithms_analysis_project/slides/04.pdf]]"
---

# Asymptotic Analysis: $\Theta$-Simplification of Summations in Basic Form

## 1. Mathematical Framework & The Basic Form

When analyzing the time complexity of iterative algorithms, the exact count of primitive operations across nested loops reduces to finite summations:

$$
T(n) = \sum_{i=c_0}^{n + c_1} f(i)
$$

where $c_0, c_1 \in \mathbb{Z}$ are constants independent of $n$.

### Definition: General Basic Form
We characterize the summand $f(i): \mathbb{N} \to \mathbb{R}^+$ by its canonical mixed asymptotic structure:

$$
f(i) \in \Theta\left( b^i \cdot i^d \cdot \log^e i \right)
$$

with parameters:
- **Exponential base:** $b \ge 1$
- **Polynomial degree:** $d \in \mathbb{R}$
- **Logarithmic degree:** $e \in \mathbb{R}$

The asymptotic classification of $\sum_{i=c_0}^n f(i)$ dichotomizes strictly based on whether the growth is driven by the exponential engine ($b > 1$) or the polynomial/integral engine ($b = 1$).

---

## 2. Geometric Summations ($b > 1$)

### 2.1 Theorem (Geometric Dominance)
Let $f(i) \in \Theta(b^i \cdot i^d \cdot \log^e i)$ with base $b > 1$. Then:

$$
\sum_{i=c_0}^{n+c_1} f(i) \in \Theta(f(n)) = \Theta\left( b^n \cdot n^d \cdot \log^e n \right)
$$

### 2.2 Mathematical Proof / Derivation

#### Pure Geometric Backbone
Consider first the case $d = 0, e = 0$. The exact sum of a geometric progression with ratio $b > 1$ is:

$$
S(n) = \sum_{i=0}^n b^i = \frac{b^{n+1} - 1}{b - 1} = \left(\frac{b}{b-1}\right) b^n - \frac{1}{b-1}
$$

Since $b > 1$ is a constant, $C = \frac{b}{b-1} > 0$ is a constant factor:

$$
\lim_{n \to \infty} \frac{S(n)}{b^n} = \lim_{n \to \infty} \left( \frac{b}{b-1} - \frac{1}{(b-1)b^n} \right) = \frac{b}{b-1} = \Theta(1)
$$

Thus, $\sum_{i=0}^n b^i \in \Theta(b^n)$.

#### Inclusion of Polynomial & Logarithmic Factors
For $f(i) = b^i \cdot g(i)$, where $g(i) = i^d \log^e i$ is polynomially bounded:

1. **Lower Bound ($\Omega$):**
   The sum of positive terms is trivially bounded below by its largest single term (the last term $i = n$):
   $$
   \sum_{i=c_0}^n f(i) \ge f(n) \implies \sum_{i=c_0}^n f(i) \in \Omega(f(n))
   $$

2. **Upper Bound ($\mathcal{O}$):**
   Rewrite the sum reversing the index $k = n - i$:
   $$
   \sum_{i=c_0}^n b^i g(i) = b^n g(n) \sum_{k=0}^{n-c_0} b^{-k} \frac{g(n-k)}{g(n)}
   $$
   Since $g(x) = x^d \log^e x$ is monotonically increasing for sufficiently large $x$, $\frac{g(n-k)}{g(n)} \le 1$ for all $k \ge 0$. Therefore:
   $$
   \sum_{i=c_0}^n b^i g(i) \le b^n g(n) \sum_{k=0}^{\infty} \left(\frac{1}{b}\right)^k = b^n g(n) \left(\frac{b}{b-1}\right) = \mathcal{O}(f(n))
   $$

Combining both bounds:

$$
\Omega(f(n)) \cap \mathcal{O}(f(n)) \implies \Theta(f(n))
$$

---

## 3. Arithmetic & Polynomial Summations ($b = 1, d > -1$)

### 3.1 Theorem (Integral Accumulation)
Let $f(i) \in \Theta(i^d \cdot \log^e i)$ with $b = 1$ and $d > -1$. Then:

$$
\sum_{i=c_0}^{n+c_1} f(i) \in \Theta(n \cdot f(n)) = \Theta\left( n^{d+1} \cdot \log^e n \right)
$$

### 3.2 Mathematical Proof via Integral Bounding

Let $g(x) = x^d \ln^e x$. For $d > -1$ and large $x$, $g(x)$ is positive and monotonically increasing. By the integral bounding theorem for monotonically increasing functions:

$$
\int_{c_0}^n g(x) \, dx \le \sum_{i=c_0}^n g(i) \le \int_{c_0}^{n+1} g(x) \, dx
$$

Evaluating the indefinite integral using integration by parts:

$$
\int x^d \ln^e x \, dx = \frac{x^{d+1} \ln^e x}{d+1} - \frac{e}{d+1} \int x^d \ln^{e-1} x \, dx
$$

Iterating this recurrence yields:

$$
\int_1^n x^d \ln^e x \, dx = \frac{n^{d+1} \ln^e n}{d+1} - \mathcal{O}\left( n^{d+1} \ln^{e-1} n \right) = \frac{1}{d+1} n^{d+1} \ln^e n + o\left( n^{d+1} \ln^e n \right)
$$

Taking the limit ratio as $n \to \infty$:

$$
\lim_{n \to \infty} \frac{\sum_{i=c_0}^n i^d \log^e i}{n^{d+1} \log^e n} = \frac{1}{d+1} \in (0, \infty)
$$

Therefore:

$$
\sum_{i=c_0}^n i^d \log^e i \in \Theta\left( n^{d+1} \log^e n \right)
$$

> **Crucial Insight:** The exponent $d$ shifts to $d+1$ because integration increases the polynomial dimension by 1 ($\int x^d = \frac{x^{d+1}}{d+1}$). The logarithmic power $e$ remains completely unchanged.

---

## 4. Special Boundary Case: $d = -1$ (Harmonic Divergence)

When $b = 1$ and $d = -1$:
- For $e = 0$: $f(i) = \frac{1}{i}$, giving the classic Harmonic series:
  $$
  \sum_{i=1}^n \frac{1}{i} = \ln n + \gamma + \mathcal{O}\left(\frac{1}{n}\right) \in \Theta(\log n)
  $$
- For general $e \ne -1$:
  $$
  \sum_{i=2}^n \frac{1}{i \ln^{-e} i} \approx \int_2^n \frac{(\ln x)^e}{x} \, dx = \frac{\ln^{e+1} n}{e+1} \in \Theta\left( \log^{e+1} n \right)
  $$

---

## 5. Summary Reference Table

| Classification | Parameter Constraint | Summand $f(i)$ | Summation Complexity $\Theta\left(\sum_{i=1}^n f(i)\right)$ |
| :--- | :--- | :--- | :--- |
| **Geometric** | $b > 1, \forall d, e$ | $b^i \cdot i^d \cdot \log^e i$ | $\Theta(f(n)) = \Theta(b^n \cdot n^d \cdot \log^e n)$ |
| **Polynomial / Arithmetic** | $b = 1, d > -1, \forall e$ | $i^d \cdot \log^e i$ | $\Theta(n \cdot f(n)) = \Theta(n^{d+1} \cdot \log^e n)$ |
| **Harmonic Critical** | $b = 1, d = -1, e = 0$ | $i^{-1}$ | $\Theta(\log n)$ |

---

## 6. Analysis of Nested Summations & Index Dependencies

### 6.1 Principles of Nested Loop Reduction
1. **Inside-Out Evaluation:** Always compute the innermost summation first, treating outer loop indices as independent parameters for the inner scope.
2. **Distinguishing Indices from Problem Parameters:**
   - Indices of outer loops ($i, j$) vary with execution and **cannot** be factored out of their parent summations.
   - Input problem dimensions ($m, n$) are invariant with respect to loop iterations and act as global parameters.
3. **Index Reversal Substitution:**
   For terms of the form $(n - i)^d$ summing over $i \in [0, n-1]$:
   $$
   u = n - i \implies \sum_{i=0}^{n-1} (n - i)^d = \sum_{u=1}^n u^d \in \Theta(n^{d+1})
   $$

---

## 7. Step-by-Step Rigorous Solutions ($S_1$ to $S_9$)

### $S_1 = \sum_{i=1}^n 3^i \cdot i^2$
- **Parameters:** $b = 3 > 1$, $d = 2$, $e = 0$.
- **Type:** Geometric.
- **Rule:** Dominated by the final term $f(n)$.
- **Result:**
  $$
  S_1 \in \Theta(3^n \cdot n^2)
  $$

---

### $S_2 = \sum_{i=1}^n i^3 \log_2^2 i$
- **Parameters:** $b = 1$, $d = 3 > -1$, $e = 2$.
- **Type:** Polynomial/Arithmetic.
- **Rule:** $d \to d + 1 = 4$, logarithmic factor $\log_2^2 n$ is preserved.
- **Result:**
  $$
  S_2 \in \Theta(n^4 \log_2^2 n)
  $$

---

### $S_3 = \sum_{i=0}^{n-1} \sum_{j=0}^{m-1} j$
- **Inner Sum:** $\sum_{j=0}^{m-1} j \in \Theta(m^2)$ (arithmetic in $j$).
- **Outer Sum:** Since $\Theta(m^2)$ is independent of $i$:
  $$
  \sum_{i=0}^{n-1} \Theta(m^2) = \Theta(m^2) \sum_{i=0}^{n-1} 1 = \Theta(n \cdot m^2)
  $$
- **Result:**
  $$
  S_3 \in \Theta(n \cdot m^2)
  $$

---

### $S_4 = \sum_{i=1}^n \sum_{j=1}^i 2^j$
- **Inner Sum:** $\sum_{j=1}^i 2^j \in \Theta(2^i)$ (geometric sum in $j$, upper limit $i$).
- **Outer Sum:** $\sum_{i=1}^n \Theta(2^i)$ is **itself a geometric sum** in $i$ with base $b = 2 > 1$.
  $$
  \sum_{i=1}^n 2^i \in \Theta(2^n)
  $$
- **Result:**
  $$
  S_4 \in \Theta(2^n)
  $$

---

### $S_5 = \sum_{i=0}^{n-1} (n - i)^3$
- **Substitution:** Let $u = n - i$. As $i$ goes from $0$ to $n-1$, $u$ ranges from $n$ down to $1$.
  $$
  S_5 = \sum_{u=1}^n u^3
  $$
- **Type:** Arithmetic with $b = 1, d = 3 \implies d \to 4$.
- **Result:**
  $$
  S_5 \in \Theta(n^4)
  $$

---

### $S_6 = \sum_{i=1}^n \sum_{j=1}^i (j \log j)$
- **Inner Sum:** $b = 1, d = 1, e = 1 \implies \Theta(i^2 \log i)$.
- **Outer Sum:** $\sum_{i=1}^n \Theta(i^2 \log i)$ has $b = 1, d = 2, e = 1 \implies d \to 3$.
- **Result:**
  $$
  S_6 \in \Theta(n^3 \log n)
  $$

---

### $S_7 = \sum_{i=0}^{n-1} \sum_{j=0}^i \sum_{k=0}^j 1$
- **Innermost ($k$):** $\sum_{k=0}^j 1 = j + 1 \in \Theta(j^1)$ ($d = 0 \to 1$).
- **Middle ($j$):** $\sum_{j=0}^i \Theta(j^1) \in \Theta(i^2)$ ($d = 1 \to 2$).
- **Outer ($i$):** $\sum_{i=0}^{n-1} \Theta(i^2) \in \Theta(n^3)$ ($d = 2 \to 3$).
- **Result:**
  $$
  S_7 \in \Theta(n^3)
  $$

---

### $S_8 = \sum_{i=1}^n \sum_{j=1}^i \sum_{k=1}^j 2^k$
- **Innermost ($k$):** $\sum_{k=1}^j 2^k \in \Theta(2^j)$ (geometric).
- **Middle ($j$):** $\sum_{j=1}^i \Theta(2^j) \in \Theta(2^i)$ (geometric).
- **Outer ($i$):** $\sum_{i=1}^n \Theta(2^i) \in \Theta(2^n)$ (geometric).
- **Result:**
  $$
  S_8 \in \Theta(2^n)
  $$

---

### $S_9 = \sum_{i=1}^n \sum_{j=1}^n \sum_{k=1}^n 2^k$
- **Innermost ($k$):** $\sum_{k=1}^n 2^k \in \Theta(2^n)$ (upper limit is invariant $n$).
- **Middle ($j$):** $\sum_{j=1}^n \Theta(2^n) = \Theta(2^n) \sum_{j=1}^n 1 = \Theta(n \cdot 2^n)$.
- **Outer ($i$):** $\sum_{i=1}^n \Theta(n \cdot 2^n) = \Theta(n \cdot 2^n) \sum_{i=1}^n 1 = \Theta(n^2 \cdot 2^n)$.
- **Result:**
  $$
  S_9 \in \Theta(n^2 \cdot 2^n)
  $$

---

# #flashcards/algorithms/asymptotic-analysis

What is the general asymptotic order $\Theta$ of $\sum_{i=1}^n (b^i \cdot i^d \cdot \log^e i)$ when $b > 1$?
?
$\Theta(b^n \cdot n^d \cdot \log^e n)$, which is simply $\Theta(f(n))$ (the order of the last term evaluated at $n$).
<!--SR:!2026-08-29,4,270-->

---

Why does an arithmetic summation $\sum_{i=1}^n i^d \log^e i$ with $d > -1$ result in $\Theta(n^{d+1} \log^e n)$ instead of incrementing the log exponent?
?
By the integral approximation $\int_1^n x^d \ln^e x \, dx$, integration by parts yields $\frac{n^{d+1}\ln^e n}{d+1} - \mathcal{O}(n^{d+1}\ln^{e-1} n)$. The leading term has polynomial degree $d+1$ while keeping the logarithmic exponent $e$ identical.
<!--SR:!2026-08-29,4,270-->

---

Why does nesting $k$ dependent geometric summations $\sum_{i_k=1}^n \cdots \sum_{i_1=1}^{i_2} 2^{i_1}$ evaluate to $\Theta(2^n)$ rather than $\Theta(n^k 2^n)$?
?
Because each geometric layer $\sum_{j=1}^i 2^j = 2^{i+1} - 2 = \Theta(2^i)$ outputs an exponential term in the next index. Each subsequent layer is itself a geometric summation dominated strictly by its own last term, never accumulating an extra polynomial factor of $n$.

---

What is the asymptotic complexity of the reversed arithmetic sum $\sum_{i=0}^{n-1} (n - i)^d$ for constant integer $d \ge 0$?
?
$\Theta(n^{d+1})$. By the change of variable $u = n - i$, the sum expands to $\sum_{u=1}^n u^d$, which is a standard arithmetic sum with degree $d \to d+1$.

---

In nested loop analysis, what is the critical difference between $S_A = \sum_{i=1}^n \sum_{j=1}^i 2^j$ and $S_B = \sum_{i=1}^n \sum_{j=1}^n 2^j$?
?
In $S_A$, the inner upper bound is $i$, making the inner sum $\Theta(2^i)$ dependent on $i$, so the outer sum is geometric: $\sum_{i=1}^n \Theta(2^i) = \Theta(2^n)$.
In $S_B$, the inner upper bound is $n$, making the inner sum $\Theta(2^n)$ independent of $i$, so the outer sum is constant multiplication: $\sum_{i=1}^n \Theta(2^n) = \Theta(n \cdot 2^n)$.
<!--SR:!2026-08-29,4,270-->

---

For the critical boundary condition $b = 1, d = -1, e = 0$, what does the summation $\sum_{i=1}^n \frac{1}{i}$ evaluate to asymptotically?
?
$\Theta(\log n)$ (the Harmonic series divergence, since $\int_1^n \frac{1}{x}\,dx = \ln n$).
<!--SR:!2026-08-29,4,270-->

---

The summation $\sum_{i=1}^n (3^i \cdot i^2)$ evaluates to ==$\Theta(3^n \cdot n^2)$== because the exponential base $b = 3 > 1$ dominates.
<!--SR:!2026-08-29,4,270-->

---

The summation $\sum_{i=1}^n (i^3 \log_2^2 i)$ evaluates to ==$\Theta(n^4 \log_2^2 n)$== because $b = 1$ and $d = 3 \to d+1 = 4$.
<!--SR:!2026-08-29,4,270-->

---

The 3-level dependent summation $\sum_{i=0}^{n-1} \sum_{j=0}^i \sum_{k=0}^j 1$ evaluates to ==$\Theta(n^3)$== because each dependent arithmetic layer raises the polynomial degree by 1 ($0 \to 1 \to 2 \to 3$).
<!--SR:!2026-08-29,4,270-->
