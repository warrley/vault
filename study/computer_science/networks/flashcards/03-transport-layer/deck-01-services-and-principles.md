---
tags:
  - flashcards
  - flashcards/networks/transport/services
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: Transport Layer Services & Principles

What is the fundamental distinction between the Transport Layer and the Network Layer?::The **Network Layer** provides logical communication between **hosts** (host-to-host across intermediate routers). The **Transport Layer** provides logical communication between **application processes** running on different hosts (process-to-process via sockets).
<!--ID: 1727100001-->

In computer networking, what is meant by "logical communication" between processes?::From the application processes' perspective, they communicate as if they were directly connected by a dedicated physical pipe, completely abstracted from the underlying physical topology, intermediate routers, and link types.
<!--ID: 1727100002-->

In the Kurose household analogy for transport services, what corresponds to: Houses, Cousins, Letters, Mail Sorters (Ann/Bill), and the Postal Service?::* **Houses** = Hosts (End systems)<br>* **Cousins** = Application processes<br>* **Letters inside envelopes** = Application messages<br>* **Ann & Bill (mail sorters)** = Transport Layer protocol<br>* **Postal Service (trucks/planes)** = Network Layer (IP).
<!--ID: 1727100003-->

Where are transport-layer protocols implemented in the Internet architecture, and why?::Exclusively on **end systems (hosts)** at the network edge. Network core devices (routers and link switches) process packets strictly up to Layer 3/Layer 2 to preserve line-rate packet forwarding throughput and respect the **End-to-End Principle**.
<!--ID: 1727100004-->

What transport services can TCP guarantee on top of an unreliable, best-effort IP network?::1. **100% Reliable Data Transfer** (zero bit errors, zero loss)<br>2. **In-Order Byte Stream Delivery** (reordering recovery and duplicate suppression)<br>3. **Flow Control** (protects receiver buffer)<br>4. **Congestion Control** (protects intermediate router links).
<!--ID: 1727100005-->

What services can the Internet Transport Layer (neither TCP nor UDP) NOT guarantee?::1. **Hard Delay / Latency Bounds** (cannot guarantee delivery within $\le X\text{ ms}$)<br>2. **Bandwidth / Throughput Guarantees** (cannot reserve a dedicated transmission rate like $\ge 10\text{ Mbps}$).
<!--ID: 1727100006-->

What is the difference between TCP's data abstraction and UDP's data abstraction?::* **TCP**: Unstructured **Continuous Byte Stream** (no application message boundaries preserved by transport layer).<br>* **UDP**: Discrete **Datagrams** (message-oriented; preserves application packet boundaries 1:1).
<!--ID: 1727100007-->

What are the base header sizes of UDP vs standard TCP?::* **UDP Header**: Fixed **8 bytes** (4 fields of 16 bits each).<br>* **TCP Header**: Minimum **20 bytes** (up to 60 bytes with optional fields).
<!--ID: 1727100008-->
