$ErrorActionPreference = "Stop"

$pluginRoot = if ($env:PLUGIN_ROOT) {
    $env:PLUGIN_ROOT
} else {
    Split-Path -Parent $PSScriptRoot
}
$scriptPath = Join-Path $pluginRoot "hooks\reasoning_effort_context.py"

function Test-Candidate {
    param(
        [string]$Command,
        [string[]]$PrefixArguments
    )

    & $Command @PrefixArguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" *> $null
    return $LASTEXITCODE -eq 0
}

$validInterpreter = $false
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python -and (Test-Candidate -Command $python.Source -PrefixArguments @())) {
    $validInterpreter = $true
    & $python.Source $scriptPath
    if ($LASTEXITCODE -eq 0) {
        exit 0
    }
}

if (-not $validInterpreter) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher -and (Test-Candidate -Command $launcher.Source -PrefixArguments @("-3"))) {
        $validInterpreter = $true
        & $launcher.Source -3 $scriptPath
        if ($LASTEXITCODE -eq 0) {
            exit 0
        }
    }
}

$fallback = @{
    continue = $true
    hookSpecificOutput = @{
        hookEventName = "UserPromptSubmit"
        additionalContext = @"
<codex-reasoning-assistant>
status=unavailable
source=python_unavailable
instruction=Runtime reasoning-effort detection is unavailable because a working Python 3.10+ interpreter was not found. Do not claim the active level is confirmed. Still assess the task and recommend a model and effort.
</codex-reasoning-assistant>
"@
    }
}

$fallback | ConvertTo-Json -Depth 4 -Compress
