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

## Milestone 2: Give the PBX a fixed address

Completed by 18 November 2026.

Added an internal Hyper-V switch called `AI-Secretary-Lab`. Windows and the PBX now have their own fixed addresses on this network, in order to use the same address each time we start the lab.

Steps in order:

1. Created the internal switch in Hyper-V.
2. Set the Windows adapter to `192.168.250.1/24`.
3. Added a second network adapter to the VM.
4. Set Debian's new adapter, `eth1`, to `192.168.250.10/24`.
5. Kept `eth0` on the Default Switch for internet access. We did not add a gateway to the new connection.
6. Trusted `192.168.250.1/32` in the FreePBX firewall.
7. Updated the SIP local networks and pointed both softphones at the fixed PBX address.
8. Rebooted the VM and checked again after the firewall started. The fixed address, phone registrations, and local audio tests worked.

Addresses:

| | Address |
|---|---|
| PBX | `192.168.250.10` |
| Windows on the lab network | `192.168.250.1` |
| FreePBX web page | <http://192.168.250.10/admin/> |

The Debian settings are saved in `/etc/network/interfaces.d/ai-secretary-lab`. The old Default Switch address can still change.

## Milestone 3: Connect Python to Asterisk

Completed by 18 November 2026.

Enabled ARI, which is the interface the program uses to control Asterisk. Created the account `ai-secretary-dev` for this connection.

Asterisk's HTTP interface stays on `127.0.0.1:8088` inside the VM. It can be reached through an SSH tunnel instead of opening that port on the VM's network.

1. Checked that ARI and Stasis were available in Asterisk.
2. Configured the ARI account.
3. Opened the SSH tunnel from Windows.
4. Checked `/ari/applications` using the ARI password.
5. Started Python and confirmed that `ai-secretary` appeared in the application list.

From Windows, ARI is available at `http://127.0.0.1:18088/ari` while the tunnel is open.

A useful distinction: the tunnel protects the control connection. The current SIP phone calls still use unencrypted local audio.

## Milestone 4: Build the first call controller

Completed by 18 November 2026.

Created `voice/telephony-controller`. It uses `websockets==17.2`.

Structure:

1. Ask for the ARI password without showing it on screen.
2. Open a WebSocket and wait for Asterisk events.
3. Print the event type, without printing the caller's details.
4. When `StasisStart` arrives, get the call's channel ID.
5. Ask Asterisk to answer that call.
6. Ask Asterisk to play `hello-world`.

The WebSocket tells Python what happened. HTTP requests tell Asterisk what to do. We wait for the answer request to finish before asking for playback.

The code is in `voice/telephony-controller/main.py`. Its library version is recorded in `requirements.txt`.

## Milestone 5: Call the Python application on 7000

Completed on 18 November 2026.

Added internal test number `7000` to `/etc/asterisk/extensions_custom.conf`, in the `from-internal-custom` section. The custom file was used so FreePBX can keep managing its generated configuration separately.

The route selects English, sets a 60-second limit, and runs `Stasis(ai-secretary)`. This hands the call to our Python application. The name must match the application name in `main.py`.

When `7000` was dialed from MicroSIP. The controller printed:

```text
Event: StasisStart
Test call answered.
Greeting playback requested.
Event: PlaybackStarted
Event: PlaybackFinished
Event: ChannelHangupRequest
Event: StasisEnd
```

Translation:

- The call reached Python.
- Asterisk accepted the answer and playback requests.
- Asterisk reported that playback started and finished.
- The call then left the application.

`PlaybackFinished` means Asterisk finished the sound. `StasisEnd` means the channel left our application. This log does not show whether hangup was manual or caused by the test timeout. Whether the greeting was heard in the headset was not separately recorded for this call.

This is a prerecorded greeting, not an AI reply yet. Python does not yet hang up automatically when playback finishes.

[//]: # (## Starting the lab next time)

[//]: # ()
[//]: # (1. Start `ai-secretary-pbx-lab` in Hyper-V.)

[//]: # (2. Open the tunnel in a Windows PowerShell window:)

[//]: # ()
[//]: # (```powershell)

[//]: # (ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:18088:127.0.0.1:8088 pbxadmin@192.168.250.10)

[//]: # (```)

[//]: # ()
[//]: # (Enter the Debian password and leave the window open. Only one tunnel should use port 18088 at a time.)

[//]: # ()
[//]: # (3. Open the PyCharm terminal in `C:\Uth\AI_Project\AI_Secretary\voice\telephony-controller` and run:)

[//]: # ()
[//]: # (```powershell)

[//]: # (.\.venv\Scripts\python.exe main.py)

[//]: # (```)

[//]: # ()
[//]: # (Enter the ARI password for `ai-secretary-dev`. This is different from the Debian password and the phone passwords.)

[//]: # ()
[//]: # (4. Wait for `Connected to Asterisk. Application: ai-secretary`.)

[//]: # (5. Check that MicroSIP is Online, dial `7000`, listen for “Hello world”, and hang up.)

[//]: # ()
[//]: # (The call has a 60-second limit. The application needs to be running before we dial 7000.)

[//]: # ()
[//]: # (## Commands worth keeping)

[//]: # ()
[//]: # (For a normal Debian terminal, open a separate PowerShell window:)

[//]: # ()
[//]: # (```powershell)

[//]: # (ssh pbxadmin@192.168.250.10)

[//]: # (```)

[//]: # ()
[//]: # (These commands show the addresses, firewall, phones, and test route:)

[//]: # ()
[//]: # (```bash)

[//]: # (ip -br -4 address)

[//]: # (sudo pgrep -af '[v]oipfirewalld')

[//]: # (sudo fwconsole firewall list trusted)

[//]: # (sudo asterisk -rx "pjsip show contacts")

[//]: # (sudo asterisk -rx "dialplan show 7000@from-internal-custom")

[//]: # (```)

[//]: # ()
[//]: # (With the tunnel open, this Windows command checks the registered ARI applications:)

[//]: # ()
[//]: # (```powershell)

[//]: # (curl.exe --noproxy "*" --connect-timeout 5 --max-time 15 --user ai-secretary-dev -i http://127.0.0.1:18088/ari/applications)

[//]: # (```)

[//]: # ()
[//]: # (Expect `200 OK` and `ai-secretary` while Python is connected.)
