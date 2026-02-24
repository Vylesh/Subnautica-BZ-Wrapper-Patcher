# Subnautica: Bellow Zero Harcoded Arguments Patcher for VR

> Bypass Steam's forced `-vrmode none` argument for Unity-based VR games.

## NOTE : IF YOU GONNA USE NAUTILUS ETC. USE VR LAUNCHER MAKER INSTEAD. WRAPPER METHOD FOR ONLY SUBMERSED VR GAMEPLAY AND NAUTILUS WILL NOT WORK. WHILE USING VR LAUNCHER NEVER FORGET THE PUT STEAM STARTING ARGUMENTS GIVEN IN LAUNCHER MAKER OR LAUNCHER WILL NEVER WORK. THINK VR LAUNCHER LIKE SMAPI FOR SUBNAUTICA

Some Unity games (like Subnautica: Below Zero) have VR support removed at the binary level and are launched by Steam with `-vrmode none` hardcoded — overriding any launch options you set. VR Wrapper Creator solves this by replacing the game's EXE with a lightweight wrapper that ignores Steam's arguments and launches the real executable with your own.

---

## How It Works

Steam launches `GameName.exe` → the wrapper intercepts → launches `GameNameReal.exe -vrmode openvr` (or any arguments you choose).

```
Steam
  └─► GameName.exe          ← wrapper (4 KB)
        └─► GameNameReal.exe -vrmode openvr   ← actual game
```

The wrapper is a compiled C# `.exe` that does nothing but call the real executable with your forced arguments. No DLL injection, no hooks, no background processes.

---

## Requirements

- **Python 3.x** (with `tkinter` — included in standard Windows installs)
- **.NET Framework 4.x** (pre-installed on Windows 10/11)
- **SteamVR** running before launching the game

---

## Installation

```
git clone https://github.com/yourusername/vr-wrapper-creator
cd vr-wrapper-creator
python vr_wrapper_maker.py
```

No additional packages needed.

---

## Usage

### 1. Select Game Folder

Click **Browse** and navigate to your game's installation directory (e.g. `steamapps\common\SubnauticaZero`). The EXE is auto-detected.

### 2. Set Arguments

The default is `-vrmode openvr`. Change this to whatever arguments your game needs.

### 3. Apply Wrapper

Click **▶ APPLY WRAPPER**. The tool will:

1. Rename `GameName.exe` → `GameNameReal.exe`
2. Rename `GameName_Data\` → `GameNameReal_Data\`
3. Compile and place a wrapper `GameName.exe` in its place

After a successful apply, a profile is automatically saved so you don't have to re-enter anything next time.

### 4. Launch

Launch the game normally from Steam. The wrapper will run and pass your arguments to the real executable.

---

## Profiles

Your game configurations are saved as named profiles in `vr_wrapper_profiles.json` (stored next to the script). The last used profile is auto-loaded on startup.

| Action | Description |
|--------|-------------|
| **Load** | Load a saved profile into the fields |
| **Save** | Save current fields as a named profile |
| **Delete** | Remove a profile |

---

## Undoing

Click **↩ UNDO** to reverse the process — the wrapper is deleted and the original EXE and `_Data` folder are restored to their original names.

---

## Status Check

Click **? STATUS** at any time to see whether the wrapper is currently active for the selected game.

---

## Tested With

| Game | Arguments |
|------|-----------|
| Subnautica: Below Zero | `-vrmode openvr` |
| Subnautica (original) | `-vrmode openvr` |

Works with any Unity game that accepts command-line VR arguments.

---

## Troubleshooting

**`csc.exe not found`**
Make sure .NET Framework 4.x is installed. It comes pre-installed on Windows 10/11 but can be downloaded from [Microsoft](https://dotnet.microsoft.com/en-us/download/dotnet-framework).

**Game still launches in non-VR mode**
- Make sure SteamVR is running and your headset is active *before* launching the game
- Check `BepInEx\LogOutput.log` and confirm the command line shows your wrapper arguments, not `-vrmode none`
- Run **? STATUS** to confirm the wrapper is actually in place

**`DllNotFoundException: OVRPlugin`**
The game is missing `OVRPlugin.dll`. Copy it from the original Subnautica (1) installation:
```
Subnautica\Subnautica_Data\Plugins\OVRPlugin.dll
→ YourGame_Data\Plugins\OVRPlugin.dll
```

**Game says `There should be 'GameNameReal_Data' folder`**
The `_Data` folder rename failed or was skipped. Manually rename `GameName_Data` → `GameNameReal_Data`, then re-apply.

---

## How the Wrapper Is Built

The tool compiles the following C# code at runtime using `csc.exe`:

```csharp
using System;
using System.Diagnostics;
using System.IO;

class VRWrapper {
    static void Main(string[] args) {
        string gameDir = AppDomain.CurrentDomain.BaseDirectory;
        string realExe = Path.Combine(gameDir, "GameNameReal.exe");
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = realExe;
        psi.Arguments = "-vrmode openvr";
        psi.UseShellExecute = false;
        psi.WorkingDirectory = gameDir;
        Process.Start(psi);
    }
}
```

The generated wrapper is ~4 KB. Steam's arguments never reach the real executable.

---

## License

MIT
