---
tags:
  - networks/mechanism
  - networks/multiplexing
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Mechanism: Transport Layer Multiplexing and Demultiplexing

### 1. The Host-to-Process Demultiplexing Problem
The Network Layer (IP) delivers datagrams to a specific destination host using its **IP address**. However, a host runs dozens or hundreds of concurrent network processes:
* Multiple browser tabs (HTTP/HTTPS to different web servers)
* Background music streaming (Spotify)
* Terminal remote session (SSH)
* Local database daemon (PostgreSQL)

When an incoming IP datagram arrives at the Network Interface Card (NIC), the operating system transport layer must direct the encapsulated payload to the exact application process.

---

### 2. Sockets & Port Numbers

To bridge user processes and the network, the operating system uses the **Socket** abstraction. Every socket is bound to a **16-bit Port Number** ($0 \text{ to } 65535 = 2^{16} - 1$):

```
 0                   15 16                  31
+----------------------+----------------------+
|  Source Port (16b)   | Destination Port(16b)|
+----------------------+----------------------+
|                  Transport Header           |
```

#### Port Number Hierarchy (IANA Standard):
1. **Well-Known Ports ($0 - 1023$):** Standardized, restricted to privileged system processes.
   - HTTP: `80`, HTTPS: `443`, SSH: `22`, DNS: `53`, SMTP: `25`, FTP: `20/21`, DHCP: `67/68`.
2. **Registered Ports ($1024 - 49151$):** Registered for user services (e.g., MySQL: `3306`, Redis: `6379`).
3. **Dynamic / Ephemeral / Private Ports ($49152 - 65535$, often starting at $1024$ in Linux):** Automatically assigned by the OS kernel to client processes for outbound connections.

---

### 3. Multiplexing vs. Demultiplexing Operations

```
SENDER HOST (Multiplexing)                      RECEIVER HOST (Demultiplexing)
+-------------------------+                     +-------------------------+
| Process P1 | Process P2 |                     | Process P3 | Process P4 |
| (Socket 1) | (Socket 2) |                     | (Socket 3) | (Socket 4) |
+------------+------------+                     +------------+------------+
        \         /                                    ^         ^
         \       /                                      \       /
      +-------------+                                +-------------+
      |  Transport  |  Gathers data & attaches       |  Transport  |  Inspects port fields &
      |    Layer    |  Source & Destination Ports    |    Layer    |  routes to target socket
      +-------------+                                +-------------+
             |                                              ^
             v                                              |
      +-------------+                                +-------------+
      |Network (IP) |  Encapsulates into IP Datagram |Network (IP) |  Decapsulates IP Datagram
      |    Layer    |  (Attaches Source/Dest IPs)    |    Layer    |  passes to Transport Layer
      +-------------+                                +-------------+
             |                                              ^
             +================ (Network) ===================+
```

* **Multiplexing (Sender):** Gathering data chunks from multiple application sockets, encapsulating each with transport headers (including Source and Destination Port numbers), and handing the segments down to the Network Layer.
* **Demultiplexing (Receiver):** Inspecting header fields of incoming transport segments to direct each segment's payload to the exact corresponding socket buffer.

---

### 4. Connectionless Demultiplexing (UDP)

In UDP, a socket is identified solely by a **2-Tuple**:
$$\text{UDP Demux Key} = (\text{Destination IP Address},\; \text{Destination Port Number})$$

#### Operational Rules:
1. When Host A and Host B both send UDP datagrams to Server C on port `6428`, **both datagrams enter the exact same socket buffer** on Server C, regardless of their source IP addresses or source port numbers.
2. The server application reads the datagram using `recvfrom()`, which provides the `(Source IP, Source Port)` alongside the data.
3. **Purpose of Source Port in UDP:** The UDP header includes the Source Port so the receiving process knows where to address its **reply** packet.

```
Host A (198.51.100.1)                      Server C (203.0.113.5)
[Src: 9157, Dst: 6428] ------------------> | 
                                           | ===> [Single Shared UDP Socket on Port 6428]
Host B (198.51.100.2)                      |
[Src: 9157, Dst: 6428] ------------------> |
```

