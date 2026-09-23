# Roadmap de Melhorias: Paper 1 (Heat Equation: ADI vs. PINN)

> **Documento Alvo:** `./research/eu/drafts/paper1_heat_adi_pinn.tex`  
> **Objetivo:** Elevar o rigor quantitativo e a competitividade do artigo para premiação no XVI Encontros Universitários da UFC em Quixadá 2026, mantendo o limite estrito de **3 a 5 páginas**.

---

## 1. Métricas Quantitativas e Histórico de Convergência
- [ ] **Valores Finais da Função de Perda:** Adicionar os valores numéricos exatos atingidos ao término do treinamento (10.000 épocas):
  - $\mathcal{L}_{\text{total}}$, $\mathcal{L}_{\text{pde}}$, $\mathcal{L}_{\text{ic}}$, $\mathcal{L}_{\text{bc}}^{\text{ext}}$ e $\mathcal{L}_{\text{bc}}^{\text{furos}}$.
- [ ] **Erro Máximo de Imposição de Fronteira:** Quantificar o erro residual máximo ao longo dos perímetros circulares dos três furos:
  $$\epsilon_{\text{max}}^{\text{furos}} = \max_{\theta \in [0, 2\pi), \, k \in \{1,2,3\}} |u_\theta(t, x_k + r_k\cos\theta, y_k + r_k\sin\theta) - 0|$$
- [ ] **Custo Computacional e Benchmark de Tempo:**
  - Tempo de treinamento em GPU/CPU (wall-clock time para 10.000 épocas).
  - Tempo de inferência direta da rede para uma grade densa de $200 \times 200$ pontos ($\sim \mathcal{O}(\text{ms})$), evidenciando a velocidade de avaliação da representação contínua.

---

## 2. Corte Transversal 1D (Slice de Temperatura ao longo de $y=0{,}30$)
- [ ] **Perfil 1D Atravessando Dois Furos:** Gerar um gráfico 1D do campo $u(x, y=0{,}30, t)$ para $x \in [0, 1]$ em diferentes instantes de tempo ($t=0{,}1, t=0{,}5, t=1{,}0$):
  - A reta $y=0{,}30$ intercepta os furos centrais em $x=0{,}30$ e $x=0{,}70$.
  - O gráfico comprova visualmente a queda abrupta da temperatura para $u=0{,}0$ dentro dos sumidouros térmicos e o valor $u=1{,}0$ nas paredes exteriores ($x=0$ e $x=1$).

---

## 3. Validação Cruzada de Linha de Base no Quadrado Regular (ADI vs. PINN)
- [ ] **Benchmark Canônico sem Furos:** Incluir um parágrafo conciso com a validação da PINN contra a solução clássica/analítica da equação do calor no quadrado unitário simples:
  $$u_{\text{exata}}(x,y,t) = \sin(\pi x)\sin(\pi y) e^{-2\pi^2 \alpha t}$$
- [ ] **Norma de Erro Relativo $\mathcal{L}_2$:**
  $$\epsilon_{\mathcal{L}_2} = \frac{\|u_{\text{PINN}} - u_{\text{ref}}\|_2}{\|u_{\text{ref}}\|_2} \approx 10^{-3} \text{ a } 10^{-4}$$
  - Isso estabelece solidez metodológica antes de apresentar o caso complexo com furos.

---

## 4. Ponderação Adaptativa da Função de Perda ($\lambda_{\text{BC}}$ Balancing)
- [ ] **Dinâmica de Gradientes:** Explicar a estratégia de balanceamento dos pesos na perda multiobjetivo:
  $$\mathcal{L}(\theta) = \mathcal{L}_{\text{pde}} + \lambda_{\text{ic}}\mathcal{L}_{\text{ic}} + \lambda_{\text{bc}}^{\text{ext}}\mathcal{L}_{\text{bc}}^{\text{ext}} + \lambda_{\text{bc}}^{\text{furos}}\mathcal{L}_{\text{bc}}^{\text{furos}}$$
- [ ] Justificar por que a imposição precisa de condições de contorno rígidas com furos pode requerer $\lambda_{\text{bc}} > 1$ para evitar o viés espectral (*spectral bias*) da rede neural.

---

## 5. Aprimoramento Visual (Figura Composta de 3 Painéis)
- [ ] **Painel (a):** Mapa 2D de contorno térmico em $t=0{,}80$.
- [ ] **Painel (b):** Perfil 1D de temperatura na seção $y=0{,}30$.
- [ ] **Painel (c):** Curva de convergência semi-logarítmica das perdas ($\mathcal{L}_{\text{pde}}$, $\mathcal{L}_{\text{bc}}$, $\mathcal{L}_{\text{ic}}$) vs. épocas de treinamento.
