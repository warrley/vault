---
tags:
  - flashcards
  - flashcards/networks/transport/pipelining
  - networks/transport-layer
  - ufc/computer-networks
parent: "[[03-transport-layer]]"
---

# Flashcards: Pipelined RDT (GBN, Selective Repeat & TCP Hybrid)

Why does the Stop-and-Wait protocol achieve poor link utilization over high-speed links?::Because the sender spends $>99.9\%$ of its time idle waiting for propagation delay over the Round-Trip Time ($RTT$). Sender utilization is bounded by $U_{\text{sender}} = \frac{d_{\text{trans}}}{RTT + d_{\text{trans}}}$.
<!--ID: 1727500001-->

Calculate the sender utilization for Stop-and-Wait on a $1\text{ Gbps}$ link with $RTT = 30\text{ ms}$ and packet size $L = 1000\text{ bytes}$ ($8000\text{ bits}$).::$d_{\text{trans}} = \frac{8000\text{ bits}}{10^9\text{ bps}} = 0.008\text{ ms}$.<br>$U = \frac{0.008\text{ ms}}{30.008\text{ ms}} \approx \mathbf{0.027\%}$ (The link is idle $99.97\%$ of the time).
<!--ID: 1727500002-->

How does Pipelining (Sliding Windows) solve the stop-and-wait utilization bottleneck?::By allowing the sender to transmit up to **$N$ consecutive packets** without waiting for acknowledgments, increasing utilization by a factor of $N$: $U_{\text{pipelined}} = \min\left(1, \; N \cdot \frac{d_{\text{trans}}}{RTT + d_{\text{trans}}}\right)$.
<!--ID: 1727500003-->

How does a Go-Back-N (GBN) receiver handle an out-of-order packet?::The GBN receiver **discards the packet completely** (maintains zero receive buffer memory) and resends a cumulative ACK for the highest sequence number received in-order.
<!--ID: 1727500004-->

What action does a Go-Back-N sender take when its retransmission timer expires?::The sender **retransmits ALL $N$ unacknowledged packets** currently in its window, starting from `send_base`, even if some of those packets were originally received correctly by the other side.
<!--ID: 1727500005-->

How does Selective Repeat (SR) differ from Go-Back-N in terms of ACKs, timers, and receiver buffering?::* **Selective Repeat**:
  - Uses **Individual ACKs** for every received packet.
  - Maintains **Individual timers** per packet.
  - **Buffers out-of-order packets** in receiver memory.
  - On timeout, retransmits **ONLY the single lost packet**.<br>* **Go-Back-N**:
  - Uses **Cumulative ACKs**.
  - Maintains a **Single timer** for `send_base`.
  - **Discards out-of-order packets** (no buffer).
  - On timeout, retransmits **ALL $N$ unACKed packets**.
<!--ID: 1727500006-->

Why is real-world TCP classified as a hybrid between Go-Back-N and Selective Repeat?::* **Like GBN**: TCP uses **Cumulative ACKs** and a single retransmission timer for the oldest unacknowledged segment.<br>* **Like SR**: Modern TCP implementations **buffer correctly received out-of-order segments** in memory and retransmit only the missing segment upon loss detection.
<!--ID: 1727500007-->

What is Fast Retransmit in TCP and what triggers it?::The sender retransmits a missing segment **immediately without waiting for the retransmission timer ($RTO$) to expire**, triggered by the arrival of **3 Duplicate ACKs** (4 identical cumulative ACKs total).
<!--ID: 1727500008-->

Why are 3 Duplicate ACKs required to trigger Fast Retransmit instead of just 1 Duplicate ACK?::Because a single duplicate ACK can be caused by minor packet reordering in intermediate router paths. Receiving 3 duplicate ACKs indicates that 3 subsequent packets have arrived safely, making packet loss highly probable rather than simple reordering.
<!--ID: 1727500009-->
