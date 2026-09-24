# JARVIS Constitution

## Project

JARVIS Local Assistant

## Purpose

Define the engineering principles that govern the
development of the JARVIS Local Assistant.

This document is mandatory for all project features.

---

## Principle I — Specification First

Every feature MUST have an approved specification
before implementation begins.

Every implementation MUST be traceable to one or
more requirements.

Requirements MUST NOT be silently changed during
implementation.

If a requirement is unclear or contradictory,
development MUST pause until the issue is resolved.

---

## Principle II — Local First

The MVP MUST prioritize local execution.

Cloud infrastructure MUST NOT be required for
the core application to run.

External services MAY be integrated through
well-defined interfaces.

The system MUST support development without
physical hardware whenever possible.

---

## Principle III — Simplicity

The MVP MUST prioritize simple and maintainable
solutions.

New technologies MUST have a documented reason.

Microservices MUST NOT be introduced without
a demonstrated architectural need.

The system MUST initially use a modular monolith
where practical.

---

## Principle IV — Hardware Abstraction

Business logic MUST NOT depend directly on
physical hardware.

Hardware access MUST be isolated behind interfaces.

The application MUST support mock implementations
for development and automated testing.

---

## Principle V — Controlled Actions

The LLM MUST NOT directly access GPIO, operating
system commands or hardware interfaces.

All actions MUST pass through controlled application
tools.

Tools MUST validate their inputs before execution.

Potentially dangerous actions MUST require explicit
authorization.

---

## Principle VI — Testability

Business-critical behavior MUST have automated tests.

Tests MUST be executable without physical hardware
whenever practical.

Every completed task MUST include appropriate
validation.

---

## Principle VII — Security

Secrets MUST NOT be committed to the repository.

Environment variables MUST be used for credentials.

The system MUST minimize the collection of personal
data.

Stored conversations MUST be removable by the user.

---

## Principle VIII — Observability

Important operations MUST generate structured logs.

Errors MUST contain enough context to support
diagnosis.

The system SHOULD expose basic health information.

Advanced observability MAY be implemented after
the core MVP is functional.

---

## Principle IX — Documentation

Architectural decisions MUST be documented.

Public interfaces MUST have clear documentation.

The README MUST explain how to run and test
the project.

---

## Principle X — Incremental Delivery

Features MUST be implemented in small increments.

Each task MUST have a clear objective.

Each completed task MUST be independently validated.

The project MUST remain runnable throughout development.