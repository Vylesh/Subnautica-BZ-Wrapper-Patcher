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

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vr_wrapper_profiles.json")

CSC_PATHS = [
    r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
]

WRAPPER_TEMPLATE = r'''
using System;
using System.Diagnostics;
using System.IO;

class VRWrapper {{
    static void Main(string[] args) {{
        string gameDir = AppDomain.CurrentDomain.BaseDirectory;
        string realExe = Path.Combine(gameDir, "{real_exe}");
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = realExe;
        psi.Arguments = "{vr_args}";
        psi.UseShellExecute = false;
        psi.WorkingDirectory = gameDir;
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
        self.title("VR Wrapper Maker")
        self.geometry("680x720")
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
        tk.Label(hdr, text="VR WRAPPER MAKER", font=self.f_title,
                 bg=BG, fg=ACCENT).pack(anchor="w")
        tk.Label(hdr, text="Bypass Steam's -vrmode none argument with a wrapper EXE",
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

        self._label("GAME EXE  (auto-detected)", pad, top=14)
        self.var_exe = tk.StringVar()
        self._entry(self, self.var_exe, fill="x", padx=pad)

        self._label("FORCED LAUNCH ARGUMENTS", pad, top=14)
        self.var_args = tk.StringVar(value="-vrmode openvr")
        self._entry(self, self.var_args, fill="x", padx=pad, fg=ACCENT)

        self._sep(pad, top=18)

        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=pad)
        self._btn(btns, "▶  APPLY WRAPPER", self.apply_wrapper,
                  ACCENT, side="left", w=210, bg=ACCENT_DIM)
        tk.Frame(btns, bg=BG, width=8).pack(side="left")
        self._btn(btns, "↩  UNDO",   self.undo_wrapper,  YELLOW, side="left", w=130)
        tk.Frame(btns, bg=BG, width=8).pack(side="left")
        self._btn(btns, "?  STATUS", self.check_status,  DIM,    side="left", w=120)

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
        self.log("Welcome! Select a profile or configure a new game.", DIM)

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
        icon = {"ok":"✓ ","warn":"⚠ ","err":"✗ ","dim":"  ","info":"  ","purple":"★ "}.get(tag, "")
        self.txt_log.insert("end", icon + msg + "\n", tag)
        self.txt_log.configure(state="disabled")
        self.txt_log.see("end")
        self.update_idletasks()

    def log_ok    (self, m): self.log(m, "ok")
    def log_warn  (self, m): self.log(m, "warn")
    def log_err   (self, m): self.log(m, "err")
    def log_dim   (self, m): self.log(m, "dim")
    def log_purple(self, m): self.log(m, "purple")

    def browse_folder(self):
        d = filedialog.askdirectory(title="Select game folder")
        if not d: return
        self.var_folder.set(d)
        self._auto_detect_exe(d)

    def _auto_detect_exe(self, folder):
        skip = {"crashhandler","uninstall","helper","launcher","unitycrash","subnautica32"}
        exes = []
        try:
            for f in os.listdir(folder):
                if f.lower().endswith(".exe") and not any(s in f.lower() for s in skip):
                    exes.append((os.path.getsize(os.path.join(folder, f)), f))
        except Exception:
            return
        if exes:
            exes.sort(reverse=True)
            self.var_exe.set(exes[0][1])
            self.log_dim(f"Auto-detected: {exes[0][1]}")

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

    def load_profile(self):
        name = self.var_profile.get()
        if name not in self.cfg["profiles"]:
            self.log_warn("No valid profile selected."); return
        self._apply_profile(name)
        self.cfg["last_profile"] = name
        save_config(self.cfg)
        self.log_purple(f"Profile loaded: {name}")

    def _apply_profile(self, name):
        p = self.cfg["profiles"][name]
        self.var_folder.set(p.get("folder", ""))
        self.var_exe.set(p.get("exe", ""))
        self.var_args.set(p.get("args", "-vrmode openvr"))

    def save_profile(self):
        folder, exe, args = self._get_inputs()
        if not folder or not exe or not args: return
        dlg = _InputDialog(self, "Save Profile", "Profile name:",
                           suggestion=os.path.basename(folder))
        name = dlg.result
        if not name: return
        self.cfg["profiles"][name] = {"folder": folder, "exe": exe, "args": args}
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

    def check_status(self):
        folder, exe, _ = self._get_inputs()
        if not folder or not exe: return
        base = os.path.splitext(exe)[0]
        self.log_dim("─── Status Check ─────────────────────")
        real_exe  = os.path.join(folder, f"{base}Real.exe")
        real_data = os.path.join(folder, f"{base}Real_Data")
        wrap_exe  = os.path.join(folder, exe)
        if os.path.exists(real_exe):
            self.log_ok(f"Real EXE found: {base}Real.exe")
        else:
            self.log_warn("Real EXE not found — wrapper not applied")
        if os.path.exists(real_data):
            self.log_ok("Real Data folder found")
        else:
            self.log_warn("Real Data folder missing")
        if os.path.exists(wrap_exe):
            size = os.path.getsize(wrap_exe)
            if size < 100_000:
                self.log_ok(f"Wrapper is active ({size//1024} KB — small = wrapper)")
            else:
                self.log_dim(f"Wrapper not applied ({size//1024} KB — original)")

    def apply_wrapper(self):
        folder, exe, args = self._get_inputs()
        if not folder or not exe or not args: return
        base      = os.path.splitext(exe)[0]
        orig_exe  = os.path.join(folder, exe)
        real_exe  = os.path.join(folder, f"{base}Real.exe")
        orig_data = os.path.join(folder, f"{base}_Data")
        real_data = os.path.join(folder, f"{base}Real_Data")

        self.log_dim("─── Applying Wrapper ─────────────────")

        if not os.path.exists(real_exe):
            if not os.path.exists(orig_exe):
                self.log_err(f"EXE not found: {exe}"); return
            os.rename(orig_exe, real_exe)
            self.log_ok(f"{exe} → {base}Real.exe")
        else:
            self.log_dim(f"{base}Real.exe already exists, skipped")

        if os.path.exists(orig_data) and not os.path.exists(real_data):
            os.rename(orig_data, real_data)
            self.log_ok(f"{base}_Data → {base}Real_Data")
        elif os.path.exists(real_data):
            self.log_dim(f"{base}Real_Data already exists, skipped")

        csc = next((p for p in CSC_PATHS if os.path.exists(p)), None)
        if not csc:
            self.log_err("csc.exe not found! Is .NET Framework 4.x installed?"); return
        self.log_ok(f"Compiler: {os.path.basename(csc)}")

        cs_code  = WRAPPER_TEMPLATE.format(real_exe=f"{base}Real.exe",
                                            vr_args=args.replace('"', '\\"'))
        cs_path  = os.path.join(folder, "_wrapper_temp.cs")
        out_path = os.path.join(folder, exe)

        with open(cs_path, "w", encoding="utf-8") as f:
            f.write(cs_code)

        self.log_dim("Compiling...")
        try:
            result = subprocess.run([csc, f"/out:{out_path}", "/target:winexe", cs_path],
                                    capture_output=True, text=True)
            if os.path.exists(out_path):
                self.log_ok(f"Wrapper EXE created: {exe}")
                self.log_ok("Done! You can now launch normally from Steam.")
                self._auto_save_profile(folder, exe, args)
            else:
                self.log_err("Compilation failed!")
                if result.stderr: self.log_warn(result.stderr[:300])
        except Exception as e:
            self.log_err(f"Compilation error: {e}")
        finally:
            if os.path.exists(cs_path):
                os.remove(cs_path)

    def _auto_save_profile(self, folder, exe, args):
        name = os.path.basename(folder)
        if name not in self.cfg["profiles"]:
            self.cfg["profiles"][name] = {"folder": folder, "exe": exe, "args": args}
            self.cfg["last_profile"] = name
            save_config(self.cfg)
            self._refresh_profile_menu()
            self.var_profile.set(name)
            self.log_purple(f"Profile auto-saved: '{name}'")

    def undo_wrapper(self):
        folder, exe, _ = self._get_inputs()
        if not folder or not exe: return
        base      = os.path.splitext(exe)[0]
        wrap_exe  = os.path.join(folder, exe)
        real_exe  = os.path.join(folder, f"{base}Real.exe")
        orig_data = os.path.join(folder, f"{base}_Data")
        real_data = os.path.join(folder, f"{base}Real_Data")

        self.log_dim("─── Undoing Wrapper ──────────────────")
        if not os.path.exists(real_exe):
            self.log_warn("Real EXE not found — wrapper already removed?"); return
        if os.path.exists(wrap_exe):
            os.remove(wrap_exe)
            self.log_ok(f"Wrapper deleted: {exe}")
        os.rename(real_exe, wrap_exe)
        self.log_ok(f"{base}Real.exe → {exe}")
        if os.path.exists(real_data) and not os.path.exists(orig_data):
            os.rename(real_data, orig_data)
            self.log_ok(f"{base}Real_Data → {base}_Data")
        self.log_ok("Undo complete.")

    def _get_inputs(self):
        folder = self.var_folder.get().strip()
        exe    = self.var_exe.get().strip()
        args   = self.var_args.get().strip()
        ok = True
        if not folder:
            self.log_err("Game folder not selected!"); ok = False
        elif not os.path.isdir(folder):
            self.log_err(f"Folder not found: {folder}"); ok = False
        if not exe and ok:
            self.log_err("EXE name is empty!"); ok = False
        if not args and ok:
            self.log_err("Arguments cannot be empty!"); ok = False
        if not ok: return None, None, None
        return folder, exe, args

    def on_close(self):
        folder = self.var_folder.get().strip()
        exe    = self.var_exe.get().strip()
        args   = self.var_args.get().strip()
        last   = self.cfg.get("last_profile", "")
        if last and last in self.cfg["profiles"]:
            self.cfg["profiles"][last] = {"folder": folder, "exe": exe, "args": args}
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
