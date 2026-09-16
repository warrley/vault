---
tags:
  - networks/encapsulation
  - networks/mechanisms
  - networks/kurose-ch1
parent: "[[01-introduction-to-networks]]"
---

# Mechanism: Encapsulation and Decapsulation

## 1. The Encapsulation Lifecycle (Down the Stack at Sender)

When an application on **Host A** sends data to **Host B**, the data travels down through each layer of the protocol stack. At each step, the protocol prepends its own control metadata (**Header**) and sometimes appends an error-checking **Trailer**:

```
[ Application Layer ]
      │  Payload: Application Message (M)
      ▼
[ Transport Layer ]
      │  Adds Transport Header H_t (Source Port, Dest Port, Sequence Number, Checksum)
      │  PDU: Segment = [ H_t | M ]
      ▼
[ Network Layer ]
      │  Adds Network Header H_n (Source IP, Dest IP, TTL, Protocol ID)
      │  PDU: Datagram = [ H_n | H_t | M ]
      ▼
[ Link Layer ]
      │  Adds Link Header H_l (Source MAC, Dest MAC, EtherType) + Trailer T_l (CRC Checksum)
      │  PDU: Frame = [ H_l | H_n | H_t | M | T_l ]
      ▼
[ Physical Layer ]
         Converts Frame bytes into physical serial bitstream (01101001...) onto medium.
```

---

## 2. Packet Traversal Through Network Devices (Exam Critical)

How do intermediate devices along the physical path process these encapsulated packets?

```
   Source Host                 Ethernet Switch                  Intermediate Router                  Destination Host
┌──────────────────┐                                                                               ┌──────────────────┐
│ 5. Application   │                                                                               │ 5. Application   │
├──────────────────┤                                                                               ├──────────────────┤
│ 4. Transport     │                                                                               │ 4. Transport     │
├──────────────────┤                                             ┌──────────────────┐              ├──────────────────┤
│ 3. Network       │                                             │ 3. Network (IP)  │              │ 3. Network       │
├──────────────────┤          ┌──────────────────┐               ├──────────────────┤              ├──────────────────┤
│ 2. Link          │ ───────► │ 2. Link (MAC)    │ ────────────► │ 2. Link (MAC)    │ ───────────► │ 2. Link          │
├──────────────────┤          ├──────────────────┤               ├──────────────────┤              ├──────────────────┤
│ 1. Physical      │          │ 1. Physical      │               │ 1. Physical      │              │ 1. Physical      │
└──────────────────┘          └──────────────────┘               └──────────────────┘              └──────────────────┘
   Encapsulates                  Inspects L2 Frame                 Decapsulates L2 Frame             Decapsulates L2
   L5 -> L4 -> L3 -> L2          Forwards via MAC                  Inspects L3 IP Header             Decapsulates L3
                                 (Leaves L3/L4 intact)             Re-encapsulates NEW L2 Frame      Decapsulates L4
                                                                                                     Passes L5 Message to App
```

---

## 3. Deep Dive on Intermediate Processing

### A. Link-Layer Switches (*Comutadores de Camada de Enlace*)
* **Operating Depth**: **Layer 2 (Data Link Layer)**.
* **Mechanism**:
  1. A switch reads the incoming frame header ($H_l$).
  2. It looks up the destination MAC address in its internal MAC switching table (*tabela de encaminhamento de enlace*).
  3. It forwards the frame directly out the specific output port connected to that destination MAC.
* **Key Fact**: The switch **never inspects or modifies** the Layer 3 IP header ($H_n$) or Layer 4 transport payload ($H_t | M$). To the IP layer, the switch is completely invisible (transparent).

---

### B. Routers (*Roteadores*)
* **Operating Depth**: **Layer 3 (Network Layer)**.
* **Mechanism**:
  1. **Layer 2 Decapsulation**: The router receives the incoming physical frame and strips off the Layer 2 header ($H_l$) and trailer ($T_l$).
  2. **Layer 3 Inspection**: The router inspects the destination IP address in the IP header ($H_n$).
  3. **Routing Decision**: It checks its IP routing/forwarding table to select the outgoing interface and next-hop IP.
  4. **Header Updates**: It decrements the IPv4 **TTL (Time to Live)** field by 1 and recomputes the IP header checksum.
  5. **Layer 2 Re-encapsulation**: It creates a **brand-new Layer 2 frame header ($H_l'$)** matching the specific physical link technology of the outbound link (e.g., if the outgoing link is Point-to-Point Protocol or Wi-Fi, it encapsulates the IP datagram into a PPP or 802.11 frame).

> [!question] Professor's Question (List 3): Does the link-layer header change during packet transmission across the Internet?
> **Answer**: **YES**. While the Layer 3 IP header ($H_n$) remains preserved end-to-end (from Source IP to Destination IP), the Layer 2 Link header ($H_l$) is local to each physical link segment. Every time a packet crosses a router, the old Link header is discarded and a new Link header with new Source/Destination MAC addresses is attached for the next hop.

---

### C. Hubs vs. Switches vs. Routers Comparison (Exercise List 3 Focus)

| Hardware Device | OSI/TCP-IP Layer | Addressing Used | Forwards Based On | Collision Domain Isolation | Broadcast Domain Isolation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hub / Repetidor** | **Layer 1 (Physical)** | None (raw bits) | Broadcasts all bits out all ports | **No** (All ports share 1 collision domain) | **No** (1 broadcast domain) |
| **Switch (Comutador)** | **Layer 2 (Data Link)** | MAC Address (48-bit) | Hardware MAC Table | **YES** (Each switch port is an isolated collision domain) | **No** (All ports share 1 broadcast domain) |
| **Router (Roteador)** | **Layer 3 (Network)** | IP Address (32/128-bit) | IP Routing Table | **YES** (Isolates collision domains) | **YES** (Isolates broadcast domains per subnet) |

---

## 4. Summary Takeaway
> [!abstract] Key Encapsulation Takeaway
> * **Encapsulation**: $M \xrightarrow{\text{L4}} \text{Segment}[H_t|M] \xrightarrow{\text{L3}} \text{Datagram}[H_n|H_t|M] \xrightarrow{\text{L2}} \text{Frame}[H_l|H_n|H_t|M|T_l]$.
> * Switches forward at Layer 2 (MAC). Routers strip and rewrite Layer 2 headers to route datagrams at Layer 3 (IP). Hosts process all 5 layers up to application sockets.
