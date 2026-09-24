---
tags:
  - networks/mechanism
  - networks/rdt
  - networks/pipelining
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Mechanism: Pipelined Reliable Data Transfer (GBN, SR, and TCP Hybrid)

### 1. Motivation: The Stop-and-Wait Utilization Bottleneck
In a stop-and-wait protocol ($rdt\text{ 3.0}$), the sender transmits a single packet and must wait for an acknowledgment ($ACK$) before transmitting the next.

#### Mathematical Formulation of Utilization:
Let:
* Link transmission rate: $R = 1\text{ Gbps} = 10^9\text{ bps}$
* Packet size: $L = 1,000\text{ bytes} = 8,000\text{ bits}$
* Round-Trip Time: $RTT = 30\text{ ms} = 0.03\text{ s}$

The packet transmission delay is:
$$d_{\text{trans}} = \frac{L}{R} = \frac{8,000\text{ bits}}{10^9\text{ bps}} = 0.008\text{ ms}$$

Sender Utilization ($U_{\text{sender}}$):
$$U_{\text{sender}} = \frac{d_{\text{trans}}}{RTT + d_{\text{trans}}} = \frac{0.008\text{ ms}}{30.008\text{ ms}} \approx 0.000267 \implies \mathbf{0.027\%}$$

> [!warning] Physical Inefficiency
> In stop-and-wait over high-speed links, the sender sits idle **$99.97\%$ of the time**, waiting for signals to propagate.

**The Solution: Pipelining (Sliding Windows)**  
The sender transmits up to **$N$ consecutive packets** without waiting for acknowledgments.

$$U_{\text{pipelined}} = \min\left(1, \; N \cdot \frac{d_{\text{trans}}}{RTT + d_{\text{trans}}}\right)$$

---

### 2. Protocol 1: Go-Back-N (GBN)

In Go-Back-N, the sender maintains a window of up to $N$ unacknowledged packets.

```
SENDER SLIDING WINDOW (Size N):
+---------------------+-------------------------------+-----------------------+
|  Sent & ACKed       |  Sent, NOT yet ACKed (Window) |  Usable, not yet sent |
+---------------------+-------------------------------+-----------------------+
                      ^                               ^
                   send_base                    next_seqnum
```

#### Core Mechanics of GBN:
1. **Cumulative ACKs:** An $\text{ACK}(k)$ confirms that **all packets up to and including $k$** were received correctly.
2. **Single Timer:** The sender maintains a single hardware/logical timer for the **oldest unacknowledged packet** (`send_base`).
3. **Receiver Discards Out-of-Order Packets:** The receiver maintains **zero buffer memory** for out-of-order packets. If packet $k$ arrives when expecting $k-1$, it drops packet $k$ and resends $\text{ACK}(k-1)$.
4. **Timeout Action:** When the timer expires, the sender **retransmits ALL $N$ unacknowledged packets** currently in the window.

```
GBN IN ACTION (Packet 2 Lost):
Sender:    [Pkt 0]  [Pkt 1]  [Pkt 2 (LOST)]  [Pkt 3]  [Pkt 4]
Receiver:   Pkt 0    Pkt 1         X          Pkt 3    Pkt 4
Actions:    ACK 0    ACK 1                    (DROPS!) (DROPS!)
                                              ACK 1    ACK 1
Sender Timeout on Pkt 2:
Retransmits: [Pkt 2] [Pkt 3] [Pkt 4]  <-- Retransmits entire window!
```

---

### 3. Protocol 2: Selective Repeat (SR)

To eliminate the bandwidth waste of retransmitting correctly received packets, **Selective Repeat** introduces receiver-side buffering.

#### Core Mechanics of SR:
1. **Individual ACKs:** The receiver sends an individual ACK for every correctly received packet, regardless of order.
2. **Receiver Buffering:** Out-of-order packets are **buffered in memory** while waiting for missing packets to fill the gap.
3. **Individual Timers:** The sender maintains an **independent timer for every unacknowledged packet**.
4. **Timeout Action:** When a packet's timer expires, the sender retransmits **ONLY that specific unacknowledged packet**.

