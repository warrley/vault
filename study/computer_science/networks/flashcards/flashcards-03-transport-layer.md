---
tags:
  - flashcards
  - flashcards/networks
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: Transport Layer & Exercise Solutions (Lista 2 - UFC)

## 1. Core Principles, Sockets & Addressing (Exercises 1, 4, 5)

What is multiplexing in general, and what is an example NOT related to the transport layer? (Exercise 1)::Multiplexing is the technique of **combining multiple discrete signals, data streams, or communication channels into a single shared physical medium or resource**.<br>* **Non-transport examples**: 
1. **Frequency-Division Multiplexing (FDM)** in radio broadcasting or Cable TV (multiple stations sharing the same air spectrum/coaxial cable simultaneously on distinct frequencies).
2. **Time-Division Multiplexing (TDM)** in traditional telephony (multiple phone conversations sharing a single T1 trunk line by interleaving dedicated time slots).
3. **Statistical Multiplexing** in packet-switched network links (routers sharing link bandwidth dynamically on demand).
<!--ID: 1727000001-->

In Internet data transmission, how is a specific process identified inside a physical machine? Give concrete examples. (Exercise 4)::By the **two-level addressing tuple: $(\text{IP Address}, \text{Port Number})$**.<br>* **IP Address (Layer 3)**: Routes the packet across the global Internet to the destination network interface card.<br>* **Port Number (Layer 4, 16-bit integer $0-65535$)**: Directs the payload inside the operating system kernel to the exact application socket buffer.<br>* **Examples**: 
- Web Server daemon: `198.51.100.10:80` (HTTP) or `198.51.100.10:443` (HTTPS)
- DNS Server daemon: `8.8.8.8:53` (UDP/TCP)
- Outbound Web Browser tab: `192.168.1.15:52411` (Ephemeral client port).
<!--ID: 1727000002-->

What is a Socket, and what system call functions are necessary for its use in TCP and UDP? (Exercise 5)::A **Socket** is the software API endpoint/abstraction (the "door") bridging a user-space application process and the operating system kernel's transport layer.<br>* **TCP Stream Socket Functions (`SOCK_STREAM`)**:
  - `socket()`: Creates socket descriptor.
  - `bind()`: Binds socket to a specific local IP and port number.
  - `listen()`: Puts server socket in passive listening mode with a connection backlog queue.
  - `accept()`: Blocks and returns a new dedicated socket descriptor for an established 3-way handshake.
  - `connect()`: Client initiates 3-way handshake to remote `(IP, Port)`.
  - `send()` / `recv()` (or `write()` / `read()`): Transmits and reads continuous byte stream.
  - `close()`: Initiates 4-way connection teardown.
* **UDP Datagram Socket Functions (`SOCK_DGRAM`)**:
  - `socket()`, `bind()`, `sendto()` (includes dest IP/Port), `recvfrom()` (captures src IP/Port), `close()`.
<!--ID: 1727000003-->

---

## 2. TCP vs. UDP: Philosophy, Practice & Applications (Exercises 2, 3, 10)

What are the philosophical differences between TCP and UDP (what does each do best)? (Exercise 2)::* **TCP Philosophy (Safety, Reliability, Global Stability)**: Treats the network as an untrusted, fragile shared resource. Prioritizes **guaranteed correctness, ordered delivery, and collective network health** over raw speed, using connection state, sliding windows, flow control, and polite congestion throttling.<br>* **UDP Philosophy (Simplicity, Immediacy, Application Autonomy)**: Treats the network as a minimal raw bit-pipe. Prioritizes **zero latency overhead, minimal footprint, and absolute application autonomy**, giving the developer direct control over transmission rate without kernel intervention.
<!--ID: 1727000004-->

