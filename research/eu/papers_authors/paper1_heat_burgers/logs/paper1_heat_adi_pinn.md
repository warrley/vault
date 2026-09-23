# Paper 1: Redes Neurais Informadas por Física (PINNs) versus Métodos de Diferenças Finitas (ADI) na Solução da Equação do Calor 2D em Domínios Irregulares

> **Localização dos arquivos:**  
> - PDF Final: `./research/eu/drafts/paper1_heat_adi_pinn.pdf` (**5 páginas**, modelo padrão UFC Quixadá)  
> - LaTeX: `./research/eu/drafts/paper1_heat_adi_pinn.tex`  
> - Figuras: `./research/eu/drafts/figures/` (`geometry_domain_holes.png`, `mlp_and_pinn_architecture.png`, `adi_regular_benchmark.png`, `fig_cell_12_1.png`, `slice_y030.png`, `loss_convergence.png`)

---

## 1. Esclarecimento do Domínio e Notação Matemática ($\Omega \times (0, T]$)

1. **O que é $\Omega$ (Domínio Espacial em $x$ e $y$):**
   - $\Omega \subset \mathbb{R}^2$ representa a área geométrica ocupada pelo sólido no plano $xy$:
     $$\Omega = \left\{ (x, y) \in [0, 1]^2 \;\middle|\; (x - x_k)^2 + (y - y_k)^2 > r_k^2, \; \forall k \in \{1, 2, 3\} \right\}$$
   - É o quadrado unitário $[0, 1] \times [0, 1]$ subtraído dos três furos circulares $\mathcal{H}_1, \mathcal{H}_2, \mathcal{H}_3$.
2. **O que é $(0, T]$ (Domínio Temporal em $t$):**
   - Intervalo contínuo de tempo em que a difusão ocorre, partindo do repouso $t=0$ até $T_{\text{max}} = 1{,}0$.
3. **O que significa $\Omega \times (0, T]$ (Cilindro Espaço-Temporal):**
   - Significa que a equação do calor $\frac{\partial u}{\partial t} = \alpha \nabla^2 u$ precisa ser satisfeita para **cada ponto $(x,y)$ dentro da chapa sólida $\Omega$ em todo instante de tempo $t$**.

---

## 2. A Física do Problema com os 3 Furos Circulares
- **Dimensões e Centros dos Furos:**
  - $\mathcal{H}_1 = (0{,}30;\, 0{,}30)$ com raio $r_1 = 0{,}12$
  - $\mathcal{H}_2 = (0{,}70;\, 0{,}30)$ com raio $r_2 = 0{,}12$
  - $\mathcal{H}_3 = (0{,}50;\, 0{,}70)$ com raio $r_3 = 0{,}12$
- **Condições Físicas:**
  - **Bordas externas ($x=0, x=1, y=0, y=1$):** Mantidas quentes a $u = 1{,}0$ (fonte de calor externa).
  - **Bordas dos furos:** Mantidas a $u = 0{,}0$ (sumidouros térmicos / canais de resfriamento).
  - **Interior da chapa:** Começa a $u(x,y,0) = 0$.
  - O calor entra pelas 4 paredes externas e é "sugado" pelos 3 orifícios internos, gerando frentes de difusão com fortes gradientes isotérmicos.

---

## 3. Imagens Integradas no Artigo
- **Figura 1:** Esquema geométrico da chapa com os 3 furos, coordenadas e condições de contorno ([`geometry_domain_holes.png`](file:///home/warley/vault/research/eu/drafts/figures/geometry_domain_holes.png)).
- **Figura 2:** Diagrama de camadas da MLP acoplada ao Autograd e à perda física da PINN ([`mlp_and_pinn_architecture.png`](file:///home/warley/vault/research/eu/drafts/figures/mlp_and_pinn_architecture.png)).
- **Figura 3:** Benchmark comparativo no quadrado regular (*Analítica vs. ADI vs. PINN vs. Erro Absoluto*) ([`adi_regular_benchmark.png`](file:///home/warley/vault/research/eu/drafts/figures/adi_regular_benchmark.png)).
- **Figura 4:** Resultados na geometria com 3 furos (Campo 2D + Corte 1D em $y=0{,}30$ cruzando os furos + Curva de convergência).
