---
tags:
  - networks/protocol
  - networks/tcp
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Protocol: Transmission Control Protocol (TCP) Segment & Connection Management

### 1. Architectural Overview & Properties (RFC 793, RFC 1122, RFC 5681)
The **Transmission Control Protocol (TCP)** is the primary connection-oriented, reliable transport protocol of the Internet stack.

> [!abstract] Foundational Pillars of TCP
> 1. **Point-to-Point**: Connection exists strictly between two endpoints (unicast only; no native multicast/broadcast).
> 2. **Reliable, In-Order Byte Stream**: Delivers an unstructured stream of bytes in exact sequential order without bit corruption, loss, or duplicates.
> 3. **Full-Duplex Service**: Application data flows bidirectionally over a single connection simultaneously.
> 4. **Connection-Oriented**: Requires explicit state establishment (handshake) before data transmission and graceful teardown when complete.

---

### 2. TCP Segment Header Format (20 to 60 Bytes)

Every TCP segment carries a minimum **20-byte base header**, followed by optional header fields and the payload data:

```
 0                   15 16                  31
+----------------------+----------------------+
|  Source Port (16b)   | Destination Port(16b)|  <-- Process endpoints
+----------------------+----------------------+
|                Sequence Number (32b)        |  <-- Byte-stream index of 1st data byte
+----------------------+----------------------+
|             Acknowledgment Number (32b)     |  <-- Next expected byte from peer
+------+---------------+----------------------+
| HLEN | Reserved|Flags|  Receive Window (16b)|  <-- Flow control (rwnd)
+------+---------------+----------------------+
|    Checksum (16b)    | Urgent Pointer (16b) |  <-- 1's-comp checksum & URG pointer
+----------------------+----------------------+
|          Options (0 to 40 bytes)            |  <-- MSS, Window Scale, Timestamps, SACK
+---------------------------------------------+
|                Application Data             |  <-- Byte stream payload
+---------------------------------------------+
```

#### Field-by-Field Breakdown:
* **Source & Destination Ports ($16$ bits each):** Demultiplexes segments to kernel sockets.
* **Sequence Number ($32$ bits):** The byte-stream number of the **first data byte** in this segment.
* **Acknowledgment Number ($32$ bits):** The sequence number of the **next byte the receiver is expecting** (Cumulative ACK).
* **Header Length (`HLEN` / Data Offset - $4$ bits):** Length of the TCP header in $32\text{-bit}$ words ($4\text{-byte}$ words). Since the base header is 20 bytes, the minimum $\text{HLEN} = 5$ ($5 \times 4 = 20\text{ bytes}$).
* **Receive Window (`rwnd` - $16$ bits):** Advertises available receiver buffer space for Flow Control.
* **Checksum ($16$ bits):** 1's-complement sum computed over TCP header, data, and a 12-byte IP pseudo-header.
* **Urgent Pointer ($16$ bits):** Offset from sequence number pointing to the last byte of urgent data (used when `URG = 1`).

#### The 6 Classic Control Flags:
| Flag | Name | Function |
| :--- | :--- | :--- |
| **`SYN`** | Synchronize | Initiates a connection and synchronizes Initial Sequence Numbers ($ISN$). |
| **`FIN`** | Finish | Sender has finished sending data; initiates graceful half-close. |
| **`ACK`** | Acknowledgment | Indicates that the *Acknowledgment Number* field contains valid data. |
| **`RST`** | Reset | Abruptly resets/aborts a connection (e.g., rejecting invalid/closed port segments). |
| **`PSH`** | Push | Instructs receiver to pass data immediately to application without waiting for buffer to fill. |
| **`URG`** | Urgent | Marks segment as carrying urgent data pointed to by the Urgent Pointer. |

---

### 3. Byte-Stream Sequence Numbering & Cumulative ACKs

Unlike message-oriented protocols, **TCP counts bytes, not packets**.

Given a continuous data stream divided into Maximum Segment Sizes ($MSS = 1000\text{ bytes}$):
* **Segment 1:** Bytes $0 \dots 999$ $\implies \mathbf{\text{Seq} = 0}$.
* **Segment 2:** Bytes $1000 \dots 1999$ $\implies \mathbf{\text{Seq} = 1000}$.
* **Segment 3:** Bytes $2000 \dots 2999$ $\implies \mathbf{\text{Seq} = 2000}$.

