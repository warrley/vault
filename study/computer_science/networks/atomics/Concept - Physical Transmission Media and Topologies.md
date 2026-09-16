---
tags:
  - networks/physical
  - networks/topologies
  - networks/kurose-ch1
  - networks/tanenbaum-ch2
parent: "[[01-introduction-to-networks]]"
---

# Concept: Physical Transmission Media and Topologies

## 1. Network Topologies (Topologias de Rede)

The physical topology defines how computing nodes and transmission cables are arranged and interconnected:

```
     Star Topology (Estrela)             Bus Topology (Barra)                 Ring Topology (Anel)
          ┌────────┐                                                            ┌────► [Host] ────┐
          │ [Host] │                     [H1]    [H2]    [H3]                   │                 │
          └───┬────┘                       │       │       │                    ▼                 ▼
              │                     ───────┴───────┴───────┴──────           [Host]             [Host]
    ┌────┐    │    ┌────┐           (Shared single backbone cable)              ▲                 │
    │[H] │──[Switch]──│[H] │                                                     │                 ▼
    └────┘    │    └────┘                                                       └──── [Host] ◄────┘
              │                                                                 (Unidirectional token ring)
          ┌───┴────┐
          │ [Host] │
          └────────┘
```

---

### In-Depth Topologies Comparison (Professor's Exam Question)

#### A. Star Topology (*Topologia em Estrela*)
* **Structure**: Every end system connects via a dedicated point-to-point cable directly to a central hub or switch.
* **Advantages**:
  * **Fault Isolation**: A cut or fault in one cable only disconnects that specific host; the rest of the network operates normally.
  * **Simplicity**: Extremely easy to add or remove nodes without disrupting active communications.
  * **Troubleshooting**: Fault diagnosis is centralized at the switch ports.
* **Disadvantages**:
  * **Single Point of Failure**: If the central switch/hub fails, the entire network goes down.
  * **Cabling Overhead**: Requires significantly more total cable length than a bus topology.
* **Modern Relevance**: Dominant topology for all modern Ethernet LANs and Wi-Fi networks.

#### B. Bus Topology (*Topologia em Barra / Barramento*)
* **Structure**: All devices tap into a single continuous backbone transmission cable (e.g., coaxial cable with terminating resistors).
* **Advantages**: Minimal cabling required; simple installation; low initial material cost.
* **Disadvantages**:
  * **Single Point of Catastrophic Failure**: A break anywhere along the main bus cable splits the network and causes impedance mismatch reflections, bringing down communication for all nodes.
  * **Collisions & Scalability**: All nodes share the same physical channel; heavy network loads cause frequent packet collisions requiring backoff algorithms (CSMA/CD).
* **Modern Relevance**: Legacy technology (10BASE2, 10BASE5 coaxial Ethernet); obsolete in modern LANs.

#### C. Ring Topology (*Topologia em Anel*)
* **Structure**: Nodes are connected sequentially in a closed physical loop. Data travels in one direction around the ring from node to node.
* **Advantages**:
  * **Deterministic Access**: Controlled by a circulating "Token" (Token Ring / FDDI). No data collisions occur; every node receives guaranteed channel access.
  * Equal bandwidth sharing under high sustained loads.
* **Disadvantages**:
  * **Single Node Failure**: A failure in any single computer or cable segment breaks the ring loop unless expensive dual-counter-rotating rings are deployed.
* **Modern Relevance**: Token Ring is obsolete, but dual-ring architectures remain critical in optical metropolitan backbones (SONET / SDH).

---

## 2. Transmission Media (Meios de Transmissão Físicos)

Transmission media fall into two fundamental categories: **Guided** (physical solid conductors/guides) and **Unguided** (wireless electromagnetic waves).

### A. Guided Media (*Meios Guiados*)

