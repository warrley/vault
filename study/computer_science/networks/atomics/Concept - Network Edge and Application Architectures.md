---
tags:
  - networks/edge
  - networks/architecture
  - networks/kurose-ch1
parent: "[[01-introduction-to-networks]]"
---

# Concept: Network Edge and Application Architectures

## 1. The Structure of the Network Edge (*Borda da Rede*)

The Internet is conceptually divided into the **network edge** (*borda*) and the **network core** (*núcleo*).

### What Resides at the Edge?
The edge consists of **hosts / end systems (*sistemas finais*)**:
* Traditional computing hardware: Desktops, laptops, virtual machines, database servers, and web servers.
* Modern interconnected endpoints: Smartphones, smart home appliances, IoT sensors, automobiles, and industrial PLCs.
* **Network Boundary**: End systems connect to the network via **edge routers** (*roteadores de borda*) through access networks (FTTH optical fiber, DSL, Cable, 4G/5G, or Wi-Fi).

---

## 2. The Fundamental Principle: Dumb Core, Smart Edge

> [!important] The "End-to-End" Architectural Principle
> In the Internet architecture, **application programs run strictly on end systems at the network edge**, never on the intermediate packet switches and routers of the network core.

```
       [Host A: Web Browser]                          [Host B: Web Server]
       ┌────────────────────┐                          ┌──────────────────┐
       │ Application (HTTP) │                          │Application (HTTP)│
       ├────────────────────┤                          ├──────────────────┤
       │ Transport   (TCP)  │                          │Transport   (TCP) │
       ├────────────────────┤   [Core Router]          ├──────────────────┤
       │ Network     (IP)   │ ──► [Layer 1-3] ──► ... ──►Network     (IP) │
       └────────────────────┘   (No App logic)         └──────────────────┘
```

### Why Is Application Logic Excluded from the Core? (Exercise Focus)
1. **Speed & Scalability**: Core routers process hundreds of millions of packets per second. If routers had to parse application payloads (such as verifying HTTP headers or parsing JSON), router latency would skyrocket, causing massive bottlenecks.
2. **Protocol Agnosticism & Rapid Innovation**: Because the network core only transports generic IP datagrams without caring about what application created them, developers can invent and deploy brand-new application protocols (e.g., HTTP/3, WebRTC, Zoom, BitTorrent) without requiring any hardware upgrades or permission from ISPs or router manufacturers.

---

## 3. Distributed Application Paradigms

Applications distributed across multiple hosts organize their communication into two primary paradigms:

### A. The Client-Server Paradigm

```
                   ┌───────────────────────────────┐
                   │   Always-on Server (Host)     │
                   │   - Permanent / Fixed IP      │
                   │   - Clustered in Datacenters  │
                   └───────┬───────────────┬───────┘
                           │               │
                 Request   │               │   Request
                 & Response│               │   & Response
                           ▼               ▼
                   ┌──────────────┐ ┌──────────────┐
                   │   Client A   │ │   Client B   │
                   │ (Dynamic IP) │ │ (Dynamic IP) │
                   └──────────────┘ └──────────────┘
```

* **Server Role**:
  * An always-on host listening on a well-known port (e.g., port 80 for HTTP, port 443 for HTTPS).
  * Has a known, stable IP address or domain name.
  * Scales by placing farms of servers behind load balancers inside datacenters.
* **Client Role**:
  * Initiates communication with the server.
  * May have dynamic, changing IP addresses (e.g., moving between Wi-Fi and mobile data).
  * Clients **never communicate directly with other clients**.
* **Trade-offs**:
  * *Advantages*: Centralized control, easy data consistency, centralized security auditing, predictable resource accounting.
  * *Disadvantages*: High infrastructure cost; server is a **single point of failure** and a severe performance bottleneck during peak load (slashdot effect / flash crowds).

---

### B. The Peer-to-Peer (P2P) Paradigm

```
             ┌──────────┐                     ┌──────────┐
             │  Peer A  │◄───────────────────►│  Peer B  │
             └────┬─────┘                     └─────┬────┘
                  │                                 │
                  │         Direct Transfer         │
                  └───────────────►◄────────────────┘
                                   │
                              ┌────▼─────┐
                              │  Peer C  │
                              └──────────┘
```

* **Mechanism**: Arbitrary pairs of hosts (called **peers**) communicate directly with one another.
* **Self-Scalability (*Autoescalabilidade*)**: In a P2P file-sharing network, every peer that downloads a file also uploads chunks of that file to other peers. As demand grows, capacity grows automatically.
* **Trade-offs**:
  * *Advantages*: Minimal server infrastructure cost, massive aggregate bandwidth, highly resilient against single-node outages.
  * *Disadvantages*:
    * **Peer Churn**: Peers join, disconnect, and change IP addresses unpredictably.
    * **Complex Coordination**: Finding which peer holds what content requires distributed search protocols.
    * **ISP Uplink Strain**: Heavy asymmetric traffic on residential upload links.

#### Pure P2P vs. Hybrid P2P (Exam Focus)

| Feature | Pure P2P (e.g., Gnutella, Kademlia/DHT) | Hybrid P2P (e.g., Napster, BitTorrent Trackers, Early Skype) |
| :--- | :--- | :--- |
| **Central Server** | **Zero** central servers. | Central servers exist **only for indexing/directory services**. |
| **Content Discovery** | Distributed queries (Query Flooding or Distributed Hash Tables). | Client queries central server: *"Who has file X?"* $\to$ Server returns peer IP list. |
| **Data Transfer** | Direct peer-to-peer. | Direct peer-to-peer. |
| **Vulnerability** | Immune to central shutdown. | Shutting down the central index server halts searches even if peers hold the files. |

---

## 4. Summary Takeaway
> [!abstract] Key Takeaway
> Applications live exclusively on **hosts at the network edge** to keep the network core fast, stateless, and protocol-agnostic. **Client-Server** centralizes control and cost on dedicated servers, while **P2P** distributes upload burden across end users, introducing churn and distributed lookup complexity.