What are the practical differences between TCP and UDP when implementing and using them? (Exercise 3)::* **Connection Setup**: TCP requires a $1\text{ RTT}$ 3-way handshake; UDP has $0\text{ RTT}$ connection setup (sends data in 1st packet).<br>* **Data Abstraction**: TCP provides an **unstructured byte stream** (no packet boundaries; receiver reads arbitrary chunks); UDP provides discrete **message datagrams** (preserves packet boundaries 1:1).<br>* **Reliability & Delivery**: TCP guarantees 100% in-order delivery and duplicate suppression; UDP is best-effort (packets may arrive corrupted, out-of-order, duplicated, or not at all).<br>* **Speed & Throttling**: TCP pauses or throttles during congestion; UDP blasts at the application's generation rate.<br>* **Header Size**: TCP header is $20-60\text{ bytes}$; UDP header is fixed at $8\text{ bytes}$.
<!--ID: 1727000005-->

If TCP offers far more services than UDP, why do some applications choose UDP? Give concrete examples and explain why. (Exercise 10)::Because TCP's extra features introduce latency, jitter, and memory overhead that are intolerable for certain application classes:<br>1. **Real-Time Interactive Media (VoIP, Video Calls, Zoom/Discord)**: Retransmitting a dropped audio packet $200\text{ ms}$ later is useless because the conversation has moved on. Better to drop the frame and maintain real-time interactive playback.<br>2. **Fast Request-Response Query Services (DNS, DHCP)**: DNS lookups fit in a single datagram. Using TCP would double latency ($1\text{ RTT handshake} + 1\text{ RTT query}$). UDP resolves in a single $1\text{ RTT}$.<br>3. **High-Density Broadcast / Multicast (IPTV, Service Discovery)**: TCP cannot broadcast; UDP natively supports multicast/broadcast.<br>4. **Massive-Scale Stateless Servers (Root DNS, NTP)**: Servers would exhaust RAM maintaining TCP TCB state buffers for millions of concurrent users.
<!--ID: 1727000006-->

---

## 3. Error Detection & The Checksum (Exercise 6)

