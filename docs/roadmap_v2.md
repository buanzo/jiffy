# Jiffy Roadmap v2 (2025 and Beyond)

This document collects proposed improvements for the next major iteration of Jiffy. The focus is on modernizing the codebase and ensuring a smoother user experience in 2025.

## 1. Update the Environment

- Require Python 3.12 or newer.
- Use a virtual environment via **pip** or **poetry**. The bundled `requests` library should be removed in favor of standard dependencies.
- Replace the legacy `gnupg` wrapper with actively maintained packages or integrate with the `cryptography` ecosystem for better performance and algorithm variety.

## 2. Modern Network Layer

- Introduce asynchronous I/O using `asyncio` and `aiohttp` for scalable send/receive operations.
- Enforce strict TLS verification with up-to-date cipher suites.
- Automate certificate management (e.g., with LetsEncrypt) so users no longer have to manually configure trust.

## 3. Improved Architecture

- Separate the core functionality (encryption, message composition, server protocol) from the UI layer.
- Provide a clean API/SDK so alternative clients (CLI, mobile, web) can reuse the logic.
- Implement message routing and federation as hinted in existing TODO comments. This will enable interoperability across multiple servers.

## 4. Redesigned User Interface

- Evaluate adopting a modern GUI toolkit (such as Qt via PySide/PyQt) or a web-based front end (Electron or pure web stack) for cross-platform reach.
- Add contact management, message history, and notification features, with optional integration for mobile devices.

## 5. Enhanced Security and Usability

- Offer a streamlined onboarding flow with automatic key generation and trust establishment, potentially using QR codes or secure invites.
- Explore user-friendly encryption approaches like MLS or Autocrypt while still supporting classic OpenPGP for backward compatibility.

## 6. Automated Testing and Deployment

- Add unit tests for the core client logic and set up continuous integration.
- Package Jiffy for distribution via PyPI or container images to simplify installation.

---

Overall, Jiffy has a solid foundation but needs significant modernization to meet expectations in 2025. Updated dependencies, asynchronous networking, a refreshed UI, and improved key and session management will help it remain relevant and secure.
