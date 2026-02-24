# Subnautica: Below Zero — VR Argument Patcher

> Two methods to bypass Steam's forced `-vrmode none` for Unity-based VR games.

Some Unity games (like Subnautica: Below Zero) have VR support stripped at the binary level. Steam hardcodes `-vrmode none` before any launch options you set, making it impossible to enable VR through normal means. This repo provides two tools to work around that — pick the one that fits your setup.

---

## Which Tool Should I Use?

| | VR Launcher Maker | VR Wrapper Maker |
|---|---|---|
| **BepInEx mods** (Nautilus, RadialTabs, etc.) | ✅ Work | ❌ Break |
| **Game EXE renamed** | No | Yes |
| **Steam launch option required** | ✅ Yes | No |
| **Recommended** | ✅ Most users | Vanilla VR only |

**TL;DR:** Use **VR Launcher Maker** if you have any mods installed. Use **VR Wrapper Maker** only if you're running a completely vanilla game.

---

## Method 1 — VR Launcher Maker ⭐ Recommended

Creates a small `GameLauncher.exe` next to the real game. You tell Steam to launch the launcher instead of the game. The launcher ignores Steam's injected arguments and starts the actual game with your own.

> Think of it like SMAPI for Stardew Valley — a small entry point that takes control before the game starts.

```
Steam → SubnauticaZeroLauncher.exe   ← Steam's -vrmode none ends here (ignored)
              └─► SubnauticaZero.exe -vrmode openvr   ← real game, original name intact
                        └─► BepInEx sees "SubnauticaZero" → all mods load ✓
```

### Setup

1. Run `vr_launcher_maker.py`
2. Click **Browse** and select your game folder
3. The game EXE and launcher name are auto-filled
4. Click **▶ CREATE LAUNCHER**
5. Copy the Steam launch option shown in the yellow box (or click it to copy)
6. In Steam: right-click game → **Properties** → **Launch Options** → paste it

The launch option will look like:
```
"C:\...\SubnauticaZero\SubnauticaZeroLauncher.exe" %command%
```

### Removing

Click **↩ REMOVE** — only the launcher EXE is deleted. The game EXE is never touched.

---

## Method 2 — VR Wrapper Maker

Renames the original game EXE and replaces it with a tiny wrapper. Steam launches the wrapper, which in turn launches the renamed real EXE with your arguments. No Steam launch option changes needed.

> ⚠️ **Warning:** Renaming the game EXE breaks BepInEx mod process filters. Mods like Nautilus, RadialTabs, and Subnautica Config Handler will be skipped entirely. Only use this method if you play without mods.

```
Steam → SubnauticaZero.exe           ← wrapper (4 KB), Steam's args ignored
              └─► SubnauticaZeroReal.exe -vrmode openvr   ← renamed real game
```

### Setup

1. Run `vr_wrapper_maker.py`
2. Click **Browse** and select your game folder
3. Set your launch arguments (default: `-vrmode openvr`)
4. Click **▶ APPLY WRAPPER**

The tool will:
1. Rename `SubnauticaZero.exe` → `SubnauticaZeroReal.exe`
2. Rename `SubnauticaZero_Data\` → `SubnauticaZeroReal_Data\`
3. Compile and place a new wrapper `SubnauticaZero.exe`

Launch normally from Steam — no launch option changes needed.

### Undoing

Click **↩ UNDO** — the wrapper is deleted and all renames are reversed.

---

## Requirements

- **Python 3.x** (tkinter included in standard Windows installs)
- **.NET Framework 4.x** (pre-installed on Windows 10/11)
- **SteamVR** running before launching the game

## Installation

```
git clone https://github.com/yourusername/vr-argument-patcher
cd vr-argument-patcher
python vr_launcher_maker.py   # or vr_wrapper_maker.py
```

No additional packages needed.

---

## Profiles

Both tools save game configurations as named profiles in a JSON file next to the script. The last used profile is auto-loaded on startup.

| Action | Description |
|--------|-------------|
| **Load** | Load a saved profile |
| **Save** | Save current fields as a named profile |
| **Delete** | Remove a profile |

---

## Tested With

| Game | Arguments |
|------|-----------|
| Subnautica: Below Zero | `-vrmode openvr` |
| Subnautica (original) | `-vrmode openvr` |

Both tools are general-purpose and work with any Unity game that accepts command-line VR arguments.

---

## Troubleshooting

**`csc.exe not found`**
.NET Framework 4.x is required. It comes pre-installed on Windows 10/11 but can be downloaded from [Microsoft](https://dotnet.microsoft.com/en-us/download/dotnet-framework).

**Mods not loading (Nautilus, RadialTabs, etc.)**
You're using the Wrapper method. Switch to **VR Launcher Maker** instead — it keeps the game EXE name intact so BepInEx process filters work correctly.

**Game still launches in non-VR mode**
- Make sure SteamVR is running *before* launching the game
- If using VR Launcher Maker, confirm the Steam launch option is set correctly
- Check `BepInEx\LogOutput.log` — the command line should show `-vrmode openvr`, not `-vrmode none`

**`DllNotFoundException: OVRPlugin`**
The game is missing `OVRPlugin.dll`. Copy it from the original Subnautica installation:
```
Subnautica\Subnautica_Data\Plugins\OVRPlugin.dll
  → SubnauticaZero_Data\Plugins\OVRPlugin.dll
```

**Wrapper only: `There should be 'GameNameReal_Data' folder`**
The `_Data` folder rename failed. Manually rename `SubnauticaZero_Data` → `SubnauticaZeroReal_Data`, then re-apply.

---

## License

Boost Software License - Version 1.0
