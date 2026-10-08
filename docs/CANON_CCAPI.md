# Canon Camera Control API (CCAPI) — what was verified

Verified on a **Canon EOS R50 V**, firmware 1.2.0, a power-zoom lens, video mode. Notes written from that experience; other CCAPI bodies should be similar but unconfirmed.

## Turn it on
1. Camera: **Menu → Network → Camera Control API**, join your Wi-Fi, wait for *"Waiting to connect"* — it shows the camera's address.
2. Put that address in the setup wizard (adapter *Canon (CCAPI)*). Port 443, https.
3. The camera joins *your* Wi-Fi (it does not create its own). It may only have an IPv6 address: link-local addresses need the interface suffix (`fe80::…%en0` on macOS).
4. After the camera powers off the API is **not** re-enabled by itself: reconnect it from the menu.
5. The camera uses a self-signed certificate; the adapter skips verification for it.

## What the adapter uses
| What | Endpoint |
|---|---|
| Info / lens / temperature | `GET ver100/deviceinformation`, `ver100/devicestatus/lens`, `…/temperature` |
| Battery / card | `GET ver110/devicestatus/batterylist`, `ver110/devicestatus/storage` |
| Settings | `GET ver100/shooting/settings` · `PUT ver100/shooting/settings/<key>` `{"value": …}` |
| Changes | `GET ver110/event/polling` (first call returns everything, then only changes) |
| Live view | `POST ver100/shooting/liveview` `{"liveviewsize":"small|medium","cameradisplay":"on"}` · `GET ver100/shooting/liveview/flip` (one JPEG) |
| Record | `POST ver100/shooting/control/recbutton` `{"action":"start|stop"}` |
| Zoom | `POST ver100/shooting/control/powerzoom` `{"value":"tele|wide|stop"}` |
| Focus | `POST ver100/shooting/control/af` `{"action":"start|stop"}` · `…/drivefocus` `{"value":"near1…far3"}` |

## Traps (each one cost time)
* **One client only on `event/polling`.** It is global: a second program polling "eats" the changes. This app must be the only one.
* **One connection at a time.** The camera chokes on parallel connections; the adapter serialises everything over one persistent connection.
* **Turn live view on before recording.** Sending `recbutton` while the camera sits on its network screen answers *"Device busy"* and can leave it locked until power-cycled. The adapter starts live view first.
* **Stopping right after starting** can answer 503 *"Device busy"*: the app retries for a few seconds.
* **Live view locks the camera's own menu** while the API is streaming. Use **Release camera** in the studio when you need the menu (registering a custom mode, formatting…), **Take camera** to come back.
* `settings/powerzoom` is the zoom **speed**, not the position. Move the lens with `control/powerzoom`.
* `remainingtime` and `recbutton` have no `GET`: they only arrive as events when they change.
* **Don't download big clips over Wi-Fi while connected** — the camera can send garbage and drop off. Take the card out and read it on a computer.
* There is **no live audio meter** over the network in video mode (RTP answers *"Mode not supported"*). The studio warns when the external microphone disconnects; check the camera's own meter before important takes.
* Picture-style parameters are not settable by the API in 10-bit video; the camera's custom picture setting rules.
* The camera does not answer ping even when connected: don't use ping as a diagnostic. *Connection refused* = the camera is on the network but its API is not listening (re-enable it from the menu).
* Live view over the API is the full recorded frame; the camera's own screen covers the edges with icons.
