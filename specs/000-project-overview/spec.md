# JARVIS Local Assistant

## Product Overview

## Status

Draft

## Objective

Build a local-first personal AI assistant that allows
users to interact through voice, view a lightweight
2D avatar and control basic IoT devices.

## Target Environment

The MVP will initially run on a development computer.

The target physical environment is a Raspberry Pi
connected to a display, microphone, speaker and
ESP32 devices.

## Core Capabilities

1. Voice interaction.
2. AI-generated responses.
3. Text-to-speech output.
4. Lightweight 2D avatar.
5. Basic computer vision.
6. MQTT-based IoT communication.
7. Temperature monitoring.
8. LED control.
9. Basic conversation history.
10. Automated testing.

## MVP Constraints

- Local-first execution.
- No mandatory cloud infrastructure.
- No 3D rendering.
- No Kubernetes.
- No Terraform.
- No facial recognition.
- No advanced robotics.
- No unnecessary microservices.
- No physical hardware required for automated tests.

## Initial Technology Choices

- Python 3.12
- FastAPI
- React
- TypeScript
- Vite
- SVG
- CSS
- OpenCV
- MQTT
- Mosquitto
- SQLite
- Docker Compose
- pytest
- Vitest
- Ruff
- ESLint

## Future Possibilities

- Local LLM.
- Vector memory.
- Raspberry Pi deployment.
- More sensors.
- More actuators.
- Cloud integration.
- Advanced computer vision.
- 3D avatar.

## Definition of MVP Completion

The MVP is considered complete when the system can:

1. Receive a user command.
2. Process the command.
3. Generate a response.
4. Display the avatar state.
5. Produce an audio response through an
   appropriate audio provider.
6. Read temperature from a simulated IoT device.
7. Control a simulated LED.
8. Communicate through MQTT.
9. Run automated tests.
10. Run locally using documented instructions.

## Development Workflow

The project follows the workflow below:

1. Define the feature objective.
2. Create or update the feature specification.
3. Review and approve the specification.
4. Create the implementation plan.
5. Review and approve the plan.
6. Create implementation tasks.
7. Implement one task at a time.
8. Write and execute automated tests.
9. Validate the implementation against acceptance criteria.
10. Update documentation.
11. Commit the changes.

## Feature Status

Features MUST use one of the following statuses:

- Draft
- In Review
- Approved
- In Progress
- Implemented
- Validated
- Deprecated

## Traceability

Every implementation task MUST reference its
corresponding requirement.

Every automated test SHOULD reference the behavior
or acceptance criterion it validates.

