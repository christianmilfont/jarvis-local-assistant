# ADR-001: Use a Modular Monolith for the MVP

## Status

Accepted

## Context

The JARVIS MVP includes voice, vision, UI and IoT
capabilities.

However, the project is initially developed locally
and does not require independent service deployment.

## Decision

Use a modular monolith as the initial architecture.

Separate responsibilities through modules and interfaces.

Do not create independent microservices unless a
future requirement justifies them.

## Consequences

### Positive

- Simpler local development.
- Easier debugging.
- Fewer deployment concerns.
- Lower resource consumption.
- Faster initial implementation.

### Negative

- Less independent scalability.
- Some modules may require future extraction.
- More responsibilities in one application.

## Alternatives Considered

- Microservices from the beginning.
- Separate processes for every capability.