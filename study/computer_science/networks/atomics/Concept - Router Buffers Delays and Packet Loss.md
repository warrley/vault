---
tags:
  - networks/performance
  - networks/delays
  - networks/kurose-ch1
parent: "[[01-introduction-to-networks]]"
---

# Concept: Router Buffers, Delays, and Packet Loss

## 1. The Anatomy of Total Nodal Delay ($d_{\text{nodal}}$)

As a packet travels from router to router across the Internet core, it experiences four distinct delays at each intermediate node:

$$d_{\text{nodal}} = d_{\text{proc}} + d_{\text{queue}} + d_{\text{trans}} + d_{\text{prop}}$$

```
Incoming Link ──► [ 1. Processing (d_proc) ]
                          │
                          ▼
                  [ 2. Queuing Buffer (d_queue) ] ──► [ 3. Transmission (d_trans) ] ──► (Physical Medium) ──► [ 4. Propagation (d_prop) ] ──► Next Router
                  [ █ █ █ █ █ _ _ ]                    (Pushes L bits at rate R)                               (Travels d meters at speed s)
```

---

### 1. Processing Delay ($d_{\text{proc}}$)
* **What happens**: The router checks the packet header for bit-level transmission errors (checksum), inspects the destination IP address, and consults its forwarding table to select the outgoing interface.
* **Characteristics**: Typically microseconds ($\mu\text{s}$) or fractions thereof on modern high-speed ASICs.

### 2. Queuing Delay ($d_{\text{queue}}$)
* **What happens**: After the forwarding decision is made, the packet enters the queue buffer of the designated outbound interface. It must wait until preceding packets in the buffer are transmitted.
* **Characteristics**: Highly variable. Depends entirely on current network load and congestion:
  $$\text{Traffic Intensity} = \frac{L \cdot a}{R}$$
  *(where $L = \text{packet size in bits}$, $a = \text{average packet arrival rate}$, $R = \text{transmission rate in bps}$)*
  * If $\frac{L \cdot a}{R} \approx 0$: Average queuing delay is virtually zero.
  * If $\frac{L \cdot a}{R} \to 1$: Queuing delay increases dramatically.
  * If $\frac{L \cdot a}{R} > 1$: Arrival rate exceeds departure rate; queues grow without bound until buffers fill up.

### 3. Transmission Delay ($d_{\text{trans}}$)
* **What happens**: The time required for the router's physical hardware interface to push (serialize) all $L$ bits of the packet onto the transmission link operating at rate $R$ bits/second.
$$d_{\text{trans}} = \frac{L}{R}$$
* **Key Insight**: Depends **only** on packet length $L$ and link capacity $R$. It is completely independent of the physical length of the cable!

### 4. Propagation Delay ($d_{\text{prop}}$)
* **What happens**: The time it takes for a single physical bit (voltage transition, optical pulse, or radio wave) to physically travel from the beginning of the link to the end of the link over distance $d$.
$$d_{\text{prop}} = \frac{d}{s}$$
* **Key Insight**: Depends **only** on physical distance $d$ and propagation speed in the medium $s$ ($s \approx 2 \times 10^8\text{ m/s}$ in copper and fiber, $\approx 3 \times 10^8\text{ m/s}$ in vacuum/air). It is completely independent of packet size $L$ or transmission rate $R$.

---

## 2. Intuitive Contrast: Transmission vs. Propagation

```
  [ Tollbooth A ] ══════════════════════════════════════════════════════════► [ Tollbooth B ]
   (10 cars in caravan)                     Highway (100 km)
```

* **Transmission Delay**: The time it takes the tollbooth attendant to service all 10 cars and push them onto the highway.
* **Propagation Delay**: The time it takes a car already on the road to drive 100 km across the highway to reach Tollbooth B.

---

## 3. Router Buffers and Packet Loss (*Perda de Pacotes*)

```
Incoming Traffic (Rate a) ──► [  █  █  █  █  █  █  █  ] ──► Outgoing Link (Rate R)
                              ▲
                              └─ Buffer is FULL: Newly arriving packets are DISCARDED (Dropped)
```

* **Finite Buffering**: Routers have finite physical memory allocated for packet buffers.
* **Overflow Condition**: When the buffer queue is completely full, a newly arriving packet cannot be stored.
* **The Discard Action**: The router simply drops the packet (**packet loss / *descarte de pacotes***).
* **End-to-End Recovery**: The core network does not inform the sender or attempt to recover the packet. Recovery is left to the **Transport Layer at the End Systems**:
  * If using **TCP**: TCP detects loss via missing ACKs or timeouts and retransmits the lost segment.
  * If using **UDP**: The application simply loses the data (acceptable for real-time voice/video frames).

---

## 4. How `traceroute` Measures Delays (Exercise List 2 Focus)
* The `traceroute` utility determines the path and measured round-trip time (RTT) to each intermediate router between source and destination.
* **Mechanism**: It sends packets with incrementing **TTL (Time to Live)** values in the IP header:
  1. Packet with $\text{TTL} = 1 \to$ First router decrements TTL to 0, discards packet, and sends back an `ICMP Time Exceeded` message.
  2. Packet with $\text{TTL} = 2 \to$ Second router decrements TTL to 0 and returns `ICMP Time Exceeded`.
  3. Repeats until the packet reaches the destination host.
* The elapsed time between sending the probe and receiving the ICMP reply gives the round-trip nodal delay to that specific hop.

---

## 5. Delay Summary
> [!abstract] Key Takeaway
> * Total nodal delay: $d_{\text{nodal}} = d_{\text{proc}} + d_{\text{queue}} + \frac{L}{R} + \frac{d}{s}$.
> * **$L/R$** is serializing bits onto the wire; **$d/s$** is the physical signal traveling through space.
> * When router queues saturate ($\frac{L \cdot a}{R} > 1$), incoming packets are dropped.
