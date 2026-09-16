> [!quote] YOU

explain to me graps given this slides /home/warley/ufc/4s/detailed_software_project/slides/aula-grasp-2.1-criador-especialista-acoplamento-controlador-coesao.pdf


> [!question] Quiz
> In Responsibility-Driven Design (PGR/RDD), what is the core problem that GRASP patterns help you solve?
>
> 1. Mapping domain classes to relational database tables
> 2. Optimizing CPU execution time and memory allocation
> 3. Structuring user interface rendering and visual layouts
> 4. Assigning responsibilities (data and behavior) to classes


> [!question] Quiz — I don't know
> Your answer: I don't know
> Correct answer: 4
>
> Note: just give me a overview, skip the quiz for now
>
> GRASP stands for General Responsibility Assignment Software Patterns. Its primary focus is Responsibility-Driven Design (RDD)—deciding which class or object is responsible for knowing specific data ('saber') and doing specific actions ('fazer').


> [!abstract] PI

Here is a complete, structured overview of **GRASP** based directly on your lecture slides.

---

## 1. The Core Philosophy: Responsibility-Driven Design (RDD / PGR)

In Object-Oriented Design, a system is not just a collection of data structures; it is a community of collaborating objects.

Every object has two fundamental kinds of responsibilities:
1. **Knowing (*Saber*):** Knowing private encapsulated data, related objects, or things it can derive.
2. **Doing (*Fazer*):** Performing calculations, initiating actions in other objects, or controlling/coordinating activities.

**GRASP** (*General Responsibility Assignment Software Patterns*) provides systematic mental rules to decide **which class should be responsible for what**.

---

## 2. Fundamental Architectural Guidelines

Before diving into specific patterns, the slides emphasize two foundational guidelines:

```
[ Domain Reality ]  ──(Low Representational Gap)──>  [ Domain Model / Code ]
                                                              ▲
                                                              │ (delegates system operations)
                                                     [ UI / View Layer ]
```

### A. Low Representational Gap (*Baixo Hiato Representacional*)
- **Idea:** The names, relationships, and concepts in your software code should mirror the real-world problem domain as closely as possible.
- **Why:** Reduces mental translation overhead. When a business concept changes, you immediately know which software class corresponds to it.

### B. Model-View Separation (*Separação Modelo-Visão*)
- **Idea:** Never put business logic, validation rules, or domain state inside UI components (buttons, forms, screens).
- **Rule:** UI components only collect user inputs, display data, and immediately delegate operations to domain objects.

---

## 3. The 5 GRASP Patterns from the Slide Deck

```
                          ┌──────────────────────────┐
                          │   GRASP Core Patterns    │
                          └─────────────┬────────────┘
         ┌──────────────────┬───────────┴───────────┬──────────────────┐
         ▼                  ▼                       ▼                  ▼
   ┌───────────┐  ┌───────────────────┐      ┌─────────────┐    ┌───────────────┐
   │  Creator  │  │Information Expert │      │ Controller  │    │Coupling/Cohesion│
   └───────────┘  └───────────────────┘      └─────────────┘    └───────────────┘
```

---

### Pattern 1: Creator (*Criador*)

* **Problem:** Who should be responsible for instantiating a new instance of class `A`?
* **Solution:** Assign class `B` the responsibility to create `A` if one (or more) of the following holds:
  1. `B` contains or composite-aggregates `A` (e.g., a `Post` contains `Comentario`s).
  2. `B` records / closely uses instances of `A`.
  3. `B` has the initialization data needed to instantiate `A`.
* **Slide Example:** In a Blog system, a `Post` aggregates comments and has their context $\rightarrow$ **`Post` creates `Comentario`**.

---

### Pattern 2: Information Expert (*Especialista na Informação*)

* **Problem:** What is the general principle for assigning any responsibility/behavior to an object?
* **Solution:** Assign the responsibility to the class that has the **information necessary to fulfill it**.
* **Key Principles connected to Expert:**
  - **"Tell, Don't Ask":** Procedural code asks an object for its data and does the calculation externally. Good OO code tells the object holding the data to do the calculation itself.
  - **Law of Demeter (Principle of Least Knowledge):** A method should only talk to its immediate neighbors (its own fields, parameters, objects it creates)—avoid long call chains like `a.getB().getC().doSomething()`.

---

### Pattern 3: Controller (*Controlador*)

* **Problem:** Which first object beyond the UI layer receives and coordinates a system operation?
* **Solution:** Assign the responsibility to an object representing either:
  1. **A Root / System / Subsystem Facade:** (e.g., `VisualizadorConteudoFacade`, `SistemaVendas`).
  2. **A Use Case Handler:** (e.g., `CriarPostHandler`, `FinalizarVendaController`).
* **Why:** Keeps the UI decoupled from the domain logic and coordinates the flow of business operations.

---

### Pattern 4 & 5: Low Coupling & High Cohesion (*Acoplamento Baixo & Coesão Alta*)

These two patterns act as the **evaluative compass** for every design decision:

| Pattern | Goal | What it means |
| :--- | :--- | :--- |
| **Low Coupling** (*Baixo Acoplamento*) | Minimize dependency between classes | If class `A` changes, classes `B`, `C`, and `D` should not break. Keep connections minimal. |
| **High Cohesion** (*Alta Coesão*) | Keep class focus narrow and clear | A class should do one well-defined job with closely related methods, rather than acting as a giant "god class". |

---

> [!tip] 🎓 English Polish
> - **Original:** *"explain to me graps given this slides"*
> - **More Natural:**
>   - *"Can you explain **GRASP** to me based on **these** slides?"* (Formal/Direct)
>   - *"Give me an overview of GRASP from **these** slides."* (Casual)
> - **Key Corrections:**
>   1. **Typo:** `graps` $\to$ `GRASP`
>   2. **Demonstrative pronoun:** `this slides` (singular + plural) $\to$ **`these slides`** (plural)
