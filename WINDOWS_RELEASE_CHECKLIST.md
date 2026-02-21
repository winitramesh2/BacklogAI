# Windows Release Checklist

Use this checklist before publishing Windows artifacts and docs.

## 1) Preflight
- [ ] Backend health check passes: `GET /health`
- [ ] Jira local server reachable
- [ ] Repository on clean commit state
- [ ] JDK 17 active in Windows shell

## 2) Build Artifacts
- [ ] Build MSI installer:

```powershell
.\gradlew.bat :composeApp:packageMsi
```

- [ ] Build desktop distributable:

```powershell
.\gradlew.bat :composeApp:createDistributable
```

- [ ] Generate portable ZIP:

```powershell
New-Item -ItemType Directory -Force -Path .\demo\binaries-v3\windows | Out-Null
Compress-Archive -Path .\composeApp\build\compose\binaries\main\app\BackLogAI\* -DestinationPath .\demo\binaries-v3\windows\BackLogAI-windows-portable.zip -Force
```

- [ ] Confirm outputs exist:
  - `composeApp/build/compose/binaries/main/msi/*.msi`
  - `demo/binaries-v3/windows/BackLogAI-windows-portable.zip`

## 3) Functional Smoke Test (Windows)
- [ ] Launch app from installer build
- [ ] Launch app from portable ZIP build
- [ ] Health check indicator shows connected
- [ ] Generate v2 flow succeeds
- [ ] Sync to Jira succeeds and Jira key is shown
- [ ] Retry behavior works on sync failure path

## 4) Regression Spot Check
- [ ] Android app generate + sync flow unaffected
- [ ] iOS app generate + sync flow unaffected
- [ ] macOS app generate + sync flow unaffected
- [ ] Slack `/backlogai` flow unaffected

## 5) Demo and Documentation
- [ ] Add Windows demo media under `demo/windows-e2e-v3/`
- [ ] Add published binaries under `demo/binaries-v3/windows/`
- [ ] Update README links for Windows demo and binaries
- [ ] Update implementation plan status (In Progress -> Completed when done)

## 6) Optional Signing Track
- [ ] Code-sign MSI when certificate is available
- [ ] Capture signing details in release notes
