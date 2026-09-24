---
tags:
  - flashcards
  - flashcards/networks/transport/tcp-core
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: TCP Segment Structure & Connection Lifecycle

What is the size of the base TCP header, and how does the `HLEN` (Header Length) field encode it?::The base TCP header is **$20\text{ bytes}$** (up to $60\text{ bytes}$ with options). The `HLEN` (Data Offset) field is a **4-bit field** specifying header length in units of **$32\text{-bit}$ ($4\text{-byte}$) words**. For a standard 20-byte header, $\text{HLEN} = 5$ ($5 \times 4 = 20\text{ bytes}$).
<!--ID: 1727400001-->

What does a TCP Sequence Number represent, and how does it differ from a packet sequence number?::A TCP Sequence Number represents the **byte-stream index of the first data byte** contained within that specific segment (counting individual bytes of unstructured data, not discrete packet numbers).
<!--ID: 1727400002-->

What does a TCP Acknowledgment (ACK) Number represent?::The sequence number of the **next byte expected from the peer**. TCP acknowledgments are **cumulative**, meaning $\text{ACK} = K$ confirms that all bytes from $0$ up to $K - 1$ have been received correctly.
<!--ID: 1727400003-->

What are the 6 standard TCP flag bits and their functions?::1. **`SYN`**: Synchronizes initial sequence numbers during connection establishment.<br>2. **`FIN`**: Signals that the sender has finished transmitting data (graceful teardown).<br>3. **`ACK`**: Confirms that the Acknowledgment Number field is valid.<br>4. **`RST`**: Abruptly resets/aborts a connection (e.g. port closed or connection corrupted).<br>5. **`PSH`**: Instructs receiver to push data immediately to the application layer.<br>6. **`URG`**: Indicates that urgent data exists at the offset specified by the Urgent Pointer.
<!--ID: 1727400004-->

What is Piggybacking in TCP?::The mechanism of combining an **acknowledgment (ACK)** of received data and **outbound application payload data** inside the exact same TCP segment (e.g., Telnet server echoing a typed character while simultaneously ACKing the client's keystroke).
<!--ID: 1727400005-->

What are the 3 steps of the TCP Connection Establishment Handshake?::1. **Client $\to$ Server (`SYN`)**: `SYN = 1`, `Seq = client_isn`, `ACK = 0`.<br>2. **Server $\to$ Client (`SYN-ACK`)**: `SYN = 1`, `ACK = 1`, `Seq = server_isn`, `Ack_Num = client_isn + 1`. Server allocates TCB state and buffers.<br>3. **Client $\to$ Server (`ACK`)**: `ACK = 1`, `Seq = client_isn + 1`, `Ack_Num = server_isn + 1`. Connection enters `ESTABLISHED` and may carry application data.
<!--ID: 1727400006-->

Why is TCP connection teardown a 4-way handshake rather than a 3-way handshake?::Because TCP is **full-duplex**. Each transmission direction must be closed independently:
1. Client sends `FIN` ($\text{seq} = u$) $\to$ Server replies with `ACK` ($\text{ack} = u + 1$). (Client enters `FIN_WAIT_2`, server can still send pending data).
2. Server finishes its transmissions and sends its own `FIN` ($\text{seq} = v$) $\to$ Client replies with `ACK` ($\text{ack} = v + 1$).
<!--ID: 1727400007-->

What is the purpose of the `TIME_WAIT` state at the end of a TCP connection?::The host that initiated active close remains in `TIME_WAIT` for **$2 \times \text{MSL}$ (Maximum Segment Lifetime, $\approx 60-120\text{ seconds}$)** to:
1. Allow enough time to retransmit the final `ACK` if it was lost, preventing the peer from getting stuck in `LAST_ACK`.
2. Ensure all duplicate/stray packets from this connection expire in intermediate routers before the same port tuple is reused.
<!--ID: 1727400008-->

Host A sends a TCP segment with $\text{Seq} = 500$ carrying $200\text{ bytes}$ of payload data. What is the value in the ACK field sent back by Host B upon correct receipt?::**$\text{ACK} = 700$** (The segment carries bytes $500$ through $699$; the next expected byte is $500 + 200 = 700$).
<!--ID: 1727400009-->
