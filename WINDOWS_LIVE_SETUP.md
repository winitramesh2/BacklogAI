# Windows Live Setup Guide (Local BacklogAI + Local Jira)

This guide helps you run and validate the Windows client using your current local backend and Jira setup.

## Current Assumptions
- BacklogAI backend runs on `http://localhost:8001`
- Jira runs on `http://localhost:8081`
- Windows app uses the shared desktop runtime path (`desktopMain`)
- Current recommended packaging output is: **MSI installer + portable ZIP**

> Tip: Open PowerShell in the repo root before running commands.

---

## 1) Prepare prerequisites

### What
Install tools needed for Windows build and runtime.

### Why
Compose Desktop packaging and app runtime depend on JDK + Gradle tooling.

### How
1. Install JDK 17
2. Confirm Java is available:

```powershell
java -version
```

3. Confirm Gradle wrapper is executable from repo root:

```powershell
.\gradlew.bat -version
```

---

## 2) Start backend services

### What
Run BacklogAI backend and Jira locally.

### Why
Windows client calls the same APIs as Android/iOS/macOS and requires backend + Jira availability.

### How
1. Start backend on port `8001`
2. Start Jira on port `8081`
3. Validate endpoints:

```powershell
curl http://localhost:8001/health
curl http://localhost:8081
```

Both commands should return successful responses.

---

## 3) Run Windows app from source

### What
Launch desktop app from Gradle.

### Why
Fastest path for local development and UI validation.

### How

```powershell
.\gradlew.bat :composeApp:run
```

Expected result: BacklogAI desktop window opens and server status can be refreshed.

---

## 4) Build Windows distributables

### What
Create installer and portable package assets.

### Why
Supports both install-based and no-install rollout flows.

### How
Build MSI and app distribution:

```powershell
.\gradlew.bat :composeApp:packageMsi :composeApp:createDistributable
```

Create portable ZIP:

```powershell
New-Item -ItemType Directory -Force -Path .\demo\binaries-v3\windows | Out-Null
Compress-Archive -Path .\composeApp\build\compose\binaries\main\app\BackLogAI\* -DestinationPath .\demo\binaries-v3\windows\BackLogAI-windows-portable.zip -Force
```

Expected outputs:
- `composeApp/build/compose/binaries/main/msi/*.msi`
- `demo/binaries-v3/windows/BackLogAI-windows-portable.zip`

---

## 5) Run end-to-end validation

### What
Validate full product flow from Windows app.

### Why
Confirms Windows behaves the same as other clients.

### How
1. Open Windows app
2. Confirm backend health indicator is connected
3. Enter context + objective and generate preview
4. Review story output
5. Click **Sync to JIRA**
6. Confirm Jira key appears and issue is created in Jira

---

## Troubleshooting

- **App opens but cannot connect**
  - Verify backend is reachable at `http://localhost:8001/health`
  - Check local firewall rules for loopback traffic

- **Generate works, sync fails**
  - Verify Jira is reachable at `http://localhost:8081`
  - Check Jira credentials in backend `.env`

- **MSI task fails**
  - Re-run with `--stacktrace`
  - Confirm JDK 17 is active in current shell

- **Portable ZIP missing**
  - Ensure `:composeApp:createDistributable` completed successfully before running `Compress-Archive`
