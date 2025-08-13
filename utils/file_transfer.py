import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

REPO_PATH = os.getcwd()

# ---------------- Git Command Helper ----------------


def run_git_cmd(args):
    """Run git command and return stdout."""
    result = subprocess.run(["git"] + args, cwd=REPO_PATH,
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()

# ---------------- Main Transfer Logic ----------------


def transfer_files():
    try:
        source_branch = src_branch.get().strip()
        target_branch = tgt_branch.get().strip()
        selected_files = file_list.get(0, tk.END)

        if not source_branch or not target_branch:
            messagebox.showerror(
                "Error", "Please select both source and target branches.")
            return
        if not selected_files:
            messagebox.showerror("Error", "Please select at least one file.")
            return

        # Ensure current branch is source branch
        current_branch = run_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"])
        if current_branch != source_branch:
            messagebox.showerror(
                "Error", f"Must be on '{source_branch}' branch to run this.")
            return

        # Switch to target branch & pull latest
        run_git_cmd(["checkout", target_branch])
        run_git_cmd(["pull", "origin", target_branch])

        # Get git diff output for validation
        diff_output = run_git_cmd(
            ["diff", "--name-status", f"{target_branch}..{source_branch}"])
        diff_lines = [line for line in diff_output.split(
            "\n") if line.startswith(("A", "M"))]

        valid_files = []
        invalid_files = []

        for f in selected_files:
            if any(line.split("\t")[1] == f for line in diff_lines):
                valid_files.append(f)
            else:
                invalid_files.append(f)

        if not valid_files:
            msg = "No valid files (A/M status) provided. Nothing to update."
            if invalid_files:
                msg += "\nInvalid or non-matching files:\n" + \
                    "\n".join(invalid_files)
            messagebox.showinfo("Info", msg)
            run_git_cmd(["checkout", source_branch])
            return

        # Checkout valid files from source
        for f in valid_files:
            run_git_cmd(["checkout", source_branch, "--", f])
            run_git_cmd(["add", f])

        if invalid_files:
            messagebox.showwarning(
                "Warning", "These files were skipped:\n" + "\n".join(invalid_files))

        # Commit & push
        commit_msg = f"Updating {target_branch} with released files from {source_branch}"
        run_git_cmd(["commit", "-m", commit_msg])
        run_git_cmd(["push", "origin", target_branch])

        # Switch back
        run_git_cmd(["checkout", source_branch])

        messagebox.showinfo("Success",
                            f"{target_branch} updated with {len(valid_files)} files from {source_branch}.\nProcessed:\n" + "\n".join(valid_files))

    except RuntimeError as e:
        messagebox.showerror("Git Error", str(e))
    except Exception as e:
        messagebox.showerror("Error", str(e))

# ---------------- File Picker ----------------


def pick_files():
    parent_dir = os.path.dirname(REPO_PATH)
    files = filedialog.askopenfilenames(
        initialdir=parent_dir, title="Select Files to Transfer")
    for f in files:
        rel_path = os.path.relpath(f, parent_dir)
        file_list.insert(tk.END, rel_path)

# ---------------- Branch Loader ----------------


def get_branches():
    return [b.strip("* ").strip() for b in run_git_cmd(["branch", "--list"]).splitlines()]


# ---------------- GUI Setup ----------------
root = tk.Tk()
root.title("Git File Transfer Tool")
root.geometry("600x600")
root.configure(bg="#f4faff")  # very light bluish background

# ---------- Modern Theme ----------
style = ttk.Style()
style.theme_use("clam")

# General widget styling
style.configure("TLabel", background="#f4faff", font=("Segoe UI", 11))
style.configure("TButton",
                font=("Segoe UI", 11, "bold"),
                background="#cce7ff",
                foreground="#003366",
                borderwidth=1,
                focusthickness=3,
                focuscolor="none",
                padding=8)
style.map("TButton",
          background=[("active", "#99d0ff")])

style.configure("TCombobox",
                fieldbackground="#ffffff",
                background="#e6f3ff",
                padding=5)

# ---------- Layout ----------
branches = get_branches()

# Title
ttk.Label(root, text="📂 Git File Transfer Tool", font=("Segoe UI", 18, "bold"), background="#f4faff").grid(
    row=0, column=0, columnspan=2, pady=(15, 25))

# Source branch
ttk.Label(root, text="Source Branch:").grid(
    row=1, column=0, sticky="e", padx=10, pady=5)
src_branch = ttk.Combobox(root, values=branches, width=40, state="readonly")
src_branch.set(branches[0])
src_branch.grid(row=1, column=1, pady=5, sticky="w")

# Target branch
ttk.Label(root, text="Target Branch:").grid(
    row=2, column=0, sticky="e", padx=10, pady=5)
tgt_branch = ttk.Combobox(root, values=branches, width=40, state="readonly")
tgt_branch.set(branches[1])
tgt_branch.grid(row=2, column=1, pady=5, sticky="w")

# File selection button
ttk.Button(root, text="📁 Select Files", command=pick_files).grid(
    row=3, column=0, columnspan=2, pady=10)

# File list with scrollbar
frame = ttk.Frame(root)
frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

scrollbar = ttk.Scrollbar(frame)
scrollbar.pack(side="right", fill="y")

file_list = tk.Listbox(frame, width=80, height=15, selectmode=tk.MULTIPLE,
                       yscrollcommand=scrollbar.set, font=("Consolas", 10))
file_list.pack(side="left", fill="both", expand=True)
scrollbar.config(command=file_list.yview)

# Transfer button
ttk.Button(root, text="🚀 Transfer Files", command=transfer_files).grid(
    row=5, column=0, columnspan=2, pady=20)

# Status bar
status_label = ttk.Label(root, text="Ready", relief="sunken",
                         anchor="w", background="#e6f3ff", font=("Segoe UI", 10))
status_label.grid(row=6, column=0, columnspan=2,
                  sticky="we", padx=5, pady=(0, 5))

root.mainloop()
