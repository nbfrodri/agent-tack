---
name: ui-references
description: "Ground a UI component in real reference sites, present three or four directions for the user to choose, then build live variants of the chosen ones. Use when designing or restyling a page, section or component."
---

# UI references

A design chosen from real references and picked by the user beats the first design that comes to mind. The user chooses the direction; the assistant researches, proposes and builds. References inform structure, density and feel: the project keeps its own brand, copy and assets.

Go straight to building when the project already has a pattern for the piece (reuse it) or the user asks for it built without options.

## Steps
1. **Scope one piece.** Name the component or section, where it lives and what it must do; read the project's stack, design tokens and existing components. A request spanning several pieces is handled one piece at a time, starting with the one that sets the look for the rest. Done when the brief fits one sentence.
2. **Find references.** Take the rows of `references/sites.md` that match the piece and open real examples with a web or browser tool. Done when each direction to propose has one or two examples you opened; when no such tool is available, link the catalog pages and say they were not opened.
3. **Present directions and stop.** Offer three or four directions that differ on a named axis (layout, density, personality, motion, interaction), each with a descriptive name, its reference links, when it is the right choice and its cost. Two directions that differ only in colour or copy are one direction. Ask through the tool's question prompt when it has one. Done when the user has chosen one or two.
4. **Build the chosen directions as variants.** Each variant works, uses the project's tokens and realistic content, and lives on an isolated prototype route or, without a project, in one standalone HTML file; production code stays as it was. With the `prototype` skill active, tell the user they can run it for a picker. Check each variant in a browser at mobile and desktop widths when a browser tool is available. Done when the user has picked the winner.
5. **Promote and record.** Move the winner into the product, delete the prototype surface, and write the chosen direction and its references where the project keeps design decisions. Done when later pieces can follow that record without asking again.

Base components come from the libraries in the `frontend` skill; decorative effects come from `showcase-ui` and only on request.
