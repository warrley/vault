$$
\begin{logicproof}{6}
\begin{subproof}
(\lnot P\lor R)\land (P\lor R) & hipótese\\
\lnot P\lor R & $\land e$ 1\\
P\lor R & $\land e$ 1\\
\begin{subproof}
\lnot R & hipótese\\
\begin{subproof}
\lnot P & hipótese\\
\begin{subproof}
P & hipótese\\
\bot & $\lnot e$ 5, 6
\end{subproof}
\begin{subproof}
R & hipótese\\
\bot & $\lnot e$ 4, 8
\end{subproof}
\bot & $\lor e$ 3, 6-7, 8-9
\end{subproof}
\begin{subproof}
R & hipótese\\
\bot & $\lnot e$ 4, 11
\end{subproof}
\bot & $\lor e$ 2, 5-10, 11-12
\end{subproof}
R & raa 4-13
\end{subproof}
((\lnot P\lor R)\land (P\lor R))\rightarrow R & $\rightarrow i$ 1-14
\end{logicproof}
$$