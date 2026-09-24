---
tags:
  - flashcards
  - flashcards/networks/transport/congestion-control
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: TCP Congestion Control & Bottleneck Fairness

What is network congestion, and what are its three primary costs?::Congestion occurs when too many sources inject traffic faster than intermediate network routers and links can handle.<br>* **Costs**:
1. Exponentially high queuing delays in router buffers ($RTT$ spikes).
2. Buffer overflow packet drops.
3. Wasted upstream link transmission capacity for packets dropped near destinations.
<!--ID: 1727700001-->

What is the difference between End-to-End Congestion Control and Network-Assisted Congestion Control?::* **End-to-End (Standard TCP)**: Intermediate routers provide zero explicit feedback. End hosts infer network congestion strictly by observing packet loss events (timeouts and duplicate ACKs) and throttle rate autonomously.<br>* **Network-Assisted**: Intermediate routers explicitly signal congestion to end hosts (e.g. via IP Explicit Congestion Notification - ECN bits).
<!--ID: 1727700002-->

What is the mathematical relationship between the TCP Congestion Window ($cwnd$), Round-Trip Time ($RTT$), and the sender's effective transmission rate?::$$\text{Transmission Rate} \approx \frac{cwnd}{RTT}\text{ bytes/second}$$
The actual amount of unACKed in-flight data is bounded by $\min(cwnd, rwnd)$.
<!--ID: 1727700003-->

How does the TCP Congestion Window ($cwnd$) grow during the Slow Start phase?::Starts at $cwnd = 1\text{ MSS}$. For **every received ACK, $cwnd$ increases by $1\text{ MSS}$**. This causes the window to **double every single RTT** ($2^k$ exponential explosion: $1 \to 2 \to 4 \to 8 \dots$) until $cwnd \ge ssthresh$.
<!--ID: 1727700004-->

How does the TCP Congestion Window ($cwnd$) grow during the Congestion Avoidance phase?::Operates under **Additive Increase**: increases $cwnd$ linearly by **$1\text{ MSS}$ per RTT** (or by $\frac{\text{MSS} \times \text{MSS}}{cwnd}$ per received ACK) to gently probe for available link bandwidth.
<!--ID: 1727700005-->

How does TCP Tahoe respond to a Timeout vs 3 Duplicate ACKs?::TCP Tahoe treats both events identically:
* Sets $ssthresh = \frac{cwnd}{2}$.
* Resets $\mathbf{cwnd = 1\text{ MSS}}$ and re-enters **Slow Start**.
<!--ID: 1727700006-->

How does TCP Reno respond to a Timeout vs 3 Duplicate ACKs?::* **Timeout (Severe Congestion)**: Sets $ssthresh = \frac{cwnd}{2}$, resets $\mathbf{cwnd = 1\text{ MSS}}$, and restarts in **Slow Start**.<br>* **3 Duplicate ACKs (Mild Congestion)**: Sets $ssthresh = \frac{cwnd}{2}$, sets $\mathbf{cwnd = ssthresh + 3\text{ MSS}}$, and enters **Fast Recovery** (skips Slow Start and resumes linearly in Congestion Avoidance).
<!--ID: 1727700007-->

What improvement does TCP New Reno introduce over standard TCP Reno during Fast Recovery?::Standard Reno exits Fast Recovery on the first partial ACK received, stalling if multiple packets in the same window were dropped. **TCP New Reno distinguishes Partial ACKs from Full ACKs**, recognizing that multiple packets in the window were lost, retransmitting subsequent lost packets without dropping back to Slow Start.
<!--ID: 1727700008-->

Why does the AIMD (Additive-Increase Multiplicative-Decrease) algorithm guarantee fairness among $K$ competing TCP flows sharing a bottleneck link of capacity $R$?::Because multiplicative decrease cuts larger flows by a larger absolute value ($50\%$), while additive increase expands all flows at the identical linear rate ($+1\text{ MSS/RTT}$). Over multiple sawtooth cycles, throughput converges along the equal-share line to $\mathbf{\frac{R}{K}}$ per flow.
<!--ID: 1727700009-->