```
SELECTIVE REPEAT IN ACTION (Packet 2 Lost):
Sender:    [Pkt 0]  [Pkt 1]  [Pkt 2 (LOST)]  [Pkt 3]  [Pkt 4]
Receiver:   Pkt 0    Pkt 1         X          Pkt 3    Pkt 4
Actions:    ACK 0    ACK 1                   (Buffers) (Buffers)
                                              ACK 3    ACK 4
Sender Timeout on Pkt 2:
Retransmits: [Pkt 2 ONLY]
Receiver gets Pkt 2: Delivers [Pkt 2, Pkt 3, Pkt 4] in-order to application!
```

---

### 4. TCP as a Hybrid Protocol

Real-world TCP combines the architectural simplicity of GBN with the performance efficiency of SR:

| Dimension | Go-Back-N (GBN) | Selective Repeat (SR) | **Real-World TCP** |
| :--- | :--- | :--- | :--- |
| **ACK Type** | Cumulative | Individual | **Cumulative** |
| **Timer Management** | Single timer for `send_base` | Timer per packet | **Single timer for oldest unACKed segment** |
| **Out-of-Order Handling** | Discards | Buffers in memory | **Buffers in memory (Implementation default)** |
| **Retransmission Scope** | Entire window ($N$ packets) | Only lost packet | **Only missing segment** (with SACK options) |

---

### 5. Fast Retransmit (The 3 Duplicate ACKs Rule)

TCP retransmission timeouts ($RTO$) are intentionally conservative to avoid unnecessary duplicate transmissions. However, waiting for an $RTO$ expiration introduces severe latency stalls.

**Fast Retransmit** uses arriving out-of-order duplicate ACKs as an instant loss detection signal:

```
SENDER                                                  RECEIVER
  |  --- Seg 1 (Seq=100) -----------------------------> | (Receives byte 100)
  |  <-- ACK 200 -------------------------------------- |
  |                                                     |
  |  --- Seg 2 (Seq=200) [LOST IN NETWORK] -----------> X
  |                                                     |
  |  --- Seg 3 (Seq=300) -----------------------------> | (Out-of-order! Buffers 300)
  |  <-- ACK 200 (Duplicate ACK 1) -------------------- | (Still expecting byte 200!)
  |                                                     |
  |  --- Seg 4 (Seq=400) -----------------------------> | (Out-of-order! Buffers 400)
  |  <-- ACK 200 (Duplicate ACK 2) -------------------- | (Still expecting byte 200!)
  |                                                     |
  |  --- Seg 5 (Seq=500) -----------------------------> | (Out-of-order! Buffers 500)
  |  <-- ACK 200 (Duplicate ACK 3) -------------------- | (Still expecting byte 200!)
  |                                                     |
  |  *** 3 TRIPLE DUPLICATE ACKS RECEIVED! ***         |
  |  ===> FAST RETRANSMIT: Immediately resends Seg 2!  |
  |  --- Seg 2 (Seq=200) -----------------------------> | (Fills the buffer gap!)
  |  <-- ACK 600 (Cumulative ACK for all buffered data)-| (Delivers bytes 100-599 to app)
  v                                                     v
```

> [!definition] Fast Retransmit Rule (RFC 5681)
> If a sender receives **3 duplicate ACKs** for the same sequence number (4 identical ACKs total), it infers that the segment immediately following that sequence number was lost, and **retransmits it immediately before the retransmission timer expires**.

---

### Summary
> [!abstract] Pipelined RDT Takeaway
> - **Pipelining** increases channel utilization from $<0.1\%$ to nearly $100\%$ by allowing up to $N$ in-flight packets.
> - **Go-Back-N (GBN):** Uses cumulative ACKs, a single timer, and discards out-of-order packets (retransmitting the entire window on timeout).
> - **Selective Repeat (SR):** Uses individual ACKs, per-packet timers, and buffers out-of-order packets.
> - **TCP Hybrid:** Employs cumulative ACKs with out-of-order buffering and uses **Fast Retransmit (3 duplicate ACKs)** for immediate recovery without waiting for timer expirations.
