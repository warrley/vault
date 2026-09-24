---
tags:
  - flashcards
  - flashcards/networks/intro/physical-media
  - networks/fundamentals
  - ufc/computer-networks
parent: "[[01-introduction-to-networks]]"
---

# Flashcards: Physical Media & Network Topologies

What is the fundamental distinction between Guided Media and Unguided Media?::* **Guided Media**: Waves are physically contained and guided along a solid transmission medium (e.g., Twisted-Pair copper, Coaxial cable, Fiber Optics).<br>* **Unguided Media**: Waves propagate freely through open atmosphere, space, or water without physical containment (e.g., Wireless Radio, Satellite, Infrared).
<!--ID: 1715500001-->

Why are copper network cables arranged as twisted pairs (par trançado)?::Twisting the two insulated copper conductors cancels out **electromagnetic interference (EMI)** and **crosstalk** (signals leaking between adjacent wire pairs) because external magnetic fields induce equal and opposite voltages in the twisted loops.
<!--ID: 1715500002-->

What are the 3 primary physical advantages of Optical Fiber over Copper conductors?::1. **Massive Bandwidth & Low Attenuation**: Can carry hundreds of Gbps over tens of kilometers without repeaters.<br>2. **Complete Immunity to EMI**: Photons carrying data are unaffected by high-voltage electrical fields or lightning.<br>3. **Security**: Extremely difficult to physically tap without causing detectable signal degradation.
<!--ID: 1715500003-->

What are the differences in collision domains, broadcast domains, and operating layers between a Hub, a Switch, and a Router?::* **Hub (Layer 1)**: Repeats raw electrical bits to all ports; **1 single shared collision domain**, 1 broadcast domain.<br>* **Switch (Layer 2)**: Forwards frames by MAC address; **isolates collision domains per port**, but maintains **1 single broadcast domain**.<br>* **Router (Layer 3)**: Forwards datagrams by IP address; **isolates collision domains and isolates broadcast domains**.
<!--ID: 1715500004-->

What is the comparative trade-off between a Star topology and a Bus topology?::* **Star Topology**: Easier cable management and fault isolation (a severed cable affects only 1 host), but the central switch is a single point of failure.<br>* **Bus Topology**: Cheaper with minimal cabling, but a single cable break or terminator failure disables the entire network, and bus collisions scale poorly.
<!--ID: 1715500005-->

Why is the wireless radio frequency spectrum strictly regulated by government agencies (e.g., Anatel / FCC)?::Because the radio frequency spectrum is a **shared, finite, unguided physical medium**. Without strict regulatory frequency licensing and transmit power rules, overlapping transmissions on the same frequencies would cause catastrophic mutual interference.
<!--ID: 1715500006-->
