---
tags:
  - networks/mechanism
  - networks/congestion-control
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Mechanism: TCP Congestion Control & Bottleneck Fairness

### 1. The Nature of Network Congestion
Network congestion occurs when too many sources send data faster than the intermediate network core routers can buffer and forward.

#### The Costs of Congestion:
1. **Excessive Queuing Delay:** As router buffer queues fill up, Round-Trip Times ($RTT$) increase exponentially.
2. **Buffer Overflow Packet Drops:** Packets are discarded when router queues fill completely, triggering retransmissions.
3. **Wasted Upstream Link Capacity:** When a packet is dropped at a bottleneck router near its destination, all transmission capacity consumed on upstream links across the path is wasted.

---

### 2. End-to-End vs. Network-Assisted Congestion Control

* **Network-Assisted Congestion Control:** Intermediate routers explicitly communicate congestion state to end hosts (e.g., setting the **ECN - Explicit Congestion Notification** bits in IP headers or generating ICMP Source Quench packets).
* **End-to-End Congestion Control (Standard TCP):** Intermediate routers provide **zero explicit feedback**. End hosts infer network congestion strictly by observing **loss events (timeouts and duplicate ACKs)** and throttle their transmission rates autonomously.

---

### 3. The Congestion Window ($cwnd$)

TCP regulates transmission rate using an internal state variable called the **Congestion Window ($cwnd$)**:

$$\text{Maximum In-Flight Bytes} \le \min(\mathbf{cwnd},\; \mathbf{rwnd})$$

$$\text{Effective Sending Rate} \approx \frac{\mathbf{cwnd}}{RTT}\text{ bytes/second}$$

* Senders probe for spare network capacity by **increasing $cwnd$** when acknowledgments arrive without loss.
* Senders back off by **decreasing $cwnd$** when a loss event occurs.

---

### 4. The 3 Phases of TCP Congestion Control (RFC 5681)

```
cwnd (MSS)
  ^
  |                                                  / (Linear: Congestion Avoidance)
16|                                      +----------+
  |                                     / | ssthresh = 8
 8|             +----------------------+  |
  |            / ssthresh = 8             |
 4|          /                            | (Loss Event: Timeout vs 3 Dup ACKs)
 2|        / (Exponential:                |
 1|---+---+   Slow Start)                 |
  +----------------------------------------------------> Time (in RTTs)
```

#### Phase 1: Slow Start (Exponential Growth)
* **Starting State:** $cwnd = 1\text{ MSS}$ ($1$ Maximum Segment Size).
* **Growth Rule:** Increase $cwnd$ by **$1\text{ MSS}$ for every incoming ACK**.
  - $RTT_1$: $1\text{ segment sent} \to 1\text{ ACK received} \implies cwnd = 2\text{ MSS}$.
  - $RTT_2$: $2\text{ segments sent} \to 2\text{ ACKs received} \implies cwnd = 4\text{ MSS}$.
  - $RTT_3$: $4\text{ segments sent} \to 4\text{ ACKs received} \implies cwnd = 8\text{ MSS}$.
* **Result:** The sending window **doubles every RTT** ($2^k$ exponential increase) to rapidly ramp up to link capacity.
* **Transition:** When $cwnd \ge \mathbf{ssthresh}$ (*Slow Start Threshold*), TCP switches to Phase 2.

---

#### Phase 2: Congestion Avoidance (Linear Growth - AIMD)
Once $cwnd$ reaches $ssthresh$, explosive exponential growth is replaced by careful linear probing:
* **Growth Rule:** Increase $cwnd$ by **$1\text{ MSS}$ per RTT** (or $\frac{\text{MSS} \times \text{MSS}}{cwnd}$ per received ACK).
* This provides the **Additive-Increase** component of AIMD.

---

#### Phase 3: Handling Loss Events (TCP Tahoe vs. TCP Reno)

When a loss event occurs, TCP updates $ssthresh$ and cuts $cwnd$:

```
                             LOSS EVENT OCCURS
                                     |
                 +-------------------+-------------------+
                 |                                       |
          [TIMEOUT EVENT]                      [3 DUPLICATE ACKS]
       (Severe Congestion:                     (Mild Congestion:
     Network pipe fully stalled)              Data still flowing)
                 |                                       |
    ssthresh = cwnd / 2                     ssthresh = cwnd / 2
    cwnd = 1 MSS (All versions)                          |
    --> Enters Slow Start                   +------------+------------+
                                            |                         |
                                      [TCP Tahoe]                [TCP Reno]
                                      cwnd = 1 MSS          cwnd = ssthresh + 3 MSS
                                   --> Slow Start          --> Fast Recovery
```

#### Comparative Reaction Matrix:
| Version | Response to Timeout | Response to 3 Duplicate ACKs |
| :--- | :--- | :--- |
| **TCP Tahoe (1988)** | $ssthresh = \frac{cwnd}{2}, \quad cwnd = 1\text{ MSS}$ (Slow Start) | $ssthresh = \frac{cwnd}{2}, \quad cwnd = 1\text{ MSS}$ (Slow Start) |
| **TCP Reno (1990)** | $ssthresh = \frac{cwnd}{2}, \quad cwnd = 1\text{ MSS}$ (Slow Start) | $ssthresh = \frac{cwnd}{2}, \quad cwnd = ssthresh + 3\text{ MSS}$<br>*(**Fast Recovery**: skips Slow Start and resumes linearly)* |

---

### 5. AIMD Dynamics & Bottleneck Fairness

Why does TCP achieve fair bandwidth sharing among independent connections without central coordination?

```
Throughput of Connection 2
  ^
  |               / Equal Bandwidth Line (Throughput 1 = Throughput 2)
  |              /
  |             /
  |            /      /\
  |           /      /  \  Multiplicative Decrease (/2)
  |          /      /    \
  |         /      /      \
  |        /      /  AIMD  \
  |       /      / Sawtooth \
  |      /      /  Converges \
  |     /      /              \
  +----+------------------------------------> Throughput of Connection 1
```

If $K$ independent TCP sessions share a bottleneck link of bandwidth $R$:
1. **Multiplicative Decrease (/2):** Connections utilizing more bandwidth lose more absolute capacity when a drop occurs.
2. **Additive Increase (+1):** All connections increase their windows at the exact same rate ($+1\text{ MSS/RTT}$) during available capacity probing.
3. **Convergence:** Over multiple sawtooth cycles, the trajectories converge along the **Fair Share Line**, yielding equal bandwidth:
$$\text{Fair Throughput} = \mathbf{\frac{R}{K}}$$

---

### Summary
> [!abstract] Congestion Control Takeaway
> - **Congestion Control** inferentially protects intermediate router buffers and link capacity using end-to-end feedback.
> - **Rate Equation:** $\text{Rate} \approx \frac{cwnd}{RTT}$.
> - **Slow Start:** Exponential growth ($2^k$) from $1\text{ MSS}$ up to $ssthresh$.
> - **Congestion Avoidance:** Linear additive growth ($+1\text{ MSS/RTT}$).
> - **Loss Handling:**
>   - **Timeout:** Severe; resets $cwnd = 1\text{ MSS}$ and $ssthresh = \frac{cwnd}{2}$.
>   - **3 Duplicate ACKs (Reno):** Mild; sets $ssthresh = \frac{cwnd}{2}$ and enters **Fast Recovery** ($cwnd = ssthresh$), preserving high pipeline utilization.
> - **AIMD Convergence:** Guarantees equal bandwidth sharing ($\frac{R}{K}$) across bottleneck connections.
