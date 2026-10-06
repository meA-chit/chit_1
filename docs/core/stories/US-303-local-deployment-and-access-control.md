---
id: US-303
title: Local deployment and access control
module: core
epic: EPIC-03
priority: must
status: draft
release: pilot-1
journey_touchpoints:
- D3
- FL1
persona: Privacy-Conscious Household Administrator
dependencies: []
architecture_refs:
- docs/core/trust-and-privacy.md
components:
- deployment
- identity
---

> **Needs revision (2026-10-06):** AC-2 and AC-3 assume authentication that the code no longer has. ADR-0007 records the interim loopback-only decision. Rewrite these criteria once the identity design (open decision #2) exists; until then the story is `draft`.

# US-303: Local deployment and access control

## User story

As a **Privacy-Conscious Household Administrator**, I want to deploy Chit locally and restrict access to authorised users, so that household data remains under my control.

## Acceptance criteria

### AC-1: Local operation

Given supported local infrastructure, then core pilot services can run without sending household data to an unapproved cloud processor.

### AC-2: Authentication

Given a protected administration route, then unauthenticated users cannot access it.

### AC-3: Authorisation

Given a signed-in member, then protected operations enforce the assigned household role.

## Product constraints

- Preserve applicable provenance and data-state metadata.
- Do not add external side effects unless explicitly required above.
- Apply household access and screen-safe policies before returning sensitive information.

## Definition of done

- Acceptance criteria have automated coverage where technically feasible.
- Relevant contract, architecture and operational documentation is updated.
- Error, unavailable and stale paths have been verified.
