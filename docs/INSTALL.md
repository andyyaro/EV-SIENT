# Installing the desktop platform

Read this first: **your operating system will try to stop you opening this, and it is right
to.** Nothing here is signed by a publisher your machine recognises. That is a real limitation
of this project, not a bug in your Mac or PC, and the instructions below tell you exactly what
you will see and exactly what to click.

**Do not disable Gatekeeper or SmartScreen system-wide.** You will find advice online telling
you to run `sudo spctl --master-disable` or to turn SmartScreen off. That advice would make
every future download on your machine less safe in order to open one file, and it is not
necessary — the per-application steps below are enough. This guide will never ask you to do it.

---

## What you are installing

A portable directory and a run script. Not an application bundle — the platform is a local
web server you start from a script and view in your browser (DEC-015).

**It ships synthetic data.** Every site in it is invented and describes no real building
(DEC-016, DEC-020). Running it produces synthetic results, and the contract it writes says
`synthetic_inputs: true` in its own manifest so nobody can mistake its numbers for the study's.

**You need Python 3.11 or newer** already installed. The run script checks, and says so if it
is missing rather than failing obscurely.

---

## macOS

Measured on **macOS 26.5.1**. The click-path has changed across recent macOS versions; this is
what the current one does.

1. Download the `.zip` beside its `.sha256` file.
2. **Verify it** before opening anything:
   ```bash
   shasum -a 256 -c fcf-platform-<version>-macos.zip.sha256
   ```
   It should print `OK`. If it does not, stop — the download is not what was published.
3. Unzip it. Double-click **`run-platform.command`**.
4. **macOS will refuse it.** You will see a dialog saying it *"Not Opened — Apple could not
   verify … is free of malware."* with **Move to Trash** and **Done**. Click **Done**. Do not
   click Move to Trash.
5. Open **System Settings → Privacy & Security**. Scroll to the **Security** section. There
   will be a line naming `run-platform.command` and an **Open Anyway** button. Click it.
6. Authenticate as an administrator when asked.
7. Double-click `run-platform.command` again. It will now run, and macOS will not ask again for
   this file.

### Why it does that, stated plainly

Apple's Gatekeeper allows apps from identified developers — meaning a paid Apple Developer
account and a notarization step where Apple scans the artifact. **This project has neither.**

**The artifact you download carries no signature at all.** This guide previously said it was
ad-hoc signed. It is not, and the correction is worth stating precisely because the earlier
sentence was a claim about the artifact rather than a measurement of it.

The packaging job did run `codesign -s -`, but ad-hoc signing a *shell script* stores the
signature in extended attributes rather than inside the file, and the very next step — `zip` —
discards extended attributes. Measured on macOS 26.5.1 by building the release artifact and
extracting it the way a recipient does: the staging file carries
`com.apple.cs.CodeDirectory`/`CodeRequirements`/`CodeSignature`; after `zip` and `unzip` it
carries none of them and `codesign -dv` reports *"code object is not signed at all"*. The
signing step destroyed its own output one line later, so no release ever shipped a signed file.

**None of that changes what you experience**, which is the reason it went unnoticed. `spctl -a
-t exec` exits **3** on both — on the signed staging file and on the unsigned extracted one.
Ad-hoc signing was never going to make macOS trust this, so the step has been removed rather
than repaired: keeping it would have meant preserving a signature that buys nothing and only
survives if you happen to extract with `ditto` instead of double-clicking.

Since macOS Sequoia, Apple removed the old Control-click → Open shortcut that used to bypass
this. The System Settings path above is the current route, and there is no engineering that
removes it.

**An Apple Developer account (~$99/year) would remove this friction entirely.** That is a
decision for the project owner, and it is recorded here so the decision stays informed rather
than forgotten.

---

## Windows

1. Download the `.zip` beside its `.sha256` file.
2. **Verify it** before opening anything:
   ```
   certutil -hashfile fcf-platform-<version>-windows.zip SHA256
   ```
   Compare the printed hash to the contents of the `.sha256` file. If they differ, stop.
3. Right-click the `.zip` → **Properties**. If there is an **Unblock** checkbox at the bottom,
   tick it and click OK. This clears the mark-of-the-web on the whole archive and saves
   unblocking each file inside it.
4. Extract it. Double-click **`run-platform.cmd`**.
5. **SmartScreen may warn** with *"Windows protected your PC — unrecognised publisher."* Click
   **More info**, then **Run anyway**.

### Why it does that

SmartScreen warns about executables from publishers it does not recognise. Recognition comes
from a code-signing certificate and, in practice, from reputation accumulated across many
downloads. **This project has no code-signing certificate**, so there is nothing for SmartScreen
to recognise. The warning is accurate.

---

## Uninstalling

There is nothing to uninstall in the usual sense — no installer ran, nothing was written
outside the folder you extracted.

**macOS and Windows:**

1. Delete the extracted folder.
2. If you ran the platform, it created a Python virtual environment inside that folder; deleting
   the folder removes it.
3. macOS only: to also forget the security exception you granted, there is nothing to do — the
   exception is tied to the file, which you have deleted.

The platform binds to **loopback only** and stores nothing outside its own directory. It opens
no ports to your network and writes nothing to your system folders.

---

## If it does not start

The run script reports what is missing rather than failing silently. The two common cases:

**"Python 3.11+ is required and was not found"** — install Python from python.org, then run the
script again.

**A build step fails on first run** — the first start builds the model surfaces from the
synthetic inputs, which takes about a minute. If a step fails, the script prints the real
output of the failing command rather than swallowing it. That output is what to report.

---

## What this installation cannot do

Stated because a capability that is quietly absent looks like a capability that is broken.

- **No MATLAB or Simulink results.** Not because they describe real sites — they do not; every
  MATLAB run used a synthetic fixture. They are excluded because they are **received CI
  artifacts from a separate harness repository**, not something this installer can produce or
  reproduce. The platform's engine surface says so explicitly rather than appearing empty.
- **No 3D explorer.** Its site geometry is generated from the real twelve facilities, so it is
  excluded. The surface is skipped rather than shown broken.
- **No real site data at all.** That is the point — see DEC-016.
