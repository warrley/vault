---
tags:
  - networks/core
  - networks/switching
  - networks/kurose-ch1
parent: "[[01-introduction-to-networks]]"
---

# Concept: Circuit Switching vs. Packet Switching

## 1. The Fundamental Network Core Problem

The network core is a mesh of interconnected packet switches and communication links. To move data from an ingress interface to an egress interface across this core, two contrasting paradigms exist: **Circuit Switching** and **Packet Switching**.

```
                   Telecommunication Networks
                               │
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
  Circuit Switching                           Packet Switching
(Comutação de Circuitos)                   (Comutação de Pacotes)
   ├── FDM (Frequency)                        ├── Virtual Circuit Networks (VC)
   └── TDM (Time)                             └── Datagram Networks (Internet / IP)
```

---

## 2. Circuit Switching (*Comutação de Circuitos*)

In circuit switching (used in legacy Public Switched Telephone Networks - PSTN), an **unbroken, dedicated transmission path** is established across all intermediate switches from source to destination before data transfer can begin.

```
Host A ───► [Switch 1] ═══ (Reserved dedicated channel) ═══► [Switch 2] ───► Host B
```

### Resource Partitioning: Multiplexing Techniques
To share a single physical link among multiple concurrent circuits, the medium's capacity is partitioned:

#### A. Frequency Division Multiplexing (FDM)
* The total frequency bandwidth of the link is split into discrete, non-overlapping frequency bands.
* Each circuit is assigned an exclusive frequency band for the duration of the call (e.g., FM radio channels, cable television).
* Signals operate concurrently in the frequency domain.

#### B. Time Division Multiplexing (TDM)
* Time is sliced into periodic **frames** of fixed duration. Each frame is further divided into a fixed number of **time slots**.
* Each connection is assigned an exclusive time slot in every frame (e.g., T1 lines with 24 voice channels).

```
TDM Frame:  [ Slot 1 (User A) | Slot 2 (User B) | Slot 3 (User C) | Slot 4 (User D) ]
```

> [!tip] Professor's Question (List 1, Q13): Multiplexing outside the Transport Layer
> **Definition**: Multiplexing is combining multiple independent signals or communication streams over a single shared physical channel.
> **Examples in Physical/Link layers**:
> 1. **FDM in Radio/TV/DOCSIS**: Sharing the physical electromagnetic spectrum or coaxial cable across distinct frequency bands.
> 2. **TDM in Telephony / SONET**: Slicing time on high-speed optical links to carry multiple independent bitstreams.
> 3. **WDM (Wavelength Division Multiplexing)**: Splitting fiber optic light into distinct laser wavelengths (colors).

### The Inefficiency for Computing: Bursty Traffic
* Circuit switching reserves end-to-end capacity continuously, whether or not bits are being sent (**silent periods consume reserved bandwidth**).
* Because computer communications are inherently **bursty** (short bursts of data transfer separated by long idle reading/processing times), circuit switching leaves links idle $>90\%$ of the time.

---

## 3. Packet Switching (*Comutação de Pacotes*)

In packet switching (the Internet's architecture), data streams are broken into formatted chunks called **packets** ($L$ bits). Senders transmit packets onto links without prior reservation.

### Core Mechanics of Packet Switching

#### 1. Statistical Multiplexing (*Multiplexação Estatística*)
* Transmission link capacity ($R$ bps) is shared on demand on a packet-by-packet basis.
* Unlike TDM (where an idle user's slot is wasted), in packet switching, if a user has nothing to send, other users consume the full link capacity.

#### 2. Store-and-Forward Transmission (*Armazena e Reenvia*)
* A packet switch (router) must receive the **entire packet** ($L$ bits) into its memory buffer and verify its integrity before it can begin transmitting the first bit onto the outbound link.
* **Transmission Delay across $N$ identical links**:
  $$\text{Total Time} = N \cdot \frac{L}{R}$$

```
Source ────(Link 1: R bps)────► [ Router ] ────(Link 2: R bps)────► Destination
  [Packet L bits] ──► Router stores all L bits ──► Router forwards L bits
```

---

## 4. Datagram Networks vs. Virtual Circuit Networks

Packet switching itself is divided into two architectural models:

### A. Datagram Networks (The Internet Architecture / IP)
* **Connectionless**: No path setup phase. Packets (datagrams) are injected directly into the network.
* **Independent Routing**: Each datagram contains the complete destination IP address in its header. Routers inspect the destination address and use their local routing/forwarding tables to select the next hop.
* **Dynamic Path Selection**: If intermediate link conditions change, successive packets of the same flow may follow completely different paths.

> [!question] Professor's Question (List 2): How can two packets from the same machine to the same destination arrive out of order?
> **Answer**: In a datagram packet-switched network, routers forward each packet independently. If a routing protocol updates routes mid-stream (e.g., link cost changes or an alternate path becomes available), or if packets experience varying queuing delays along different parallel links, later packets can take a shorter/faster path and reach the destination before earlier packets. The receiving host's Transport Layer (TCP) is responsible for reordering them.

### B. Virtual Circuit Networks (VC - e.g., ATM, Frame Relay, X.25)
* **Connection-Oriented at the Network Layer**: Requires a 3-phase lifecycle: (1) Setup $\to$ (2) Data Transfer $\to$ (3) Teardown.
* Packets do not carry full destination IP addresses; they carry a short **Virtual Circuit Identifier (VCI)**.
* Every intermediate switch maintains a state table mapping `(Incoming Port, Incoming VCI) -> (Outgoing Port, Outgoing VCI)`. All packets in a session follow the exact same path in-order.

---

## 5. Core Comparison Matrix

| Architectural Dimension | Circuit Switching | Packet Switching: Datagram (IP) | Packet Switching: Virtual Circuit (ATM) |
| :--- | :--- | :--- | :--- |
| **Dedicated Path** | Yes (Physical/Logical) | No | Yes (Logical path) |
| **Dedicated Bandwidth** | Yes (Guaranteed) | No (Shared on demand) | Can support QoS guarantees |
| **Setup Phase Required** | Yes (Call setup) | **No** (Connectionless) | Yes (VC setup) |
| **Router State** | Per-circuit state | **Zero per-connection state** | Per-VC state table |
| **Addressing in Packet** | None (implicit in slot/freq) | Full Global Dest IP | Short VCI (local significance) |
| **Out-of-Order Delivery** | Impossible | **Possible** | Impossible |
| **Link Efficiency for Bursty Data** | Very Low | **Very High** | High |
| **Congestion / Loss** | Busy signal at setup | Packet loss at router buffers | Packet loss / cell discard |

---

## 6. Summary Takeaway
> [!abstract] Key Takeaway
> The Internet chose **Datagram Packet Switching** because computer traffic is bursty, making statistical multiplexing dramatically more efficient than circuit switching. The trade-off is that routers maintain no connection state, packets can arrive out of order, and congestion causes variable delays and packet loss in router buffers.
