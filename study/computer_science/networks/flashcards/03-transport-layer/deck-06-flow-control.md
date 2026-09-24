---
tags:
  - flashcards
  - flashcards/networks/transport/flow-control
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: TCP Flow Control & Buffer Management

What is the fundamental objective of Flow Control in TCP?::To provide an end-to-end speed-matching mechanism that prevents a fast sender from overflowing the allocated memory buffer (`RcvBuffer`) of a slower receiving application.
<!--ID: 1727600001-->

What is the difference between Flow Control and Congestion Control?::* **Flow Control**: Protects the **specific receiver's socket buffer** from being overwhelmed by a fast sender.<br>* **Congestion Control**: Protects the **intermediate routers and shared network links** across the Internet core from being overwhelmed by aggregate traffic from all sending hosts.
<!--ID: 1727600002-->

What is the mathematical formula used by a TCP receiver to calculate its Receive Window ($rwnd$)?::$rwnd = \text{RcvBuffer} - (\text{LastByteRcvd} - \text{LastByteRead})$.
<!--ID: 1727600003-->

What inequality does the TCP sender enforce to respect the receiver's advertised flow control window?::$\mathbf{\text{LastByteSent} - \text{LastByteAcked} \le rwnd}$.
<!--ID: 1727600004-->

A TCP receiver allocates `RcvBuffer` $= 80,000\text{ bytes}$. The receiving application has read up to byte $25,000$ (`LastByteRead`), and segments have arrived up to byte $65,000$ (`LastByteRcvd`). What is the advertised $rwnd$?::* $\text{Occupied Space} = 65,000 - 25,000 = 40,000\text{ bytes}$.<br>* $rwnd = 80,000 - 40,000 = \mathbf{40,000\text{ bytes}}$.
<!--ID: 1727600005-->

What is the Zero-Window Deadlock in TCP, and what causes it?::When the receiver buffer fills up, it advertises $rwnd = 0$, causing the sender to pause. Later, the receiving application consumes all buffered data, emptying the buffer. If the receiver has no outbound data to send, it will not generate any segment, so the sender never learns that $rwnd > 0$, causing both hosts to wait forever in a deadlock.
<!--ID: 1727600006-->

How does TCP resolve the Zero-Window Deadlock?::The sender starts a **persist timer** when $rwnd = 0$. When the timer expires, the sender transmits a **Probe Segment carrying $1\text{ byte}$ of dummy data**, forcing the receiver to reply with an ACK segment that carries its updated, non-zero $rwnd$.
<!--ID: 1727600007-->
