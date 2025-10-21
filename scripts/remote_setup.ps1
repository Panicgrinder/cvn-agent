param(
    [Parameter(Mandatory = $true)]
    [string]$Remote,

    [Parameter(Mandatory = $false)]
    [int]$Port = 22,

    [Parameter(Mandatory = $false)]
    [string]$IdentityFile
)

Write-Host "[Remote Setup] Ziel: $Remote, Port: $Port" -ForegroundColor Cyan

# 0) Voraussetzungen prüfen
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Error "OpenSSH Client ist nicht installiert oder nicht im PATH. Installiere das Windows-Feature 'OpenSSH Client'."
    exit 1
}

# 1) Bash-Skript (wird auf dem Server ausgeführt)
$script = @'
set -euo pipefail

REPO_URL="https://github.com/Panicgrinder/cvn-agent.git"
REPO_DIR="$HOME/cvn-agent"
APP_PORT="8000"
MODEL_TAG="llama3.1:8b"

echo "[1/6] Docker Engine + Compose installieren (Ubuntu/Debian)"
if ! command -v docker >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y docker.io docker-compose-plugin
    sudo systemctl enable --now docker
  else
    echo "apt-get nicht gefunden. Bitte Docker Engine + Compose Plugin manuell installieren."
    exit 1
  fi
else
  echo "Docker bereits installiert."
fi

echo "[2/6] Repo klonen oder aktualisieren"
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$REPO_DIR"
fi
cd "$REPO_DIR"

echo "[3/6] Optionales Override: Ollama-Port nicht öffentlich exposen"
cat > docker-compose.override.yml <<'YAML'
version: "3.9"
services:
  ollama:
    ports: []  # kein externes Port-Mapping für 11434
YAML

echo "[4/6] Stack bauen & starten"
sudo docker compose up -d --build

echo "[5/6] Modell einmalig in Ollama ziehen: $MODEL_TAG"
# Warten, bis ollama API lauscht
TRIES=30
until curl -fsS http://localhost:11434/api/version >/dev/null 2>&1 || [ $TRIES -eq 0 ]; do
  sleep 2
  TRIES=$((TRIES-1))
done
sudo docker exec cvn-ollama ollama pull "$MODEL_TAG"

echo "[6/6] Healthcheck der App"
sleep 2
if curl -fsS "http://localhost:${APP_PORT}/health"; then
  echo
  echo "Swagger:  http://$(hostname -I | awk '{print $1}'):${APP_PORT}/docs"
  echo "Health:   http://$(hostname -I | awk '{print $1}'):${APP_PORT}/health"
else
  echo "Healthcheck fehlgeschlagen. App-Logs (letzte 10 Min):"
  sudo docker compose logs --no-color --since=10m app || true
  exit 2
fi
'@

# 2) SSH-Argumente bauen
$sshArgs = @()
if ($Port -ne 22) {
    $sshArgs += @('-p', "$Port")
}
if ($IdentityFile) {
    $sshArgs += @('-i', $IdentityFile)
}
$sshArgs += $Remote
$sshArgs += 'bash'
$sshArgs += '-s'

Write-Host "[Remote Setup] Führe Setup auf Server aus..." -ForegroundColor Cyan

# 3) Skript an SSH pipen und ausführen
try {
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = 'ssh'
    $processInfo.Arguments = ($sshArgs -join ' ')
    $processInfo.RedirectStandardInput = $true
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $processInfo.UseShellExecute = $false
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo

    [void]$process.Start()
    $process.StandardInput.Write($script)
    $process.StandardInput.Close()

    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    if ($stdout) { Write-Host $stdout }
    if ($stderr) { Write-Host $stderr -ForegroundColor Yellow }

    exit $process.ExitCode
}
catch {
    Write-Error $_
    exit 1
}