---

### 5. Connection-Oriented Demultiplexing (TCP)

In TCP, a socket is bound to a specific point-to-point connection identified by a **4-Tuple**:
$$\text{TCP Demux Key} = (\text{Source IP},\; \text{Source Port},\; \text{Destination IP},\; \text{Destination Port})$$

#### Why TCP Requires all 4 Fields:
Unlike UDP, TCP maintains rich, connection-specific state in the kernel (**Transmission Control Block - TCB**):
* Sequence numbers sent, received, and acknowledged.
* Send and receive sliding window buffers.
* Congestion window size ($cwnd$), slow-start threshold ($ssthresh$), and receive window ($rwnd$).
* Round-Trip Time ($RTT$) estimates and active retransmission timers.

If segments from different clients were delivered to the same socket, their sequence numbers, ACKs, and window states would collide and corrupt the byte stream.

---

### 6. TCP Server Socket Lifecycle: Welcoming vs. Dedicated Sockets

```
Client A (198.51.100.1)                     Web Server S (203.0.113.5)
Port: 50001 (Conn 1) ---------------------> [Socket 1: (198.51.100.1, 50001, 203.0.113.5, 80)]
Port: 50002 (Conn 2) ---------------------> [Socket 2: (198.51.100.1, 50002, 203.0.113.5, 80)]

Client B (198.51.100.2)
Port: 50001 (Conn 3) ---------------------> [Socket 3: (198.51.100.2, 50001, 203.0.113.5, 80)]
Port: 50002 (Conn 4) ---------------------> [Socket 4: (198.51.100.2, 50002, 203.0.113.5, 80)]
                                            [Welcoming Socket: (*, *, 203.0.113.5, 80)]
```

1. **The Welcoming (Listening) Socket:**
   The server binds to port 80 and executes `listen()`. It waits for incoming TCP connection requests (`SYN` packets).
2. **Accepting Connection:**
   When a `SYN` arrives, the 3-way handshake executes. Upon completion, `accept()` creates a **brand-new dedicated socket descriptor** tied specifically to that client's 4-tuple.
3. **Concurrent Processing:**
   The welcoming socket remains active on port 80 to receive new connection handshakes, while all data transfer segments are demultiplexed to their respective dedicated connection sockets (often handled in separate threads or asynchronous event loops).

---

### 7. Analytical Scenario: Collision Resistance

> [!example] Exam / Diagnostic Scenario
> **Scenario:** Host A (IP `10.0.0.1`) and Host B (IP `10.0.0.2`) both open 2 simultaneous connections to Server S (IP `10.0.0.99`) on port 80. Both happen to use ephemeral ports `55000` and `55001`.
> 
> **Question:** How many distinct sockets exist on Server S to service these connections?
> 
> **Resolution:**
> * Socket 1: `(10.0.0.1, 55000, 10.0.0.99, 80)`
> * Socket 2: `(10.0.0.1, 55001, 10.0.0.99, 80)`
> * Socket 3: `(10.0.0.2, 55000, 10.0.0.99, 80)`
> * Socket 4: `(10.0.0.2, 55001, 10.0.0.99, 80)`
> * Plus 1 welcoming socket: `(*, *, 10.0.0.99, 80)`
> 
> $\implies$ Exactly **4 dedicated connection sockets** $+$ **1 listening socket** $= \mathbf{5\text{ sockets}}$ total.

---

### Summary
> [!abstract] Multiplexing and Demultiplexing Takeaway
> - **Multiplexing** occurs at the sender (gathering data across sockets and stamping port headers); **Demultiplexing** occurs at the receiver (inspecting headers to deliver payloads into specific socket buffers).
> - **UDP Demux Key (2-Tuple):** `(Destination IP, Destination Port)`. All packets targeting that destination port share one socket.
> - **TCP Demux Key (4-Tuple):** `(Source IP, Source Port, Destination IP, Destination Port)`. Every connection has a dedicated socket holding independent connection state.
