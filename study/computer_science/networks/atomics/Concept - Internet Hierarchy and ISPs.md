---
tags:
  - networks/topology
  - networks/isp
parent: "[[01-introduction-to-networks]]"
---

# Concept: Internet Hierarchy, ISPs, Transit, and Peering

## 1. The Structure: A Network of Networks
The Internet is not a single centrally managed network; it is a global interconnection of tens of thousands of privately and publicly owned **Autonomous Systems (AS)** and **Internet Service Providers (ISPs)** organized in a loose commercial hierarchy.

```
                         ┌─────────────────────────────┐
                         │      Tier-1 ISP Backbone    │◄── Settlement-Free Peering ──►┌─────────────────────────────┐
                         │     (Lumen, AT&T, Telia)    │                               │      Tier-1 ISP Backbone    │
                         └──────────────┬──────────────┘                               └──────────────┬──────────────┘
                                        │                                                             │
                           Provider-Customer (Paid Transit)                              Provider-Customer (Paid Transit)
                                        │                                                             │
                                        ▼                                                             ▼
                         ┌─────────────────────────────┐   IXP / Peering Link          ┌─────────────────────────────┐
                         │     Tier-2 Regional ISP     │◄─────────────────────────────►│     Tier-2 Regional ISP     │
                         │      (Claro, Vivo, etc.)    │   (Settlement-Free Peering)   │        (Embratel, etc.)     │
                         └──────────────┬──────────────┘                               └──────────────┬──────────────┘
                                        │                                                             │
                           Provider-Customer (Paid Transit)                              Provider-Customer (Paid Transit)
                                        │                                                             │
                                        ▼                                                             ▼
                         ┌─────────────────────────────┐                               ┌─────────────────────────────┐
                         │       Access / Local ISP    │                               │       Campus Network        │
                         │    (Brisanet, Desktop, etc) │                               │        (e.g., UFC)          │
                         └──────────────┬──────────────┘                               └──────────────┬──────────────┘
                                        │                                                             │
                                        ▼                                                             ▼
                                   [ End Hosts ]                                                 [ End Hosts ]
```

---

## 2. The Hierarchy Tiers

### A. Tier-1 ISPs (Global Backbones)
* Global transit providers with massive high-speed fiber-optic backbones spanning multiple continents and submarine ocean cables.
* **The Defining Property**: **Tier-1 ISPs pay zero transit fees to anyone.** They have full global reach solely by interconnecting with all other Tier-1 ISPs via **settlement-free peering**.
* *Examples*: Lumen (formerly Level 3 / CenturyLink), AT&T, NTT Communications, Telia Carrier (Arelion), Tata Communications, Orange, Sprint.

### B. Tier-2 ISPs (Regional / National ISPs)
* Regional or national network operators that cover specific countries or geographical zones (e.g., Claro, Vivo, Embratel).
* Customers of Tier-1 ISPs (they pay Tier-1 providers for global Internet transit).
* They often peer with other Tier-2 ISPs directly to avoid paying Tier-1 transit fees for regional traffic.

### C. Access ISPs (Local Providers & Institutions)
* The "last mile" networks providing connectivity to homes, businesses, and universities (e.g., local fiber providers like Brisanet, or institutional networks like UFC).
* Pay upstream Tier-2 or Tier-1 providers for global Internet access.

---

## 3. Commercial Agreements: IP Transit vs. Peering

```
           CUSTOMER-PROVIDER (IP TRANSIT)                          PEERING (SETTLEMENT-FREE)
               +-------------------+                                  +-------------------+
               |   Provider ISP    |                                  |       ISP A       |
               +---------+---------+                                  +---------+---------+
                         | $$$ (Monthly recurring $/Mbps)                       |  $0 (No money changes hands)
                         |                                                      |  "Symmetric mutual benefit"
                         v                                                      v
               +---------+---------+                                  +---------+---------+
               |   Customer ISP    |                                  |       ISP B       |
               +-------------------+                                  +-------------------+
     Provider sells access to the ENTIRE INTERNET.             ISPs ONLY exchange traffic destined for
                                                               EACH OTHER's direct customers.
```

### A. IP Transit (The Paid Commercial Service)
* **Contract**: A customer network pays an upstream provider recurring fees based on capacity (typically $95^{\text{th}}$ percentile bandwidth billing).
* **Scope**: The upstream provider guarantees to route traffic from the customer to **any routable IP prefix in the entire global Internet** (the "Default-Free Zone") and deliver incoming packets back to the customer.
* **BGP Routing Behavior**: The provider advertises the customer's IP prefixes to the global BGP routing table and supplies the customer with either a full BGP routing table (~$950{,}000$ IPv4 routes) or a default route ($0.0.0.0/0$).

