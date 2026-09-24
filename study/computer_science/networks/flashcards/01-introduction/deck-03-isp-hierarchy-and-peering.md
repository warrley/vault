---
tags:
  - flashcards
  - flashcards/networks/intro/isp-topology
  - networks/fundamentals
  - ufc/computer-networks
parent: "[[01-introduction-to-networks]]"
---

# Flashcards: Global Internet Topology & ISP Hierarchy

What are the 3 tiers of the global Internet ISP hierarchy?::1. **Tier-1 ISPs**: Global backbone operators (e.g., Lumen, AT&T, NTT) that treat the entire Internet as peers with no upstream transit provider.<br>2. **Tier-2 / Regional ISPs**: Cover regional/national geography; purchase transit from Tier-1 ISPs and peer with each other.<br>3. **Tier-3 / Access ISPs**: Local last-mile providers delivering residential and enterprise connectivity, purchasing transit from Tier-2/Tier-1 ISPs.
<!--ID: 1715300001-->

What is the economic and technical difference between IP Transit and Settlement-Free Peering?::* **IP Transit (Customer-Provider)**: A paid commercial contract where an upstream provider guarantees global reachability to the entire Internet ($0.0.0.0/0$).<br>* **Settlement-Free Peering (Peer-to-Peer)**: A mutual zero-cost agreement where two equal ISPs exchange traffic exclusively destined for **each other's direct customers**, never providing free transit to third-party networks.
<!--ID: 1715300002-->

What is an Internet Exchange Point (IXP / PTT) and why do ISPs connect to them?::An **IXP** is a physical, shared Layer-2 switching fabric where multiple independent ISPs, CDNs, and enterprises interconnect directly to peer traffic locally. It dramatically reduces transit latency and eliminates costly upstream transit fees.
<!--ID: 1715300003-->

What role does an IXP Route Server play in BGP peering?::It enables **Multilateral Peering**: instead of an ISP establishing separate bilateral BGP sessions with 200 individual networks at an IXP ($O(N^2)$ sessions), the ISP establishes a single BGP session with the Route Server ($O(N)$), which automatically distributes routing tables to all participants.
<!--ID: 1715300004-->

What is Hot-Potato Routing (*Roteamento Batata-Quente*)?::An intra-domain routing strategy where an originating autonomous system (AS) transfers an outbound inter-AS packet to the **physically closest egress router** connecting to the neighboring network, minimizing internal resource usage and dumping long-haul transit costs onto the peer.
<!--ID: 1715300005-->

What is a Point of Presence (PoP)?::A group of one or more routers in the provider's network at which customer ISPs can physically connect into the provider's backbone via high-speed leased links.
<!--ID: 1715300006-->
