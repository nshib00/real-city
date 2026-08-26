# Real City - Agent Instructions

## Project Overview

This repository is the browser game project `Real City`.

The game is a multiplayer real-time strategy on one shared persistent map. All players exist in the same world, place buildings on the map, compete for space and resources, and interact with each other through construction, economy, defense, raids, destruction, and territorial control.

The closest reference is the closed browser game Gnomgrad / "Real City - Gnomgrad" (`https://gnomgrad.ru/`). Use it as a gameplay reference, not as something to copy directly. Preserve the useful design ideas, but do not copy its setting, names, visual identity, exact object list, text, or copyrighted assets.

## Reference Mechanics From Gnomgrad

From the available Gnomgrad materials:

- It was a multiplayer browser city-building game on a shared map with chat.
- The core goals were city construction, economic growth, resource capture, and territorial control.
- Players could collect and grow resources, raid neighbors, destroy buildings, and fight alone or in groups.
- There were player groups/gangs, markets, defensive objects, weapons, decorations, roads/walls, storage buildings, production buildings, city centers, resource nodes, terrain objects, and monsters.
- The world included forest exploration, deposits/resource nodes, and hunting or fighting monsters.
- Buildings were organized by gameplay categories: housing, special buildings, factories, fields/farms, statues/idols, centers, storage, towers, gang castles, gifts/decor, roads/walls, cannons, resources, monsters, deposits, rivers, and mountains.

## Our Game Direction

Keep the following pillars stable unless the user explicitly changes the design:

- Browser-first multiplayer game.
- One large shared server-side map, not isolated per-player bases.
- Real-time world simulation.
- Player-built structures exist directly on the map and can affect nearby territory.
- Other players can interact with, raid, damage, or destroy vulnerable buildings.
- Hostile roaming monsters create PvE pressure and make undefended expansion risky.
- Resources spawn or exist on the shared map and can be claimed, harvested, contested, stolen, or defended.
- Territory and logistics should matter: placement, borders, roads, defenses, travel time, and proximity should create strategic decisions.
- The setting must be original. Avoid gnomes and direct Gnomgrad naming unless the user explicitly asks for temporary placeholders.

## Product Principles

- Build the actual playable game surface first, not a marketing landing page.
- Favor systems that create emergent conflict on the shared map over isolated menu management.
- Make actions readable and inspectable: players should understand who owns a tile/object, what it produces, what protects it, and what threatens it.
- Design for asynchronous and real-time play: the world continues while players are offline, but avoid mechanics that punish casual players so hard that recovery is impossible.
- Avoid pay-to-win assumptions. If monetization appears later, keep power-affecting mechanics earned through play unless the user decides otherwise.

## Technical Principles

- Treat the server as authoritative for map state, resources, combat, construction, monster AI, ownership, and timers.
- Clients should render and request actions; they must not be trusted for final game-state decisions.
- Prefer deterministic or auditable server-side simulation steps for systems such as production ticks, movement, combat, decay, and monster behavior.
- Use real-time transport for live map updates when the stack supports it, typically WebSockets or an equivalent event stream.
- Design map updates to be incremental. A large shared world should not require resending the whole map for every change.
- Keep domain concepts explicit in code: `Map`, `Tile`, `Building`, `ResourceNode`, `Player`, `Faction/Group`, `Monster`, `Action`, `Combat`, `Inventory`, `Territory`, and `Event`.
- Build mechanics with testable pure/domain logic where practical, then connect them to persistence, networking, and UI.
- Validate all player actions server-side: range, ownership, cooldowns, resource costs, permissions, collision, build rules, and target validity.
- Assume hostile clients. Never trust client-provided coordinates, ownership, costs, cooldown completion, damage values, or rewards.

## Frontend Principles

- The first screen of the app should be a usable game/map interface when feasible.
- Prioritize dense, readable strategy UI: map, side panels, selection details, build/action controls, event log, resource bar, and notifications.
- Use screenshots from `reference/images` as the primary local reference for the original game's visual appearance, map composition, UI density, color mood, and isometric presentation.
- Use stable dimensions for map cells, toolbars, counters, panels, and buttons to avoid layout shifts.
- Controls should be familiar: icon buttons for tools, tabs for panels, menus for option sets, toggles for binary state, sliders/inputs for numeric values.
- Do not add decorative UI that competes with the map. The map is the primary surface.
- For any 3D map or scene, use Three.js and verify that the canvas renders correctly on desktop and mobile.

## Development Workflow

- Before changing code, inspect the current stack and follow existing project conventions.
- Keep changes scoped to the requested feature or fix.
- Prefer `rg` / `rg --files` for repository search.
- Use `apply_patch` for manual file edits.
- Write all Markdown (`.md`) files in Russian by default, unless the user explicitly asks for another language.
- Do not introduce unrelated refactors or formatting churn.
- If tests or validation scripts exist, run the relevant ones before finishing.
- If a dev server is needed for browser verification, start it and provide the local URL.

## Naming And IP Boundaries

- Do not use Gnomgrad-specific names, characters, exact building names, images, icons, or text as production content.
- It is acceptable to use generic category names such as `building`, `resource node`, `monster`, `market`, `warehouse`, `tower`, `wall`, `road`, `guild`, or `territory`.
- When implementing placeholder content, choose neutral original names and make it easy to replace them later.

## Current Repository State

At the time this file was created, the repository did not yet contain an application structure. Future agents should first inspect the workspace before assuming a framework, package manager, language, or architecture.
