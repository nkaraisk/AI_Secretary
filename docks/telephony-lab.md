## Milestone: Local telephone lab verified
Date: 2026-11-11

### Environment
- Hyper-V Generation 2 VM running Debian 12.
- FreePBX 17.0.33.4 and Asterisk 22.11.0 installed using the official installer.
- Hyper-V Default Switch used for local networking.
- Sangoma firewall running.
- Individual Windows management address trusted.
- Responsive Firewall disabled for the local lab.
- Anonymous inbound SIP calls and SIP guests disabled.

### Telephone accounts
- Extension 1001: MicroSIP on Windows.
- Extension 1002: Linphone on Windows.
- Both PJSIP contacts show Available.
- No User Control Panel accounts linked to these test extensions.

### Successful tests
- Extension 1001 registered.
- Extension 1002 registered.
- Echo test (*43): instructions and returned voice heard clearly.
- PCMU/G.711 μ-law audio test passed.
- G.722 audio test passed.
- Call from 1001 to 1002: ringing, answering, and hangup passed.
- Call from 1002 to 1001: ringing, answering, and hangup passed.

### Current limitations
- Local development environment only.
- SIP uses UDP; test calls are unencrypted.
- No carrier trunk or public telephone number connected.
- No Python call control or AI audio integration yet.
- Network addresses may change with Hyper-V Default Switch.

### Next milestone
Python controls a dedicated test call through Asterisk ARI,
plays a fixed greeting, and cleans up correctly on hangup.