#### 1. Twisted-Pair Copper Wire (*Par Trançado*)
* **Structure**: Pairs of insulated copper wires twisted spirally around each other (e.g., Cat 5e, Cat 6, Cat 6a).
* **Why are the wires twisted? (List 3 Focus)**:
  * Passing electric current through a wire creates a magnetic field that induces unwanted noise (crosstalk) in adjacent wires.
  * Twisting the two wires of a pair ensures both wires receive equal exposure to external electromagnetic fields and adjacent signals. Because network transceivers measure the **differential voltage** ($V_1 - V_2$) between the two wires, any noise induced equally in both wires cancels out mathematically!
* **Trade-offs**: Inexpensive, flexible, ubiquitous; maximum segment length is limited to $100\text{ m}$ to prevent excessive signal attenuation.

#### 2. Coaxial Cable (*Cabo Coaxial*)
* **Structure**: Central copper conductor surrounded by a dielectric insulator, metallic braided shielding, and outer jacket.
* **Trade-offs**: Higher bandwidth and better noise immunity than twisted-pair over longer distances; more rigid and expensive to install. Standard for broadband cable Internet (DOCSIS).

#### 3. Fiber Optic (*Fibra Ótica*)
* **Structure**: Hair-thin strand of ultra-pure silica glass carrying pulses of laser light or LEDs.
* **Physical Principle**: **Total Internal Reflection** (*Reflexão Total Interna*). Light is guided inside the glass core because the surrounding cladding has a lower refractive index.
* **Advantages**:
  * Massive transmission bandwidth ($> 100\text{ Gbps}$ to Terabits/s).
  * **100% Immune to Electromagnetic Interference (EMI)** (does not use electrical currents; can run next to high-voltage power lines).
  * Extremely low attenuation (signals travel $50 - 100\text{ km}$ before requiring amplification).
* **Disadvantages**: Fragile glass fibers; expensive optical transceivers; difficult splicing and termination.

---

### B. Unguided Media (*Meios Não Guiados / Sem Fio*)

#### 1. Radio Frequency (*Ondas de Rádio*)
* **Characteristics**: Omnidirectional propagation (transmits in all directions); penetrates walls and obstacles easily.
* **Applications**: Wi-Fi (802.11), Cellular (4G/5G), Bluetooth.
* **Vulnerabilities**: Prone to multipath fading (signals reflecting off walls and interfering destructively) and security interception.

#### 2. Terrestrial Microwave (*Micro-ondas Terrestres*)
* **Characteristics**: Highly directional, high-frequency signals focused by parabolic dish antennas. Requires strict **Line-of-Sight (LOS)** between antenna towers.
* **Applications**: Long-range carrier backhaul between mountain peaks, telecommunications towers, and ISP links.

#### 3. Infrared (*Infravermelho*)
* **Characteristics**: Short-range, directional, **cannot penetrate walls or opaque objects**.
* **Advantages**: High localized security; zero interference with adjacent rooms or equipment.
* **Applications**: Remote controls, short-range peripheral connections.

---

## 3. Fundamental Physical Layer Questions (Exercise List 3 Focus)

> [!question] Professor's Question: Why are radio frequency spectrum bands strictly regulated by government agencies (Anatel / FCC)?
> **Answer**: The electromagnetic spectrum is a finite, globally shared natural resource. If radio frequencies were unregulated, multiple nearby transmitters would broadcast on the exact same frequency channels simultaneously, causing catastrophic destructive interference that would render cellular networks, emergency services, air traffic control radars, and satellite communications unusable. Licensing and regulating frequency bands guarantees exclusive, interference-free operational channels.

> [!question] Professor's Question: What is the role of repeaters and amplifiers in communication links?
> **Answer**: As electrical, optical, or wireless signals propagate through physical media, they suffer **attenuation** (loss of signal power over distance) and **dispersion/distortion**.
> * **Amplifiers (Analog)**: Boost the amplitude/voltage of the signal (along with any noise).
> * **Repeaters (Digital)**: Receive the attenuated digital bitstream, reconstruct the clean binary square waves (`0`s and `1`s), and retransmit a pristine, noise-free signal, significantly extending the maximum physical distance of the communication link.
