# JARVIS Development Instructions

## Project Methodology

This project follows Spec-Driven Development (SDD).

The specification is the source of truth for
feature behavior.

## Before Implementation

Before implementing any feature, the agent MUST read:

1. `specs/constitution.md`
2. The relevant feature specification
3. The relevant implementation plan
4. The relevant task list

## Implementation Rules

- Do not implement unspecified features.
- Do not silently modify approved requirements.
- Prefer simple solutions.
- Prefer a modular monolith for the MVP.
- Do not introduce unnecessary microservices.
- Do not introduce cloud infrastructure unless explicitly requested.
- Do not introduce 3D rendering in the MVP.
- Use mock hardware when physical hardware is unavailable.
- Keep hardware access behind abstractions.
- Keep business logic independent from physical hardware.

## Security

- Never commit secrets.
- Never hardcode API keys.
- Never expose credentials.
- Do not execute destructive commands without confirmation.

## Testing

Every implementation must include appropriate automated tests.

Before considering a task complete:

1. Run tests.
2. Run lint.
3. Run type checking where applicable.
4. Verify the acceptance criteria.
5. Report validation results.

## Scope

Implement only the requested task.

Do not implement future features unless explicitly requested.

## Documentation

Architectural decisions must be documented in:

`docs/decisions/`

Specifications must be stored under:

`specs/`