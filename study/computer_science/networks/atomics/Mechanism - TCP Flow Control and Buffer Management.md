---
tags:
  - networks/mechanism
  - networks/flow-control
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Mechanism: TCP Flow Control & Buffer Management

### 1. The Core Objective of Flow Control
**Flow Control** is an end-to-end speed-matching service that prevents a fast sender from overflowing the memory buffers of a slower receiving application.

```
+-----------------------------------------------------------------------------------+
| FLOW CONTROL vs. CONGESTION CONTROL                                                |
| * Flow Control: Protects the RECEIVER SOCKET BUFFER from application lag.          |
| * Congestion Control: Protects INTERMEDIATE ROUTERS & LINKS from traffic overload. |
+-----------------------------------------------------------------------------------+
```

---

### 2. Receiver Buffer Architecture (`RcvBuffer` & `rwnd`)

When a TCP connection is established, the receiving operating system allocates a dedicated kernel memory space called **`RcvBuffer`** (typically configured via `SO_RCVBUF`, defaulting to several kilobytes or megabytes).

```
                                RECEIVER BUFFER (RcvBuffer)
+---------------------------------------------+------------------------------------+
|  Buffered Data waiting for Application      |         Free Buffer Space          |
|  (Received, ACKed, not yet read by app)     |       Available for new data       |
+---------------------------------------------+------------------------------------+
^                                             ^                                    ^
|                                             |                                    |
LastByteRead                           LastByteRcvd                       RcvBuffer End
|<-------- Buffered Data in Kernel ---------->|<----------- rwnd (Free) ---------->|
```

#### Byte Stream Pointers:
1. **`LastByteRead`**: The byte sequence number that the receiving user application has already read from the buffer via `read()` / `recv()`.
2. **`LastByteRcvd`**: The sequence number of the last byte that arrived from the network, passed checksum verification, and was placed into the buffer.

---

### 3. Mathematical Formulation of the Receive Window

The currently occupied space in kernel memory is:
$$\text{Occupied Space} = \text{LastByteRcvd} - \text{LastByteRead}$$

To prevent buffer overflow, the spare capacity—the **Receive Window ($rwnd$)**—is calculated dynamically:
$$\mathbf{rwnd = \text{RcvBuffer} - (\text{LastByteRcvd} - \text{LastByteRead})}$$

#### Sender Transmission Constraint:
The receiver advertises its current $rwnd$ in the **16-bit Receive Window field** of every outgoing TCP segment. The sender continuously enforces:

$$\mathbf{\text{LastByteSent} - \text{LastByteAcked} \le rwnd}$$

```
If rwnd decreases (buffer filling up):   ===> Sender throttles transmission window.
If rwnd == 0 (buffer completely full):  ===> Sender stops transmitting new data!
```

---

### 4. Zero-Window Deadlock & The 1-Byte Probe Segment

When the receiver buffer fills up completely ($rwnd = 0$), a subtle deadlock scenario arises:

```
1. Receiver buffer full ===> Advertises rwnd = 0 in ACK segment.
2. Sender receives rwnd = 0 ===> Sender blocks and stops transmitting.
3. Receiving application calls read() ===> Consumes all data; buffer is now 100% EMPTY!
```

> [!warning] The Zero-Window Deadlock
> If the receiver has no outbound data to transmit back to the sender, it will not generate any segments. Because the sender is blocked from sending, it never receives an updated $rwnd$, resulting in a permanent **deadlock**.

#### The Solution: Zero-Window Probing (RFC 793)
When $rwnd = 0$, the sender starts a **persist timer**. When the timer expires, the sender transmits a **Probe Segment with $1\text{ byte}$ of payload data**:
1. The probe forces the receiver to respond with an acknowledgment segment.
2. This acknowledgment contains the updated, non-zero $rwnd$ value.
3. The sender learns that buffer space has reopened and resumes normal high-throughput transmission.

---

### 5. Numerical Example / Exam Problem

> [!example] Worked Problem
> **Given:**
> * `RcvBuffer` $= 100,000\text{ bytes}$
> * $\text{LastByteRead} = 30,000$
> * $\text{LastByteRcvd} = 90,000$
> 
> **Calculation:**
> $$\begin{aligned}
> \text{Occupied Space} &= \text{LastByteRcvd} - \text{LastByteRead} = 90,000 - 30,000 = 60,000\text{ bytes} \\
> rwnd &= \text{RcvBuffer} - \text{Occupied Space} = 100,000 - 60,000 = \mathbf{40,000\text{ bytes}}
> \end{aligned}$$
> The sender is permitted to transmit at most $40,000$ unacknowledged bytes before pausing.

---

### Summary
> [!abstract] Flow Control Takeaway
> - **Flow Control** prevents a fast sender from exhausting the receiver's application buffer.
> - **Receive Window ($rwnd$):** $rwnd = \text{RcvBuffer} - (\text{LastByteRcvd} - \text{LastByteRead})$.
> - **Constraint:** Senders maintain $\text{LastByteSent} - \text{LastByteAcked} \le rwnd$.
> - **Deadlock Prevention:** Senders transmit periodic **1-byte probe segments** when $rwnd = 0$ to elicit updated window advertisements.
