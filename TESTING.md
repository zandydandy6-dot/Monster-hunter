# Testing Monster Hunter in game (10 minutes)

Run `./gradlew runClient`, make a **Creative, cheats-on** world, then go through this list.

| # | Do this | You should see |
|---|---------|----------------|
| 1 | Main menu > Mods | "Monster Hunter" in the list; GeckoLib and Player Animation Library listed too |
| 2 | Creative inventory | A "Monster Hunter" tab with the black sword and James's Sweater / Trousers / Boots |
| 3 | `/give @s hagoyama:hagoyama` | A black sword with a red eye gem; hold it, swing it 3 times fast |
| 4 | (same) | Swing = slash 1, 2, 3 animation on your body (use F5 to see it). A second player sees it too |
| 5 | Spawn egg tab > James Spawn Egg | James: blocky body, spiky blue hair, black sword. He idles holding the sword |
| 6 | Hit James | He chases you, swings with different slashes; walk animation when he runs |
| 7 | Kill him 6 times | Each kill drops **exactly one** of sweater / trousers / boots (never two, never none) |
| 8 | Put the drops on | They show on your body like armor; each fits its own slot |
| 9 | `/hagoyama locate` | "Nearest Hagoyama cave shrine: [x, y, z] - N blocks away". Works for anyone |
| 10 | Click the coordinates, press Enter, `/tp` there, dig down to that Y | The cave shrine (winding caves, last room has the sword) |
| 11 | `/hagoyama trance` | Dark dimension; a **black shadow with two round glowing red eyes** walks a circle around you |
| 12 | `/hagoyama awaken`, hold the sword, look at mobs | New steel health bar with a red eye on the left; green > yellow > red as health drops |
| 13 | (optional, Curios installed) put the sword in the Curios **Back** slot | It is drawn across your back |

Things to look at if something is off (all are one-line fixes):
- Slash direction looks mirrored/backwards -> flip the sign of the `pitch` numbers in `assets/hagoyama/player_animation/*.json`, or the X rotations in `animations/entity/james.animation.json` (written for the usual Bedrock sign convention).
- Sword on the back sits wrong -> the three `ps.translate/scale` numbers in `client/CuriosSheath.java`.
- Shrines too rare/common -> `REGION` in `ShrineLocator.java`.
- Library version not found when building -> use the newest 1.20.1 version of that library (see README).
- `logs/latest.log`: search for "hagoyama" and "playeranim" - a failed animation file is logged there instead of crashing.
