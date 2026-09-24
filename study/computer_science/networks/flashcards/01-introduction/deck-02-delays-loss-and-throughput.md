---
tags:
  - flashcards
  - flashcards/networks/intro/delays-performance
  - networks/fundamentals
  - ufc/computer-networks
parent: "[[01-introduction-to-networks]]"
---

# Flashcards: Delays, Loss & Network Performance

What are the 4 fundamental sources of packet delay in a packet-switched network?::1. **Nodal Processing Delay ($d_{\text{proc}}$)**: Time to inspect packet headers, check bit-level errors, and determine egress interface.<br>2. **Queuing Delay ($d_{\text{queue}}$)**: Time the packet spends waiting in router buffer memory for transmission.<br>3. **Transmission Delay ($d_{\text{trans}}$)**: Time required to push all packet bits onto the physical link ($L/R$).<br>4. **Propagation Delay ($d_{\text{prop}}$)**: Time for a physical bit to travel across the physical medium ($d/s$).
<!--ID: 1715200001-->

What is the formula and physical meaning of Transmission Delay ($d_{\text{trans}}$)?::$$d_{\text{trans}} = \frac{L}{R}$$
Where $L$ is packet length in bits and $R$ is link transmission rate in bps. It is the time the network interface needs to serialize and transmit all bits. It depends **only on packet size and link capacity**, completely independent of physical distance.
<!--ID: 1715200002-->

What is the formula and physical meaning of Propagation Delay ($d_{\text{prop}}$)?::$$d_{\text{prop}} = \frac{d}{s}$$
Where $d$ is the physical length of the link in meters and $s$ is the propagation speed of the signal in the medium ($s \approx 2 \times 10^8\text{ m/s}$ in copper/fiber). It depends **only on distance and physical medium speed**, completely independent of packet size or link transmission rate.
<!--ID: 1715200003-->

In Kurose's toll-booth caravan analogy, what corresponds to Transmission Delay vs Propagation Delay?::* **Transmission Delay**: The time it takes for the **toll-booth operator to service all 10 cars** in a caravan and release them onto the highway ($L/R$).<br>* **Propagation Delay**: The time it takes for a **car to physically drive along the highway** from Toll Booth 1 to Toll Booth 2 ($d/s$).
<!--ID: 1715200004-->

What is Traffic Intensity ($\frac{L \cdot a}{R}$) and what does it indicate about router queuing delay?::Where $L$ is packet length (bits), $a$ is average packet arrival rate (pkts/sec), and $R$ is transmission rate (bps):<br>* If $\frac{L \cdot a}{R} \approx 0$: Queuing delay is negligible.<br>* If $\frac{L \cdot a}{R} \to 1$: Queuing delay grows asymptotically to infinity as queues form.<br>* If $\frac{L \cdot a}{R} > 1$: Average arrival rate exceeds link capacity, queuing delay is infinite, and **packet loss occurs** as router buffers overflow.
<!--ID: 1715200005-->

Under what exact condition does packet loss occur at an intermediate router?::When a packet arrives at a router whose buffer memory is completely full ($\text{Buffer Occupancy} = \text{Capacity}$), leaving no room to store the incoming packet, forcing the router to discard (drop) it.
<!--ID: 1715200006-->

What is the Bottleneck Link in an end-to-end network path, and what is the formula for end-to-end throughput?::The bottleneck link is the link along the transmission path with the **minimum transmission rate**. For a path with link capacities $R_1, R_2, \dots, R_n$, the end-to-end throughput is bounded by:
$$\text{Throughput} = \min(R_1, R_2, \dots, R_n)$$
<!--ID: 1715200007-->
