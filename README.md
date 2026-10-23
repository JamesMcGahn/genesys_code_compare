# Genesys Code Compare

An interactive command-line tool for comparing Genesys Cloud Workforce Management activity codes across business units. Select the business units to inspect, then export an Excel workbook showing shared codes, configuration differences, and codes missing from some units.

The application reads business units and activity codes from Genesys Cloud; it does not modify their configuration.

## Requirements

- Python **3.14 or later**.
- `uv` for the setup commands below.
- A Genesys Cloud OAuth client configured for the **client credentials** grant, with access to read the relevant Workforce Management business units and activity codes.
- The client ID, client secret, and region for your organization.
- Network access to that region's login and API endpoints.

Runtime dependencies are `requests`, `questionary`, and `openpyxl`. They are installed during setup.

## Quick start

From the repository root:

```sh
uv sync
uv run start
```

The `start` command is the console entry point declared in `pyproject.toml`.

1. Enter your client ID and client secret. The secret prompt masks your input.
2. Select your Genesys Cloud region.
3. Choose **COMPARE ACTIVITY CODES**.
4. Select business units using **Space**, then press **Enter** to confirm. Select two or more for a useful comparison.
5. Open the generated workbook at the path printed in the terminal.
6. Run another comparison from the menu, choose **QUIT**, or press **Ctrl+C** to exit.

Credentials are entered interactively and held in memory for the session; the application does not save them to the configuration file. It obtains an access token at sign-in and checks its expiry before starting each comparison.

## Excel report

For a source run, reports are saved relative to the current working directory:

```text
reports/report_YYYYMMDD-HHMMSS.xlsx
```

When running as a frozen executable, the `reports` folder is created beside the executable instead.

Each workbook contains five sheets:

| Sheet                 | Contents                                                                                                  |
| --------------------- | --------------------------------------------------------------------------------------------------------- |
| **Summary**           | One row per code name and one column per selected business unit. `X` means present; `O` means missing.    |
| **Exact Matches**     | Codes present in every selected business unit with matching name, category, and default-code flag.        |
| **Field Differences** | Codes with the same name in every selected business unit, but different categories or default-code flags. |
| **Partial Matches**   | Codes present in more than one, but fewer than all, selected business units.                              |
| **Unique Codes**      | Codes present in only one selected business unit when multiple units are selected.                        |

Detail sheets include **Code**, **Business Unit**, **Category**, **Default Code**, **Default Name Changed**, and **ID**. All sheets have bold headers, a frozen header row, and autofilters.

### Matching rules

- Only active activity codes with an ID are included.
- Matching uses exact, case-sensitive names; names are not trimmed or normalized.
- When an activity code has no name, its category is used as its display and comparison name.
- Only name, category, and the default-code flag determine an exact field match. IDs and the `Default Name Changed` field are exported but do not affect matching.
- `Default Name Changed` is set to `True` when a default code arrives without a name. It is not a history of user renames.
- Codes that occur in only a subset of selected units remain partial or unique matches, even if their fields differ.
- With one business unit selected, every included code is an exact match.

The analyzer keys business units and codes by name. Duplicate business-unit names, or duplicate code names within a unit, can overwrite one another during analysis. The API client also reads the returned `entities` array without following pagination links.

## Region configuration

The repository's `config.toml` and bundled defaults define all 18 core deployment regions listed in the [Genesys Cloud AWS regions documentation](https://help.genesys.cloud/articles/aws-regions-for-genesys-cloud-deployment/), verified on October 23, 2026. Satellite media regions are excluded. Ohio (`us-east-2`) is dedicated to FedRAMP / U.S. Public Sector use, and Brandenburg (`eusc-de-east-1`) has limited availability.

Each region requires a token endpoint and an API base URL:

```toml
[regions.us-east-1]
login_url = "https://login.mypurecloud.com/oauth/token"
api_url = "https://api.mypurecloud.com"
```

To add a region, add another `[regions.<name>]` table with its corresponding URLs.

Configuration lookup depends on how the application runs:

- **Source checkout:** use `config.toml` at the repository root.
- **Frozen executable:** use `config.toml` beside the executable.
- **Fallback:** if the external file does not exist, load `src/genesys_code_compare/default_config.toml` from the package.

An external configuration replaces the bundled configuration; the two are not merged. Region entries missing either URL are skipped, and loading fails if no valid regions remain.

## Troubleshooting

| Problem                                    | What to check                                                                                       |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| Authentication fails                       | Verify the client ID, secret, and selected region. The sign-in flow prompts you to try again.       |
| Access denied                              | Check the OAuth client's permissions and access to the selected business units.                     |
| Genesys cannot be reached                  | Check your connection and configured endpoint URLs.                                                 |
| Rate limiting or temporary service failure | Wait, then start the comparison again from the menu. Failed requests are not automatically retried. |
| Report cannot be written                   | Close the workbook in Excel and check permissions on the output folder.                             |
| A code is absent from the report           | Check whether it is active, has an ID, and belongs to a selected business unit.                     |

## Development

Install dependencies, including the development group, and run the tests:

```sh
uv sync --group dev
uv run pytest
```

