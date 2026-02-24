import tkinter as tk
from tkinter import filedialog, font, messagebox
import os
import subprocess
import json
from datetime import datetime

BG         = "#0a0a0f"
PANEL      = "#12121a"
BORDER     = "#1e1e2e"
ACCENT     = "#64dcaa"
ACCENT_DIM = "#1a3d2e"
TEXT       = "#d0d0e0"
DIM        = "#555570"
RED        = "#e05050"
YELLOW     = "#e0b83c"
BLUE       = "#6090e0"
PURPLE     = "#a080e0"

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vr_launcher_profiles.json")

CSC_PATHS = [
    r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
]

# Launcher template - launches the real game EXE directly (no rename needed)
LAUNCHER_TEMPLATE = r'''
using System;
using System.Diagnostics;
using System.IO;

class VRLauncher {{
    static void Main(string[] args) {{
        // Steam passes its own args (including -vrmode none) via %command%.
        // We ignore them entirely and launch with our own forced arguments.
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        string realExe = Path.Combine(dir, "{game_exe}");
        if (!File.Exists(realExe)) {{
            Console.WriteLine("[VRLauncher] ERROR: " + realExe + " not found!");
            Console.ReadLine();
            return;
        }}
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = realExe;
        psi.Arguments = "{vr_args}";
        psi.UseShellExecute = false;
        psi.WorkingDirectory = dir;
        Process.Start(psi);
    }}
}}
'''


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"profiles": {}, "last_profile": ""}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Config save error: {e}")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VR Launcher Maker")
        self.geometry("700x760")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.cfg = load_config()
        self.setup_fonts()
        self.build_ui()
        self.load_last_profile()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_fonts(self):
        self.f_title  = font.Font(family="Consolas", size=15, weight="bold")
        self.f_label  = font.Font(family="Consolas", size=8)
        self.f_input  = font.Font(family="Consolas", size=9)
        self.f_btn    = font.Font(family="Consolas", size=9, weight="bold")
        self.f_log    = font.Font(family="Consolas", size=8)
        self.f_sub    = font.Font(family="Consolas", size=9)

    def build_ui(self):
        pad = 24

        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=pad, pady=(20, 0))
        tk.Label(hdr, text="VR LAUNCHER MAKER", font=self.f_title,
                 bg=BG, fg=ACCENT).pack(anchor="w")
        tk.Label(hdr, text="Creates a launcher EXE that bypasses Steam's -vrmode none",
                 font=self.f_sub, bg=BG, fg=DIM).pack(anchor="w", pady=(2, 0))

        self._sep(pad)

        self._label("SAVED PROFILES", pad)
        prof_row = tk.Frame(self, bg=BG)
        prof_row.pack(fill="x", padx=pad, pady=(4, 0))

        self.var_profile = tk.StringVar()
        self.combo_profiles = tk.OptionMenu(prof_row, self.var_profile, "")
        self.combo_profiles.config(
            font=self.f_input, bg=PANEL, fg=TEXT,
            activebackground=BORDER, activeforeground=ACCENT,
            highlightthickness=1, highlightbackground=BORDER,
            relief="flat", bd=0, width=28
        )
        self.combo_profiles["menu"].config(
            bg=PANEL, fg=TEXT, activebackground=ACCENT_DIM,
            activeforeground=ACCENT, font=self.f_input
        )
        self.combo_profiles.pack(side="left", ipady=4)

        tk.Frame(prof_row, bg=BG, width=8).pack(side="left")
        self._btn(prof_row, "Load",   self.load_profile,   ACCENT,  side="left", w=70)
        tk.Frame(prof_row, bg=BG, width=6).pack(side="left")
        self._btn(prof_row, "Save",   self.save_profile,   PURPLE,  side="left", w=70)
        tk.Frame(prof_row, bg=BG, width=6).pack(side="left")
        self._btn(prof_row, "Delete", self.delete_profile, RED,     side="left", w=70)

        self._sep(pad, top=14)

        self._label("GAME FOLDER", pad)
        row1 = tk.Frame(self, bg=BG)
        row1.pack(fill="x", padx=pad, pady=(4, 0))
        self.var_folder = tk.StringVar()
        self._entry(row1, self.var_folder, side="left", expand=True, padx=(0, 8))
        self._btn(row1, "Browse", self.browse_folder, ACCENT, side="left", w=90)

        self._label("GAME EXE  (auto-detected, this will NOT be renamed)", pad, top=14)
        self.var_exe = tk.StringVar()
        self._entry(self, self.var_exe, fill="x", padx=pad)

        self._label("LAUNCHER EXE NAME  (will be created next to game EXE)", pad, top=14)
        self.var_launcher_name = tk.StringVar()
        self._entry(self, self.var_launcher_name, fill="x", padx=pad, fg=YELLOW)

        self._label("FORCED LAUNCH ARGUMENTS", pad, top=14)
        self.var_args = tk.StringVar(value="-vrmode openvr")
        self._entry(self, self.var_args, fill="x", padx=pad, fg=ACCENT)

        # Steam hint box
        self._sep(pad, top=14)
        hint_frame = tk.Frame(self, bg=PANEL, bd=0,
                              highlightthickness=1, highlightbackground=BORDER)
        hint_frame.pack(fill="x", padx=pad, pady=(6, 0))
        tk.Label(hint_frame, text="STEAM LAUNCH OPTIONS", font=self.f_label,
                 bg=PANEL, fg=DIM).pack(anchor="w", padx=10, pady=(8, 2))
        self.var_hint = tk.StringVar(value="← Apply launcher first to see the Steam launch option")
        hint_entry = tk.Entry(hint_frame, textvariable=self.var_hint,
                              font=self.f_input, bg="#0d0d16", fg=YELLOW,
                              insertbackground=ACCENT, relief="flat",
                              state="readonly",
                              readonlybackground="#0d0d16",
                              highlightthickness=0)
        hint_entry.pack(fill="x", padx=10, pady=(0, 8), ipady=4)
        hint_entry.bind("<Button-1>", self._copy_hint)
        tk.Label(hint_frame, text="Click to copy  •  Paste in: Steam → Right-click game → Properties → Launch Options",
                 font=self.f_label, bg=PANEL, fg=DIM).pack(anchor="w", padx=10, pady=(0, 8))

        self._sep(pad, top=14)

        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=pad)
        self._btn(btns, "▶  CREATE LAUNCHER", self.apply_launcher,
                  ACCENT, side="left", w=210, bg=ACCENT_DIM)
        tk.Frame(btns, bg=BG, width=8).pack(side="left")
        self._btn(btns, "↩  REMOVE",  self.remove_launcher, YELLOW, side="left", w=130)
        tk.Frame(btns, bg=BG, width=8).pack(side="left")
        self._btn(btns, "?  STATUS",  self.check_status,    DIM,    side="left", w=120)

        self._sep(pad, top=16)

        self._label("LOG", pad)
        log_frame = tk.Frame(self, bg=BORDER, bd=0)
        log_frame.pack(fill="both", expand=True, padx=pad, pady=(4, pad))

        self.txt_log = tk.Text(log_frame, font=self.f_log,
                               bg="#08080d", fg=TEXT,
                               insertbackground=ACCENT, relief="flat",
                               state="disabled", wrap="word",
                               selectbackground=ACCENT_DIM)
        scroll = tk.Scrollbar(log_frame, command=self.txt_log.yview,
                              bg=PANEL, troughcolor=BG, relief="flat")
        self.txt_log.configure(yscrollcommand=scroll.set)
        self.txt_log.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        scroll.pack(side="right", fill="y")

        for tag, color in [("ok", ACCENT), ("warn", YELLOW), ("err", RED),
                           ("dim", DIM), ("info", BLUE), ("time", DIM), ("purple", PURPLE)]:
            self.txt_log.tag_config(tag, foreground=color)

        self._refresh_profile_menu()
        self.log("Welcome! Select a profile or configure a new game.", "dim")

    def _sep(self, pad, top=14):
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=pad, pady=(top, 0))

    def _label(self, text, pad, top=0):
        tk.Label(self, text=text, font=self.f_label,
                 bg=BG, fg=DIM).pack(anchor="w", padx=pad, pady=(top, 0))

    def _entry(self, parent, var, side=None, fill=None, padx=0, expand=False, fg=TEXT):
        e = tk.Entry(parent, textvariable=var, font=self.f_input,
                     bg=PANEL, fg=fg, insertbackground=ACCENT, relief="flat",
                     highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)
        kw = {"ipady": 5}
        if side:   kw["side"]   = side
        if fill:   kw["fill"]   = fill
        if expand: kw["expand"] = True
        if padx:   kw["padx"]   = padx
        if not side and fill: kw["pady"] = (4, 0)
        e.pack(**kw)
        return e

    def _btn(self, parent, text, cmd, color, side=None, w=None, bg=PANEL):
        b = tk.Button(parent, text=text, command=cmd, font=self.f_btn,
                      bg=bg, fg=color, activebackground=color, activeforeground=BG,
                      relief="flat", cursor="hand2",
                      highlightthickness=1, highlightbackground=color, bd=0)
        kw = {"ipady": 5}
        if side:
            b.pack(side=side, **kw)
            if w: b.config(width=w // 9)
        else:
            b.pack(fill="x", **kw)
        return b

    def log(self, msg, tag="info"):
        self.txt_log.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert("end", f"[{ts}] ", "time")
        icon = {"ok": "✓ ", "warn": "⚠ ", "err": "✗ ", "dim": "  ",
                "info": "  ", "purple": "★ "}.get(tag, "")
        self.txt_log.insert("end", icon + msg + "\n", tag)
        self.txt_log.configure(state="disabled")
        self.txt_log.see("end")
        self.update_idletasks()

    def log_ok    (self, m): self.log(m, "ok")
    def log_warn  (self, m): self.log(m, "warn")
    def log_err   (self, m): self.log(m, "err")
    def log_dim   (self, m): self.log(m, "dim")
    def log_purple(self, m): self.log(m, "purple")

    def _copy_hint(self, _event=None):
        hint = self.var_hint.get()
        if "Apply" in hint:
            return
        self.clipboard_clear()
        self.clipboard_append(hint)
        self.log_ok("Steam launch option copied to clipboard!")

    def browse_folder(self):
        d = filedialog.askdirectory(title="Select game folder")
        if not d: return
        self.var_folder.set(d)
        self._auto_detect_exe(d)

    def _auto_detect_exe(self, folder):
        skip = {"crashhandler", "uninstall", "helper", "launcher",
                "unitycrash", "subnautica32"}
        exes = []
        try:
            for f in os.listdir(folder):
                if f.lower().endswith(".exe") and not any(s in f.lower() for s in skip):
                    exes.append((os.path.getsize(os.path.join(folder, f)), f))
        except Exception:
            return
        if exes:
            exes.sort(reverse=True)
            game_exe = exes[0][1]
            self.var_exe.set(game_exe)
            base = os.path.splitext(game_exe)[0]
            self.var_launcher_name.set(f"{base}Launcher.exe")
            self.log_dim(f"Auto-detected: {game_exe}")
            self.log_dim(f"Launcher will be: {base}Launcher.exe")

    def _refresh_profile_menu(self):
        menu = self.combo_profiles["menu"]
        menu.delete(0, "end")
        profiles = list(self.cfg["profiles"].keys())
        if not profiles:
            menu.add_command(label="(no profiles)", command=lambda: None)
            self.var_profile.set("(no profiles)")
        else:
            for name in profiles:
                menu.add_command(label=name, command=lambda n=name: self.var_profile.set(n))
            last = self.cfg.get("last_profile", "")
            self.var_profile.set(last if last in profiles else profiles[0])

    def load_last_profile(self):
        last = self.cfg.get("last_profile", "")
        if last and last in self.cfg["profiles"]:
            self._apply_profile(last)
            self.log_purple(f"Auto-loaded profile: {last}")
            self._update_hint()

    def load_profile(self):
        name = self.var_profile.get()
        if name not in self.cfg["profiles"]:
            self.log_warn("No valid profile selected."); return
        self._apply_profile(name)
        self.cfg["last_profile"] = name
        save_config(self.cfg)
        self._update_hint()
        self.log_purple(f"Profile loaded: {name}")

    def _apply_profile(self, name):
        p = self.cfg["profiles"][name]
        self.var_folder.set(p.get("folder", ""))
        self.var_exe.set(p.get("exe", ""))
        self.var_launcher_name.set(p.get("launcher_name", ""))
        self.var_args.set(p.get("args", "-vrmode openvr"))

    def save_profile(self):
        folder, exe, launcher_name, args = self._get_inputs()
        if not folder: return
        dlg = _InputDialog(self, "Save Profile", "Profile name:",
                           suggestion=os.path.basename(folder))
        name = dlg.result
        if not name: return
        self.cfg["profiles"][name] = {
            "folder": folder, "exe": exe,
            "launcher_name": launcher_name, "args": args
        }
        self.cfg["last_profile"] = name
        save_config(self.cfg)
        self._refresh_profile_menu()
        self.var_profile.set(name)
        self.log_purple(f"Profile saved: '{name}'")

    def delete_profile(self):
        name = self.var_profile.get()
        if name not in self.cfg["profiles"]:
            self.log_warn("No valid profile selected."); return
        if not messagebox.askyesno("Delete Profile", f"Delete '{name}'?"):
            return
        del self.cfg["profiles"][name]
        if self.cfg.get("last_profile") == name:
            self.cfg["last_profile"] = ""
        save_config(self.cfg)
        self._refresh_profile_menu()
        self.log_warn(f"Profile deleted: '{name}'")

    def _update_hint(self):
        folder = self.var_folder.get().strip()
        launcher = self.var_launcher_name.get().strip()
        if folder and launcher:
            path = os.path.join(folder, launcher)
            self.var_hint.set(f'"{path}" %command%')

    def check_status(self):
        folder, exe, launcher_name, _ = self._get_inputs()
        if not folder: return
        self.log_dim("─── Status Check ─────────────────────")
        launcher_path = os.path.join(folder, launcher_name)
        game_path     = os.path.join(folder, exe)

        if os.path.exists(launcher_path):
            size = os.path.getsize(launcher_path)
            self.log_ok(f"Launcher active: {launcher_name} ({size // 1024} KB)")
        else:
            self.log_warn(f"Launcher not found: {launcher_name}")

        if os.path.exists(game_path):
            self.log_ok(f"Game EXE intact: {exe}")
        else:
            self.log_err(f"Game EXE missing: {exe}")

        hint = self.var_hint.get()
        if hint and "Apply" not in hint:
            self.log_dim(f"Steam option: {hint}")

    def apply_launcher(self):
        folder, exe, launcher_name, args = self._get_inputs()
        if not folder: return

        game_path     = os.path.join(folder, exe)
        launcher_path = os.path.join(folder, launcher_name)

        self.log_dim("─── Creating Launcher ────────────────")

        if not os.path.exists(game_path):
            self.log_err(f"Game EXE not found: {exe}"); return
        self.log_ok(f"Game EXE found: {exe} (will NOT be renamed)")

        csc = next((p for p in CSC_PATHS if os.path.exists(p)), None)
        if not csc:
            self.log_err("csc.exe not found! Is .NET Framework 4.x installed?"); return
        self.log_ok(f"Compiler: {os.path.basename(csc)}")

        cs_code = LAUNCHER_TEMPLATE.format(
            game_exe=exe,
            vr_args=args.replace('"', '\\"')
        )
        cs_path = os.path.join(folder, "_vrlauncher_temp.cs")

        with open(cs_path, "w", encoding="utf-8") as f:
            f.write(cs_code)

        self.log_dim(f"Compiling {launcher_name}...")
        try:
            result = subprocess.run(
                [csc, f"/out:{launcher_path}", "/target:exe", "/optimize+", cs_path],
                capture_output=True, text=True
            )
            if os.path.exists(launcher_path):
                size = os.path.getsize(launcher_path)
                self.log_ok(f"Launcher created: {launcher_name} ({size // 1024} KB)")
                self._update_hint()
                hint = self.var_hint.get()
                self.log_ok("─── Steam Launch Options ─────────────")
                self.log("  " + hint, "warn")
                self.log_ok("Paste the above into Steam → Right-click game → Properties → Launch Options")
                self.log_ok("Click the yellow box above to copy automatically.")
                self._auto_save_profile(folder, exe, launcher_name, args)
            else:
                self.log_err("Compilation failed!")
                if result.stderr:
                    self.log_warn(result.stderr[:400])
        except Exception as e:
            self.log_err(f"Compilation error: {e}")
        finally:
            if os.path.exists(cs_path):
                os.remove(cs_path)

    def _auto_save_profile(self, folder, exe, launcher_name, args):
        name = os.path.basename(folder)
        self.cfg["profiles"][name] = {
            "folder": folder, "exe": exe,
            "launcher_name": launcher_name, "args": args
        }
        self.cfg["last_profile"] = name
        save_config(self.cfg)
        self._refresh_profile_menu()
        self.var_profile.set(name)
        self.log_purple(f"Profile auto-saved: '{name}'")

    def remove_launcher(self):
        folder, exe, launcher_name, _ = self._get_inputs()
        if not folder: return
        launcher_path = os.path.join(folder, launcher_name)
        self.log_dim("─── Removing Launcher ────────────────")
        if not os.path.exists(launcher_path):
            self.log_warn(f"Launcher not found: {launcher_name}"); return
        os.remove(launcher_path)
        self.log_ok(f"Deleted: {launcher_name}")
        self.log_ok("Game EXE is untouched.")
        self.var_hint.set("← Apply launcher first to see the Steam launch option")

    def _get_inputs(self):
        folder        = self.var_folder.get().strip()
        exe           = self.var_exe.get().strip()
        launcher_name = self.var_launcher_name.get().strip()
        args          = self.var_args.get().strip()
        ok = True

        if not folder:
            self.log_err("Game folder not selected!"); ok = False
        elif not os.path.isdir(folder):
            self.log_err(f"Folder not found: {folder}"); ok = False

        if ok and not exe:
            self.log_err("EXE name is empty!"); ok = False

        if ok and not launcher_name:
            self.log_err("Launcher EXE name is empty!"); ok = False
        elif ok and not launcher_name.lower().endswith(".exe"):
            launcher_name += ".exe"
            self.var_launcher_name.set(launcher_name)

        if ok and not args:
            self.log_err("Arguments cannot be empty!"); ok = False

        if not ok:
            return None, None, None, None
        return folder, exe, launcher_name, args

    def on_close(self):
        folder        = self.var_folder.get().strip()
        exe           = self.var_exe.get().strip()
        launcher_name = self.var_launcher_name.get().strip()
        args          = self.var_args.get().strip()
        last          = self.cfg.get("last_profile", "")
        if last and last in self.cfg["profiles"]:
            self.cfg["profiles"][last] = {
                "folder": folder, "exe": exe,
                "launcher_name": launcher_name, "args": args
            }
            save_config(self.cfg)
        self.destroy()


class _InputDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, suggestion=""):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.result = None
        self.grab_set()

        f = font.Font(family="Consolas", size=9)
        tk.Label(self, text=prompt, font=f, bg=BG, fg=TEXT).pack(
            padx=20, pady=(16, 4), anchor="w")

        self.var = tk.StringVar(value=suggestion)
        e = tk.Entry(self, textvariable=self.var, font=f,
                     bg=PANEL, fg=TEXT, insertbackground=ACCENT, relief="flat",
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT, width=34)
        e.pack(padx=20, ipady=5)
        e.select_range(0, "end")
        e.focus()

        row = tk.Frame(self, bg=BG)
        row.pack(pady=14, padx=20, fill="x")
        fb = font.Font(family="Consolas", size=9, weight="bold")
        tk.Button(row, text="OK", command=self._ok, font=fb,
                  bg=ACCENT_DIM, fg=ACCENT, activebackground=ACCENT,
                  activeforeground=BG, relief="flat", cursor="hand2",
                  highlightthickness=1, highlightbackground=ACCENT,
                  bd=0).pack(side="left", ipadx=16, ipady=4)
        tk.Frame(row, bg=BG, width=8).pack(side="left")
        tk.Button(row, text="Cancel", command=self.destroy, font=f,
                  bg=PANEL, fg=DIM, activebackground=BORDER, activeforeground=TEXT,
                  relief="flat", cursor="hand2",
                  highlightthickness=1, highlightbackground=BORDER,
                  bd=0).pack(side="left", ipadx=10, ipady=4)

        self.bind("<Return>", lambda _: self._ok())
        self.bind("<Escape>", lambda _: self.destroy())
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        self.wait_window()

    def _ok(self):
        self.result = self.var.get().strip()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