What is the purpose of the Checksum in the transport layer, and how does its algorithm work? (Exercise 6)::The **Checksum** detects bit corruption introduced by electrical noise, wireless attenuation, or router hardware faults.<br>* **Algorithm (Sender)**:
  1. Treat all bytes of the header, data (and IP pseudo-header) as a sequence of **16-bit unsigned integers**.
  2. Add them using **1's complement addition**: whenever an addition overflows the 16th bit, wrap the carry bit around and add it to the least significant bit ($LSB$).
  3. Compute the **bitwise inversion (1's complement)** ($0 \to 1, 1 \to 0$) and insert into the Checksum field.<br>* **Verification (Receiver)**:
  - Add all 16-bit words of the received segment **plus the Checksum**.
  - If the result is **`1111 1111 1111 1111` (`0xFFFF`)**, the segment is accepted as error-free.
  - If **any bit is `0`**, an error is detected and the segment is discarded.
<!--ID: 1727000007-->

---

## 4. TCP Lifecycle: Establishment & Teardown (Exercise 7)

How are TCP Connection Establishment and Connection Teardown performed? (Exercise 7)::* **Establishment (3-Way Handshake)**:
  1. `Client -> Server (SYN)`: `SYN = 1`, `Seq = x`, `ACK = 0`.
  2. `Server -> Client (SYN-ACK)`: `SYN = 1`, `ACK = 1`, `Seq = y`, `Ack_Num = x + 1`. Allocates TCB buffers.
  3. `Client -> Server (ACK)`: `ACK = 1`, `Seq = x + 1`, `Ack_Num = y + 1`. Connection `ESTABLISHED` (may carry application data).<br>* **Teardown (4-Way Handshake)**:
  1. `Client -> Server (FIN)`: Client signals it has finished sending data (`Seq = u`).
  2. `Server -> Client (ACK)`: Server acknowledges half-close (`Ack = u + 1`).
  3. `Server -> Client (FIN)`: Server finishes sending remaining data and signals its close (`Seq = v`).
  4. `Client -> Server (ACK)`: Client confirms (`Ack = v + 1`) and enters `TIME_WAIT` ($2 \times \text{MSL}$) before fully closing.
<!--ID: 1727000008-->

---

## 5. Flow Control & Buffer Management (Exercise 9)

How does TCP Flow Control work, and what is its relationship to the sliding window? (Exercise 9)::**Flow Control** is an end-to-end mechanism that prevents a fast sender from overflowing the receiver's allocated socket buffer (`RcvBuffer`).<br>* **Formula**: $rwnd = \text{RcvBuffer} - (\text{LastByteRcvd} - \text{LastByteRead})$.<br>* **Relationship with Sliding Window**: The receiver advertises $rwnd$ in every TCP header. The sender uses $rwnd$ as an absolute upper bound on its sliding window:
$$\text{In-Flight UnACKed Bytes} \le \min(cwnd, rwnd)$$
If the receiver buffer fills ($rwnd = 0$), the sender's sliding window closes completely, pausing transmission. Senders send periodic **1-byte probe segments** to prevent zero-window deadlocks.
<!--ID: 1727000009-->

---

## 6. TCP Congestion Control, Modes & New Reno (Exercise 8)

How does the TCP Congestion Control sliding window work, and what are the operating modes of TCP New Reno and the conditions for switching between them? (Exercise 8)::TCP regulates transmission rate via an internal **Congestion Window ($cwnd$)**, adjusting its size based on inferred network state ($\text{Rate} \approx \frac{cwnd}{RTT}$).<br>* **Operating Modes & Transitions**:
1. **Slow Start**: Begins at $cwnd = 1\text{ MSS}$. Grows **exponentially** ($2^k$, doubling every RTT by adding $+1\text{ MSS}$ per received ACK). Switches to Congestion Avoidance when $cwnd \ge ssthresh$.
2. **Congestion Avoidance**: Operates under **AIMD**. Grows **linearly** ($+1\text{ MSS}$ per RTT) probing for link capacity.
3. **Fast Recovery (TCP Reno / New Reno)**: Triggered upon receiving **3 Duplicate ACKs**.
   - Sets $ssthresh = \frac{cwnd}{2}$ and $cwnd = ssthresh + 3\text{ MSS}$.
   - **TCP New Reno Improvement**: In standard Reno, a single "partial ACK" during recovery causes TCP to exit Fast Recovery and stall. **New Reno distinguishes Partial ACKs from Full ACKs**, recognizing that multiple packets in the same window were dropped, retransmitting subsequent lost packets without dropping back to Slow Start.
4. **Timeout Fallback**: If a severe retransmission timeout occurs, $ssthresh = \frac{cwnd}{2}$, $cwnd$ drops to **$1\text{ MSS}$**, and TCP returns to **Slow Start**.
<!--ID: 1727000010-->

---

## 7. Deep Analytical Scenarios & Diagnostic Checks

Host A and Host B both open 2 concurrent TCP connections to Server S (port 80) with identical ephemeral ports 55000 and 55001. How many distinct sockets exist on Server S?::**5 sockets total**: 4 dedicated connection sockets (each uniquely keyed by its 4-tuple: `(Src IP, Src Port, Dst IP, Dst Port)`) plus 1 welcoming listening socket on port 80.
<!--ID: 1727000011-->

What does a Go-Back-N receiver do with out-of-order packets vs a standard TCP receiver?::* **Go-Back-N**: Discards out-of-order packets immediately (no buffer) and retransmits cumulative ACK for highest in-order packet.<br>* **Standard TCP**: Buffers out-of-order segments in memory and sends duplicate ACKs to trigger Fast Retransmit.
<!--ID: 1727000012-->

A TCP Reno sender with $cwnd = 32\text{ MSS}$ in Congestion Avoidance receives 3 Duplicate ACKs. What are the new $ssthresh$ and $cwnd$ upon entering Fast Recovery?::$ssthresh = \frac{32}{2} = \mathbf{16\text{ MSS}}$, and $cwnd = ssthresh + 3\text{ MSS} = \mathbf{19\text{ MSS}}$ (or $16\text{ MSS}$ baseline).
<!--ID: 1727000013-->