The test suite covers configuration, prompts, authentication, API parsing, network handling, comparison logic, workbook generation, and application workflows.

```text
src/genesys_code_compare/
├── __init__.py          # Console entry point and session cleanup
├── app.py               # Application setup and interactive menu
├── app_config.py        # TOML configuration loading
├── analyze.py           # Activity-code classification
├── cli.py               # Terminal input and output
├── prompts.py           # Credential, region, and business-unit prompts
├── default_config.toml  # Bundled region definitions
├── workflows/           # Authentication and comparison orchestration
├── genesys/             # Genesys API calls and token lifecycle
├── network/             # HTTP client, response handling, and throttling
├── file/                # Excel report generation and output paths
├── models/              # Data models
├── enums/               # HTTP methods and menu choices
└── errors/              # Configuration and network exceptions
tests/                   # pytest suite
```

## Build commands

Run these commands from the repository root on the target operating system.
Python and dependencies are included in the output; recipients do not need Python
or uv. Keep `launcher.py` as the PyInstaller entry point. Builds target the
architecture of the Python interpreter used to build them.

Both builds include the packaged default config. The macOS build also copies the
root `config.toml` beside its executable inside the app. Rebuilding replaces release files; save any
custom configuration and reports elsewhere first. These commands produce
unsigned releases and do not perform macOS notarization.

### Windows (PowerShell)

```powershell
uv run --group dev pyinstaller --noconfirm --clean --onefile --console `
  --name GenesysCodeCompare `
  --icon "assets/app.ico" `
  --paths src `
  --add-data "src/genesys_code_compare/default_config.toml:genesys_code_compare" `
  --add-data "LICENSE:." `
  --distpath dist/windows `
  --workpath build/windows `
  launcher.py

if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }
```

Send only `dist/windows/GenesysCodeCompare.exe`. Python, DLLs, dependencies,
the default configuration, and the license are embedded in this single file.
Users can double-click it or run it from PowerShell:

```powershell
.\GenesysCodeCompare.exe
```

The executable uses `assets/app.ico` and the bundled `default_config.toml`;
no separate configuration file is required. To change the embedded configuration,
edit `src/genesys_code_compare/default_config.toml` before building. An optional
`config.toml` beside the executable overrides the embedded defaults.

PyInstaller extracts its bundled runtime to a temporary directory when launched;
users do not need to manage those files. Generated Excel reports are saved in
`reports/` beside the executable, so run it from a writable folder.

### macOS (Terminal)

This builds a single `.app` containing the executable, Python, dependencies,
configuration, icon, and Terminal launcher. The Terminal launcher is necessary
for the interactive menus; it lives inside the `.app` and requires no separate
files from the recipient.

Paste the whole block into Terminal. It stops on failure and replaces only the
previous macOS `.app` at the specified output path.

```bash

set -e

uv run --group dev pyinstaller --noconfirm --clean --onedir --console \
  --name GenesysCodeCompare \
  --paths src \
  --add-data "src/genesys_code_compare/default_config.toml:genesys_code_compare" \
  --distpath dist/macos \
  --workpath build/macos \
  launcher.py

app="dist/macos/GenesysCodeCompare.app"
rm -rf "$app"
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
mv dist/macos/GenesysCodeCompare "$app/Contents/Resources/runtime"
cp config.toml "$app/Contents/Resources/runtime/config.toml"
cp LICENSE "$app/Contents/Resources/LICENSE"
cp assets/app.icns "$app/Contents/Resources/app.icns"

cat > "$app/Contents/MacOS/launch" <<'SH'
#!/bin/sh
contents=$(cd "$(dirname "$0")/.." && pwd) || exit 1
exec /usr/bin/open -a Terminal "$contents/Resources/runtime/Launch.command"
SH

cat > "$app/Contents/Resources/runtime/Launch.command" <<'SH'
#!/bin/sh
cd "$(dirname "$0")" || exit 1
exec ./GenesysCodeCompare
SH

chmod +x "$app/Contents/MacOS/launch" \
  "$app/Contents/Resources/runtime/Launch.command"

cat > "$app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>GenesysCodeCompare</string>
  <key>CFBundleDisplayName</key><string>Genesys Code Compare</string>
  <key>CFBundleIdentifier</key><string>com.genesyscodecompare.launcher</string>
  <key>CFBundleExecutable</key><string>launch</string>
  <key>CFBundleIconFile</key><string>app.icns</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict>
</plist>
PLIST

/usr/bin/ditto -c -k --sequesterRsrc --keepParent \
  "$app" dist/GenesysCodeCompare-macos.zip

```

Send `dist/GenesysCodeCompare-macos.zip`. Users extract it and double-click
`GenesysCodeCompare.app`; it opens the app in Terminal with your `.icns` Finder
icon. Keep the app in a writable folder, since the current application saves
reports beside its executable inside the bundle.

To edit configuration or retrieve reports, right-click the `.app`, choose
**Show Package Contents**, and open `Contents/Resources/runtime`. That directory
contains `config.toml` and, after a comparison, `reports/`.

## License

[MIT](LICENSE) — Copyright © 2026 James McGahn.
