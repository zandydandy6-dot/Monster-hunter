# Monster Hunter (Forge 1.20.1, Java 17)
Hagoyama - the black sword whose eyes open when you almost die - plus **James** (the sword's wielder), the red-eyed
**shadow** you meet in the trance, James's wearable clothes, and a command that finds the cave where it all starts.
(Mod id stays `hagoyama` so nothing already made breaks; everything you read in-game says "Monster Hunter".)

## Build
1. Download the official Forge MDK for 1.20.1 (47.x) from files.minecraftforge.net and unzip it.
2. Delete the MDK's `src/main/java/com/example` folder and its `src/main/resources/META-INF/mods.toml`.
3. Copy this zip's `src` folder into the MDK (merge/overwrite).
4. In the MDK's `gradle.properties` set:  mod_id=hagoyama  mod_name="Monster Hunter"  mod_group_id=com.hagoyama
5. In the MDK's `build.gradle` add the three library mods (versions are the ones this was written against -
   if Gradle can't find one, use the newest 1.20.1 version listed on that mod's page):
```gradle
repositories {
    maven { url = 'https://dl.cloudsmith.io/public/geckolib3/geckolib/maven/' }   // GeckoLib
    maven { url = 'https://maven.kosmx.dev/' }                                    // Player Animation Library
    maven { url = 'https://maven.theillusivec4.top/' }                            // Curios (optional)
}
dependencies {
    implementation fg.deobf('software.bernie.geckolib:geckolib-forge-1.20.1:4.4.9')
    implementation fg.deobf('dev.kosmx.player-anim:player-animation-lib-forge:1.0.2-rc1+1.20')
    runtimeOnly    fg.deobf('top.theillusivec4.curios:curios-forge:5.9.1+1.20.1')   // optional, only to test the sheath
}
```
6. `./gradlew runClient` to test, or `./gradlew build` -> jar in build/libs.

**Players need GeckoLib + Player Animation Library installed next to this mod (Curios is optional).**

## What's in it
- **James** (`/summon hagoyama:james`, or the spawn egg): blocky Minecraft body, spiky blue hair, knit sweater,
  denim, boots, black sword. GeckoLib animations: idle, walk and three different sword slashes.
  Killing him drops **exactly one** of: James's Sweater, Trousers or Boots - wear them like armor (they show on your body).
- **Black Hagoyama sword** with a red eye. Swinging it plays a 3-hit slash combo on you (Player Animation Library),
  and other players see it too. With Curios installed it also fits the **back** slot and is drawn sheathed on your back.
- **Shadow** in the trance: a black smoke creature with two round, glowing red eyes.
- **Clear Eye health bars**: steel Monster-Hunter-style gauge with a red eye emblem, green -> yellow -> red.
- **/hagoyama locate** (anyone can use it): shows the nearest cave shrine with clickable coordinates. One shrine per
  192x192-block region, placed from the world seed, so it works in places you haven't explored yet.

## Controls (changeable in Controls > Monster Hunter)
R = switch move, hold Z = zoom (scroll while holding Z to change zoom).

## Test commands
/hagoyama locate   - nearest cave shrine (everyone)
/hagoyama trance   - enter the trance now (op)
/hagoyama awaken   - unlock Clear Eye (op)
/hagoyama reset    - lock it again and allow re-claiming (op)
/give @s hagoyama:hagoyama
Full check-list for trying everything in game: TESTING.md

## Tuning
Shrine spacing: `REGION` in ShrineLocator.java (chunks per side; smaller = more shrines)
Trance timings/health: constants at the top of Trance.java
New moves: add to Moves.java

## Art
`tools/` holds the Python scripts that draw every texture and model (James, shadow, sword, clothes, health bar):
`python3 tools/gen_james.py && python3 tools/gen_items.py && python3 tools/gen_shadow.py && python3 tools/gen_models.py`
`python3 tools/verify_mod.py` re-runs the offline checks.
