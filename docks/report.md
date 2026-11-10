# AI Secretary — Progress Report

**Date:** 11 November 2026  
**Repository:** [nkaraisk/AI_Secretary](https://github.com/nkaraisk/AI_Secretary)  
**Current milestone:** Local telephone infrastructure and internal calling verified.

## 1. Project objective

Build an AI receptionist platform that can:

- Receive real telephone calls.
- Communicate naturally with callers.
- Answer business questions.
- Perform authorized actions, such as booking appointments.
- Support multiple businesses, each with a unique telephone number.
- Protect personal information and prevent unauthorized AI actions.

The planned technology stack is:

- **Spring Boot microservices:** business operations and authorization.
- **Python:** telephony control, speech recognition, AI conversation, and speech synthesis.
- **Asterisk:** telephone call processing.
- **FreePBX:** administration and configuration of the initial telephone lab.
- **Modulus:** future geographical telephone numbers and public telephone-network connectivity.

## 2. Architecture planning completed

A preliminary architecture and repository structure were designed.

Planned backend responsibilities include:

- Business and telephone-number configuration.
- Call-session tracking.
- Authorization of AI-requested actions.
- Appointment scheduling.
- Customer information.
- Calendar and external-system integrations.
- Business knowledge retrieval.
- Notifications.
- Audit and usage tracking.

The architecture separates:

1. Live audio transport.
2. Telephone call control.
3. Business operations.

Security principles established include:

- Enforcing permissions in backend code rather than relying on AI prompts.
- Deriving business identity from trusted telephone routing.
- Isolating each business’s data.
- Giving the AI narrowly scoped actions.
- Collecting only necessary personal information.
- Keeping credentials and customer recordings out of Git.
- Requiring confirmed backend success before announcing a completed booking.

These are design decisions; the production controls have not yet been implemented.

## 3. Development environments established

### Java backend

Created and successfully ran the `tenant-service` project in IntelliJ IDEA.

Configuration:

- Java 21.
- Spring Boot 4.1.2.
- Maven.
- Spring Web MVC.
- Validation.
- Actuator.
- Local development profile.

The development service listens on:

```text
http://127.0.0.1:8081
```

The loopback binding restricts access to the development computer.

### Python application

Created and successfully ran the `voice-runtime` project in PyCharm using a project-specific virtual environment.

Implemented a Python client that retrieves synthetic business configuration from the Java service.

### Java–Python integration verified

Implemented a local demonstration endpoint:

```text
GET /api/v1/demo/tenant-configuration
```

The response contains fictional business information:

- Tenant identifier.
- Business name.
- Language.
- Timezone.
- Greeting.

Verified:

- Java starts successfully.
- The health endpoint responds.
- Python retrieves and parses the JSON response.
- Python reports a connection failure when Java is stopped.

This integration is a local, unauthenticated demonstration. It does not handle real customer data.


## 4. Linux telephone lab installed

Created a dedicated Hyper-V virtual machine on Windows 11 Pro.

| Setting | Configuration |
|---|---|
| VM name | `ai-secretary-pbx-lab` |
| VM generation | Generation 2 |
| Operating system | Debian 12 |
| Virtual processors | 2 |
| Memory | 4 GB |
| Virtual disk | 40 GB |
| Networking | Hyper-V Default Switch |
| Linux hostname | `pbx-lab` |

Installed Debian as a server with:

- SSH server.
- Standard system utilities.
- No desktop environment.

Created a regular Linux administration account with `sudo` access.

Updated Debian and verified SSH access from Windows Terminal.

[//]: # (### Boot issue resolved)

[//]: # ()
[//]: # (The first installation attempt encountered a Secure Boot rejection and an unattached installation ISO.)

[//]: # ()
[//]: # (Corrected:)

[//]: # ()
[//]: # (- Debian ISO attachment.)

[//]: # (- Boot order.)

[//]: # (- Secure Boot template for Linux.)

[//]: # ()
[//]: # (Debian subsequently installed and booted successfully.)

### Recovery checkpoint created

Created a clean recovery checkpoint:

```text
Debian 12 updated - before FreePBX
```

## 5. Asterisk and FreePBX installed

Installed FreePBX 17 and Asterisk using the official FreePBX Debian installer.

Used `tmux` to keep the installation session available if SSH disconnected.

Accessed the FreePBX web interface and completed the initial administrator and language setup.

Exact installed Asterisk and FreePBX component versions still need to be recorded.

No commercial activation or purchased telephone number was required for the local lab.

## 6. Firewall configured and management access restored

Enabled Sangoma Smart Firewall.

Configured:

- Trust for the individual Windows management address.
- No trust for the broader network proposed by the wizard.
- Responsive Firewall disabled for the local lab.

[//]: # (During setup, an AJAX error occurred and browser/SSH access timed out.)

[//]: # ()
[//]: # (Troubleshooting through the Hyper-V console confirmed:)

[//]: # ()
[//]: # (- The VM’s IP address had not changed.)

[//]: # (- SSH was running and listening on port 22.)

[//]: # (- The Windows management address was visible in previous successful connections.)

[//]: # ()
[//]: # (Added the individual management address to the firewall’s Trusted zone and restarted the firewall.)

[//]: # ()
[//]: # (Verified:)

[//]: # ()
[//]: # (- SSH access restored.)

[//]: # (- Web administration access restored.)

[//]: # (- Trusted-address entry present.)

[//]: # (- `voipfirewalld` and its monitor process running.)

[//]: # (- The setup wizard successfully continued afterward.)

[//]: # ()
[//]: # (The earlier `firewalld.service not-found` result referred to a different service name and did not establish that Sangoma’s firewall was stopped.)

## 7. SIP and audio settings configured

Verified the detected local network against the VM’s routing information.

Configured or retained:

- Anonymous inbound SIP calls: disabled.
- SIP guests: disabled.
- PJSIP transport for the lab: UDP on port 5060.
- RTP audio port range: 10000–20000.
- Strict RTP: enabled.
- STUN/TURN: not configured.
- Video support: disabled.

The local-network setting tells Asterisk when to use its internal address. It is separate from firewall trust.

External carrier connectivity has not been configured or tested.

## 8. Two internal extensions created

Created and applied two PJSIP extensions:

| Extension | Display name | Software phone |
|---|---|---|
| `1001` | Lab Phone 1 | MicroSIP on Windows |
| `1002` | Lab Phone 2 | Linphone on Windows |

Each extension has its own generated SIP password.

Both extensions were configured without linked User Control Panel accounts.

## 9. Audio testing completed

Configured MicroSIP to use the headset microphone and headphones.

Tested FreePBX’s echo-test feature:

```text
*43
```

### PCMU test

Observed negotiated codec:

```text
PCMU @ 8 kHz, 64 kbit/s
```

Result:

- Instructions heard clearly.
- Microphone audio returned clearly.

### G.722 test

Temporarily enabled only G.722 to verify wideband codec negotiation.

Observed negotiated codec:

```text
G722 @ 16 kHz, 64 kbit/s
```

Result:

- Call connected.
- Echo test completed successfully.
- Audio heard clearly.

Both tests used unencrypted media. TLS/SRTP has not yet been configured.

These tests verify the local audio path; they do not measure AI response latency or public-network call quality.

## 10. Registration and internal calling verified

Checked registration using:

```bash
sudo asterisk -rx "pjsip show contacts"
```

Both extensions appeared as:

```text
Avail
```

Both software phones run on the same Windows computer and use different local SIP ports.

Successfully tested:

- `1001 → 1002`.
- `1002 → 1001`.
- Ringing.
- Answering.
- Call establishment.
- Hangup.

The displayed contact RTT values measure SIP reachability, not end-to-end voice latency.

## 11. Current working capabilities

The development environment can now:

- Run the Java and Python projects independently.
- Exchange synthetic business configuration over HTTP.
- Run an Asterisk/FreePBX telephone server in a Linux VM.
- Register two software phones.
- Route calls between internal extensions.
- Send and receive clear audio through the PBX.
- Complete echo tests using PCMU and G.722.
- Provide working SSH and web administration access.

[//]: # (## 13. Not yet implemented)

[//]: # ()
[//]: # (The following remain outstanding:)

[//]: # ()
[//]: # (- Modulus number purchase and SIP trunk configuration.)

[//]: # (- Calls to or from the public telephone network.)

[//]: # (- Python call control through Asterisk ARI.)

[//]: # (- Live audio exchange between Asterisk and Python.)

[//]: # (- Speech-to-text.)

[//]: # (- AI conversation handling.)

[//]: # (- Text-to-speech.)

[//]: # (- Interruption and turn-taking behavior.)

[//]: # (- Appointment booking and calendar integration.)

[//]: # (- Backend authentication and tenant isolation.)

[//]: # (- Production privacy and retention controls.)

[//]: # (- Encrypted SIP/media configuration.)

[//]: # (- Automated deployment, monitoring, load testing, and recovery testing.)

[//]: # ()
[//]: # (The current environment is a functional development lab, not a production deployment.)

[//]: # ()
[//]: # (## 14. Next milestone)

[//]: # ()
[//]: # (**Enable Python to answer a dedicated test call and play a fixed greeting.**)

[//]: # ()
[//]: # (Planned sequence:)

[//]: # ()
[//]: # (1. Record installed software versions.)

[//]: # (2. Save documentation to GitHub.)

[//]: # (3. Create a checkpoint of the verified telephone lab.)

[//]: # (4. Inspect Asterisk HTTP, ARI, and Stasis availability.)

[//]: # (5. Configure dedicated ARI credentials and protected development access.)

[//]: # (6. Create the Python `telephony-controller` service.)

[//]: # (7. Route a dedicated test number to the Python-controlled application.)

[//]: # (8. Answer the call, play a sound, and handle hangup cleanly.)

[//]: # (9. Introduce live speech processing after call control is reliable.)

[//]: # ()
[//]: # (This will connect the working telephone infrastructure to the application layer.)