$$\text{Cumulative ACK Value} = \text{Next Expected Byte} = \text{Last In-Order Byte Received} + 1$$

---

### 4. Interactive Traffic & Piggybacking (Telnet Trace)

```
CLIENT (Host A)                                         SERVER (Host B)
  |                                                        |
  |  1. User types 'C' (1 byte)                            |
  |  ----------------- Seq = 42, ACK = 79, Data = 'C' ---> |
  |                                                        | (Server buffers 'C', echoes
  |                                                        |  'C' back to display on client,
  |                                                        |  and ACKs byte 42):
  |  <---------------- Seq = 79, ACK = 43, Data = 'C' ---- |
  |                                                        |
  |  2. Client receives echo & ACKs server's 'C':          |
  |  ----------------- Seq = 43, ACK = 80, Data = [None] ->|
  v                                                        v
```

> [!definition] Piggybacking
> When a host needs to acknowledge received data and simultaneously has outbound application data to transmit, it sends **both in a single segment** (e.g. `Seq = 79, ACK = 43, Data = 'C'`), saving packet headers and bandwidth.

---

### 5. Connection Lifecycle: Handshake & Teardown

```
    CLIENT                                             SERVER
      |                                                  | (Listening on Port 80)
      | ----------------- 1. SYN (seq = x) ------------> | (Allocates TCB & buffers)
      |                                                  |
      | <--------- 2. SYN-ACK (seq = y, ack = x + 1) --- |
      |                                                  |
      | ------------- 3. ACK (seq = x + 1, ack = y + 1) -> | (Connection ESTABLISHED)
      |       [Can carry first application payload!]     |
      |                                                  |
      |                     DATA EXCHANGE                |
      |                                                  |
      | ----------------- 1. FIN (seq = u) ------------> | (Client stops sending data)
      | <---------------- 2. ACK (ack = u + 1) --------- | (Server ACKs half-close)
      |                                                  | (Server may still send pending data)
      | <---------------- 3. FIN (seq = v) ------------- | (Server stops sending data)
      | ----------------- 4. ACK (ack = v + 1) --------> | (Connection CLOSED)
      | [Waits TIME_WAIT = 2*MSL before closing]         |
      v                                                  v
```

#### The 3-Way Handshake Steps:
1. **`SYN`**: Client chooses randomized Initial Sequence Number ($ISN = x$) and transmits segment with `SYN = 1`, `ACK = 0`.
2. **`SYN-ACK`**: Server allocates Transmission Control Block (TCB), chooses server $ISN = y$, and replies with `SYN = 1`, `ACK = x + 1`.
3. **`ACK`**: Client confirms server's sequence number with `ACK = y + 1`. Client state becomes `ESTABLISHED`. This 3rd packet **can carry initial application data**.

#### The 4-Way Teardown Steps:
Because TCP is full-duplex, each direction closes independently:
1. Client sends `FIN` ($\text{seq} = u$).
2. Server responds with `ACK` ($\text{ack} = u + 1$). Client enters `FIN_WAIT_2`.
3. When server finishes sending its remaining data, it transmits its own `FIN` ($\text{seq} = v$).
4. Client replies with `ACK` ($\text{ack} = v + 1$) and enters `TIME_WAIT` (typically $2 \times \text{MSL} \approx 60-120\text{ seconds}$) to guarantee the final ACK was received and drain stray packets from the network.

---

### Summary
> [!abstract] TCP Segment & Connection Management Takeaway
> - **TCP Segment Header:** 20-byte base header carrying sequence numbers, cumulative ACKs, receive window (`rwnd`), and control flags (`SYN`, `FIN`, `ACK`, `RST`, `PSH`, `URG`).
> - **Byte-Stream Indexing:** Sequence numbers identify the exact byte offset within the stream; ACKs represent the next expected byte.
> - **Piggybacking:** Combines outgoing data and incoming acknowledgments in a single packet.
> - **Lifecycle:** Established via a 3-way handshake (`SYN` $\to$ `SYN-ACK` $\to$ `ACK`) and terminated via an independent 4-way teardown (`FIN`/`ACK`).
