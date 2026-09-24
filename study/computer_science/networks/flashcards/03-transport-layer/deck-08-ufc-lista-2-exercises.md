---
tags:
  - flashcards
  - flashcards/networks/transport/exercises
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: Lista 2 de Exercícios (Transporte - UFC)

What is multiplexing, and what are two real-world examples NOT related to the transport layer? (Exercise 1)::Multiplexing is combining multiple distinct signals, data streams, or communications into a single shared physical resource.<br>* **Non-transport examples**:
1. **Frequency-Division Multiplexing (FDM)** in Radio/Cable TV (multiple TV channels broadcast simultaneously across different frequencies over one coaxial cable).
2. **Time-Division Multiplexing (TDM)** in telephony (multiple phone conversations sharing a single T1 trunk line by interleaving dedicated time slots).
<!--ID: 1727800001-->

What are the philosophical differences between TCP and UDP? (Exercise 2)::* **TCP Philosophy (Safety, Reliability & Global Health)**: Treats the network as a fragile shared resource. Prioritizes **guaranteed correctness, ordered delivery, and collective network stability** over raw speed, using connection state, sliding windows, flow control, and polite congestion throttling.<br>* **UDP Philosophy (Simplicity, Immediacy & Application Autonomy)**: Treats the network as a raw bit-pipe. Prioritizes **zero setup delay, minimal footprint, and absolute application autonomy**, giving the developer direct control over transmission rate without kernel intervention.
<!--ID: 1727800002-->

What are the practical differences between TCP and UDP when implementing/using them? (Exercise 3)::* **Connection Setup**: TCP requires a $1\text{ RTT}$ 3-way handshake; UDP has $0\text{ RTT}$ setup.<br>* **Data Abstraction**: TCP provides an **unstructured byte stream** (`SOCK_STREAM`); UDP preserves **discrete datagram boundaries** (`SOCK_DGRAM`).<br>* **Reliability**: TCP guarantees 100% in-order delivery and loss recovery; UDP is best-effort (packets may drop or reorder).<br>* **Rate Control**: TCP throttles rate under congestion; UDP blasts at application rate.<br>* **Header Size**: TCP header is $20-60\text{ bytes}$; UDP header is fixed at $8\text{ bytes}$.
<!--ID: 1727800003-->

In an Internet data transmission, how is a specific application process identified inside a physical machine? Give examples. (Exercise 4)::By the **two-level addressing tuple: $(\text{IP Address}, \text{Port Number})$**.<br>* **IP Address (Layer 3)**: Routes the packet across the global Internet to the destination network interface card.<br>* **Port Number (Layer 4, 16-bit integer $0-65535$)**: Directs the payload inside the operating system kernel to the exact application socket buffer.<br>* **Examples**:
- Web server: `198.51.100.10:80` (HTTP) or `198.51.100.10:443` (HTTPS)
- DNS server: `8.8.8.8:53` (UDP/TCP)
- Client browser tab: `192.168.1.15:52411` (Ephemeral port).
<!--ID: 1727800004-->

What is a Socket, and what functions are necessary for its use in TCP and UDP? (Exercise 5)::A **Socket** is the software API endpoint (the "door") bridging a user-space application process and the kernel's transport layer.<br>* **TCP Stream Socket Functions (`SOCK_STREAM`)**: `socket()`, `bind()`, `listen()`, `accept()`, `connect()`, `send()` / `recv()`, `close()`.<br>* **UDP Datagram Socket Functions (`SOCK_DGRAM`)**: `socket()`, `bind()`, `sendto()`, `recvfrom()`, `close()`.
<!--ID: 1727800005-->

What is the purpose of the Checksum, and how does its algorithm work? (Exercise 6)::The **Checksum** detects bit corruption introduced by electrical noise, wireless attenuation, or router memory faults.<br>* **Algorithm (Sender)**:
  1. Partition bytes into **16-bit unsigned integers**.
  2. Add them using **1's complement addition** (wrap overflow carry bits past the 16th bit back and add to the LSB).
  3. Compute the **bitwise inversion (1's complement)** ($0 \leftrightarrow 1$) and store in the Checksum field.<br>* **Verification (Receiver)**: Sum all words $+$ Checksum. If result is **`1111 1111 1111 1111` (`0xFFFF`)**, packet is error-free; otherwise discarded.
<!--ID: 1727800006-->

How are TCP Connection Establishment and Connection Teardown performed? (Exercise 7)::* **Establishment (3-Way Handshake)**:
  1. `Client -> Server (SYN)`: `SYN = 1`, `Seq = x`, `ACK = 0`.
  2. `Server -> Client (SYN-ACK)`: `SYN = 1`, `ACK = 1`, `Seq = y`, `Ack_Num = x + 1`.
  3. `Client -> Server (ACK)`: `ACK = 1`, `Seq = x + 1`, `Ack_Num = y + 1`.<br>* **Teardown (4-Way Full-Duplex Handshake)**:
  1. `Client -> Server (FIN)` $\to$ 2. `Server -> Client (ACK)`.
  3. `Server -> Client (FIN)` $\to$ 4. `Client -> Server (ACK)` (Client enters `TIME_WAIT`).
<!--ID: 1727800007-->

How does the TCP Congestion Control sliding window work, and what are the operating modes of TCP New Reno and when do transitions occur? (Exercise 8)::TCP regulates transmission rate via the **Congestion Window ($cwnd$)** ($\text{Rate} \approx \frac{cwnd}{RTT}$):<br>1. **Slow Start**: Begins at $cwnd = 1\text{ MSS}$. Doubles every RTT ($2^k$) until $cwnd \ge ssthresh$.<br>2. **Congestion Avoidance**: Grows linearly by $+1\text{ MSS}$ per RTT (AIMD).<br>3. **Fast Recovery (New Reno)**: Triggered by **3 Duplicate ACKs**. Sets $ssthresh = \frac{cwnd}{2}$ and $cwnd = ssthresh + 3\text{ MSS}$. Distinguishes Partial ACKs from Full ACKs to retransmit multiple lost packets in the same window without stalling back into Slow Start.<br>4. **Timeout**: Severe loss drops $cwnd = 1\text{ MSS}$ and restarts Slow Start.
<!--ID: 1727800008-->

How does TCP Flow Control work, and what is its relationship to the sliding window? (Exercise 9)::**Flow Control** prevents a fast sender from overflowing the receiver's socket buffer (`RcvBuffer`).<br>* **Formula**: $rwnd = \text{RcvBuffer} - (\text{LastByteRcvd} - \text{LastByteRead})$.<br>* **Relationship with Sliding Window**: The receiver advertises $rwnd$ in every TCP header. The sender restricts its sliding window to $\text{In-Flight} \le \min(cwnd, rwnd)$. If $rwnd = 0$, sender pauses and sends periodic 1-byte probes to avoid deadlock.
<!--ID: 1727800009-->

If TCP offers far more services than UDP, why do some applications choose UDP? Give examples. (Exercise 10)::Because TCP's reliability, connection setup, and congestion throttling introduce latency, jitter, and memory overhead that break certain application types:<br>1. **Real-Time Interactive Audio/Video (VoIP, Zoom, Discord, Gaming)**: Prefer dropping late frames over waiting for retransmissions.<br>2. **Single Query-Response Services (DNS, DHCP)**: Single-packet queries resolve in $1\text{ RTT}$ under UDP vs $2\text{ RTT}$ under TCP.<br>3. **High-Density Stateless Servers (Root DNS, NTP)**: Servers would exhaust memory buffers maintaining TCP connection states for millions of users.
<!--ID: 1727800010-->
