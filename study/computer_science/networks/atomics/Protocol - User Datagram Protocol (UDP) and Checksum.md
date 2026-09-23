---
tags:
  - networks/protocol
  - networks/udp
  - networks/checksum
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Protocol: User Datagram Protocol (UDP) & Checksum

### 1. Architectural Motivation (RFC 768)
The **User Datagram Protocol (UDP)** is the minimal, bare-bones Internet transport protocol. It acts as a thin wrapper over IP, providing essentially only two functions:
1. **Process Multiplexing / Demultiplexing** (via 16-bit Port Numbers)
2. **Lightweight Error Detection** (via 16-bit Checksum)

#### Why Applications Choose an "Unreliable" Protocol:
Why would an application choose UDP over full-featured TCP?

| Design Factor | UDP Rationale | TCP Contrast |
| :--- | :--- | :--- |
| **1. Application-Level Rate Control** | Sends data immediately as generated. Real-time apps (VoIP, games) prefer dropping old packets rather than waiting for retransmissions. | Throttles send rate via Congestion Control ($cwnd$) upon link congestion; stalls data pipeline. |
| **2. Zero Connection Setup Delay** | Transmits payload in the very first datagram ($0\text{ RTT}$ setup). Critical for latency-sensitive lookups (DNS, DHCP). | Requires $1\text{ RTT}$ 3-way handshake before any application data can be sent. |
| **3. Stateless at Server** | Server maintains zero connection state, zero timers, and zero buffers per client. A single UDP server can support tens of thousands of active clients. | Server must allocate Transmission Control Blocks (TCBs), sequence buffers, and timers for every client. |
| **4. Minimal Header Overhead** | Only **8 bytes** per segment. | Minimum **20 bytes** (and up to 60 bytes with options). |

---

### 2. UDP Segment Header Format

A UDP datagram consists of an **8-byte fixed header** followed by the application payload:

```
 0                   15 16                  31
+----------------------+----------------------+
|  Source Port Number  |  Dest Port Number    |  (Bytes 0-3)
+----------------------+----------------------+
|     Total Length     |       Checksum       |  (Bytes 4-7)
+----------------------+----------------------+
|                                             |
|          Application Payload Data           |
|                                             |
+---------------------------------------------+
```

* **Source Port ($16$ bits):** Port on sending host (used by receiver to address reply).
* **Destination Port ($16$ bits):** Port on destination host (used to demux to socket).
* **Length ($16$ bits):** Total length of UDP segment in bytes (Header $+$ Payload). Minimum value is $8\text{ bytes}$.
* **Checksum ($16$ bits):** Error detection field computed over the UDP pseudo-header, UDP header, and payload.

---

### 3. The Internet Checksum Algorithm

The Internet Checksum (RFC 1071) detects bit corruption introduced by physical noise, fading wireless channels, or router memory faults.

#### Mathematical Definition: 1's Complement Addition
In 1's complement arithmetic, an overflow beyond the $16\text{th}$ bit (a carry bit) is **wrapped around** (end-around carry) and added to the least significant bit ($LSB$).

$$\text{Checksum} = \sim \left( \sum_{i} \text{Word}_i \quad (\text{mod } 2^{16} - 1) \right)$$

---

#### Step-by-Step Calculation Procedure (Sender):

1. **Partition** all bytes in the segment into a sequence of **16-bit integers** (if odd number of bytes, pad with a trailing zero byte).
2. **Sum** all 16-bit integers using standard binary addition.
3. **Wrap Around Carry Bits:** Whenever a carry bit overflows beyond the $16\text{th}$ bit, add it to the lowest bit ($LSB$).
4. **Bitwise Inversion (1's Complement):** Invert all bits ($0 \to 1, 1 \to 0$).
5. **Store:** Place this final 16-bit value into the UDP Checksum field.

---

#### Concrete Numerical Example:

Calculate the checksum for two 16-bit words:
* $\text{Word}_1 = \texttt{1110 0110 0100 1100}$ ($\text{0xE64C}$)
* $\text{Word}_2 = \texttt{1101 0101 0101 0101}$ ($\text{0xD555}$)

$$\begin{array}{r@{\quad}l}
  & 1110\;0110\;0100\;1100 \\
+ & 1101\;0101\;0101\;0101 \\
\hline
\mathbf{1} & 1011\;1011\;1010\;0001 \quad (\text{Overflow carry bit: } \mathbf{1})
\end{array}$$

**Wrap around the carry bit:**
$$\begin{array}{r@{\quad}l}
  & 1011\;1011\;1010\;0001 \\
+ & 0000\;0000\;0000\;0001 \\
\hline
  & 1011\;1011\;1010\;0010 \quad (\text{Sum } = \text{0xBBA2})
\end{array}$$

**Bitwise Invert ($0 \leftrightarrow 1$):**
$$\text{Checksum} = \mathbf{0100\;0100\;0101\;1101} \quad (\text{0x445D})$$

---

### 4. Receiver Integrity Verification

When the receiver gets the segment, it adds **all 16-bit words together PLUS the received Checksum**:

$$\text{Verification Sum} = \text{Word}_1 + \text{Word}_2 + \dots + \text{Word}_n + \text{Checksum}$$

```
+-------------------------------------------------------------------------+
| RECEIVER VERIFICATION RULE                                              |
| * If Verification Sum == 1111 1111 1111 1111 (0xFFFF)                   |
|   --> Segment is error-free (No bit errors detected).                   |
| * If ANY bit in the Verification Sum is 0                               |
|   --> Error detected! Segment is corrupt and must be discarded.         |
+-------------------------------------------------------------------------+
```

#### Why it evaluates to `0xFFFF`:
Because $\text{Checksum} = \sim \text{Sum}$, we have:
$$\text{Sum} + \sim\text{Sum} = \texttt{1111 1111 1111 1111}_2 = \text{0xFFFF}$$

---

### 5. Checksum Capabilities & Limitations

* **Error Detection Capability:** Detects all single-bit errors and the vast majority of multi-bit burst errors.
* **Limitations (No Error Correction):** UDP checksum cannot identify *which* bit flipped, so it **cannot correct errors** (unlike Hamming codes or Reed-Solomon).
* **Compensating Errors (Undetected):** If one bit flips from $0 \to 1$ and an identical positional bit in another word flips from $1 \to 0$, the arithmetic sum remains unchanged, leaving the corruption **undetected**.

---

### Summary
> [!abstract] UDP and Checksum Takeaway
> - **UDP Header:** Fixed 8 bytes containing `(Source Port, Destination Port, Length, Checksum)`.
> - **Design Philosophy:** Minimalist, zero connection setup latency, stateless, no congestion control throttling.
> - **Internet Checksum:** Computed via 1's complement addition with end-around carry wrap, followed by bitwise inversion.
> - **Receiver Check:** $\sum \text{Words} + \text{Checksum} = \text{0xFFFF}$ (all 1s). Any 0 bit indicates packet corruption.