### B. Settlement-Free Peering (The Direct Mutual Exchange)
* **Contract**: Two ISPs (often of comparable traffic volume, geographic scale, and customer count) agree to link directly **without paying each other**.
* **The Golden Peering Invariant**:
  $$\text{An ISP NEVER routes third-party transit traffic across a settlement-free peering link.}$$
  * If ISP A peers with ISP B:
    * ISP A will **only** send traffic destined for ISP B's own network and ISP B's direct paying customers.
    * ISP A will **never** announce routes learned from its upstream transit providers or other peering partners to ISP B.
* **Economic & Technical Benefits**:
  1. **Cost Elimination**: Traffic exchanged over peering links bypasses expensive upstream transit links.
  2. **Latency Reduction**: Direct physical interconnection bypasses multiple intermediate router hops, reducing propagation ($d_{\text{prop}}$) and queuing ($d_{\text{queue}}$) delays.

---

## 4. Physical Interconnection Entities: PoPs, IXPs, and PNIs

### A. Point of Presence (PoP) & Private Network Interconnect (PNI)
* **Point of Presence (PoP)**: A physical location (usually a colocation data center like Equinix or Ascenty) where an ISP deploys a cluster of core and edge routers.
* **Private Network Interconnect (PNI)**: When two networks exchange immense volumes of data (e.g., Netflix sending $100\text{ Gbps}$ directly into an Access ISP), they order a dedicated physical fiber cable (**Cross-Connect**) inside the datacenter directly linking router interfaces.

### B. Internet Exchange Point (IXP / PTT - Ponto de Troca de Tráfego)
* An **IXP** is a shared physical switching facility (a large multi-tenant Layer-2 Ethernet switching fabric).
* **How it operates**:
  * Instead of running dozens of individual cables to dozens of networks, an ISP connects **one** high-speed optical port (e.g., $100\text{ Gbps}$) into the IXP switch matrix.
  * Through that single port, the ISP can peer with **hundreds of distinct networks** connected to that same IXP fabric.
* **Route Servers**: IXPs provide centralized BGP Route Servers. Instead of configuring separate bilateral BGP sessions with every member, an ISP connects to the IXP Route Server (**Multilateral Peering**), instantly exchanging routes with all participants.
* *Example*: **IX.br** in Brazil is one of the largest IXP ecosystems in the world (with major hubs in São Paulo, Fortaleza, Rio de Janeiro).

---

## 5. Hot-Potato Routing (*Roteamento Batata-Quente*)

When two large transit or peering networks span across continents, an economic routing behavior known as **Hot-Potato Routing** emerges:

```
                       ISP A Network (Origin)
       [ Origin Host ] ──► [ Router A1 ] ═════════════════════► [ Router A2 ] (New York)
       (Los Angeles)              │                                      │
                                  │ (Handoff immediately)                │
                                  ▼                                      ▼
                             [ Router B1 ] ═════════════════════► [ Router B2 ] ──► [ Destination Host ]
                             (Los Angeles)                          (New York)
                                            ISP B Network (Destination)
```

* **The Problem**: Carrying traffic across long continental distances consumes expensive internal fiber bandwidth and router switching capacity.
* **The Mechanism**: When an ISP receives a packet from a customer destined for an external AS, its internal routing protocol (OSPF/IS-IS) directs the packet to the **physically closest exit router (egress point)** connecting to the neighbor ISP.
* **The Consequence**: The origin ISP rids itself of the packet as fast as possible (like a "hot potato"), forcing the receiving neighbor ISP to bear the cost and distance of long-haul continental transport.

---

## 6. Content Provider Networks (The Modern Disruptor)

Tech giants (Google, Meta, Netflix, Microsoft, Amazon, Cloudflare) have transformed the traditional ISP hierarchy:
* Rather than paying billions to Tier-1 ISPs, they built their own **Private Global Optical Networks**.
* They place **Content Delivery Network (CDN) edge cache servers** directly inside local Access ISP datacenters and at regional IXPs.
* **Result**: When an end user in Quixadá requests a YouTube video or Netflix movie, the request is served directly from a local edge cache hosted at an IXP or local provider, completely bypassing Tier-1 transit links and transatlantic cables.

---

## 7. Hierarchy Summary
> [!abstract] Hierarchy Takeaway
> The global Internet is structured hierarchically: **Local/Access ISPs $\to$ Tier-2 Regional ISPs $\to$ Tier-1 Global Backbones**. Commercial agreements dictate traffic flow:
> * **Transit**: Paid contract providing reachability to the entire global Internet ($0.0.0.0/0$).
> * **Peering**: Settlement-free direct exchange of customer-only traffic at **PoPs** or **IXPs**.
> * **Hot-Potato Routing**: Egressing inter-domain packets at the nearest boundary router to minimize internal backbone costs.

