# How the advice is calculated (and how to check it by eye)

All of this is standard practice. The app turns it into numbers for the distances you entered.

## Camera
* **Shutter:** the 180° rule says shutter ≈ 1 / (2 × frame rate). It is then snapped to a speed that does not flicker under mains-powered LED/fluorescent light: with 60 Hz mains use 1/60 or 1/120; with 50 Hz use 1/50 or 1/100. (24 fps under 60 Hz → 1/60.)
* **White balance:** set the camera's Kelvin to the colour temperature of your key/fill lights. Verify with the **white-card helper**: hold a white sheet in the dashed box; a *bluish* card means raise Kelvin, *reddish* means lower it. Re-measure after each step.
* **ISO:** as low as the key light allows. Use **Look match** to raise it just until the face reaches the target brightness.
* **Aperture:** a range per style (wider = softer background, narrower = sharper and deeper). Eyes in focus matters more than a number.

## Lights
| Style | Key angle | Key height | Key:fill | Background |
|---|---|---|---|---|
| Corporate & clean | 30–45° | 12–30° above eyes | 1.5–2.5 : 1 | even, a stop under the face |
| Podcast, warm | 35–50° | 10–25° | 2–3 : 1 | warm practicals |
| Cinematic, moody | 55–75° | 20–35° | 4–8 : 1 | dark + rim light |
| Bright & airy | 0–25° | 10–20° | 1–1.5 : 1 | bright |
| Tech, cool | 30–45° | 12–30° | 2–3 : 1 | cool accents behind |

* **Angle** is measured from the camera axis (0° = next to the camera, 90° = beside you, 180° = behind you). **Height** is the elevation angle above your eyes: `atan(height / distance)`.
* **Inverse-square law:** a light's strength at your face ∝ power / distance². The app estimates key:fill from power and distance **assuming similar fixtures** and tells you where to move the fill (`d' = √(P_f · d_k² · target / P_k)`) or what power to set.
* **Falloff across a face:** at distance *d*, the near cheek is `d − 7.5 cm` and the far cheek `d + 7.5 cm` away: `2·log₂((d+7.5)/(d−7.5))` stops. Closer light = softer but a bigger gap between cheeks.
* **Mixed colour temperatures** among key/fill/back (>600 K apart) are flagged: skin turns orange on one side, blue on the other. Background/practical lights are exempt (deliberate accents).
* **Subject → background ≥ 120 cm** keeps the background soft and out of your key light. **Camera ≥ 150 cm** (and zoom in) avoids stretching the face; lens at eye level or a little above.

## How Look match measures
In the browser, on the monitor image (never uploaded): brightness is the picture's own 0–255 value (gamma-coded) of a box at the centre of the frame; the **cheek ratio** compares the left and right halves of that box (gamma 2.4 converts between that and a lighting ratio); **warmth** is red/blue of the face; **light side** is the brighter half. Sit in the middle of the frame while measuring. It describes the *picture*, not your lights: a camera in a flat/log profile will read differently from a display-ready one — compare like with like (reference photos should be display-ready).

## Eyeball checks that still beat any app
* Catchlights in both eyes. * No dark pits under the brow (key too high). * No flashlight-under-chin look (key too low). * A thin bright edge on hair/shoulders from the back light. * Skin that doesn't change colour from one cheek to the other.
