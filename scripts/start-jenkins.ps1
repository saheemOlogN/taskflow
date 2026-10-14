param([string]$JavaHome = 'C:\Program Files\Java\jdk-21')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$toolDir = Join-Path $projectRoot '.tools'
$stateDir = Join-Path $projectRoot '.runtime'
$war = Join-Path $toolDir 'jenkins.war'
New-Item -ItemType Directory -Force $toolDir, $stateDir | Out-Null
if (-not (Test-Path $war)) {
    $release = '2.580.1'
    $url = "https://get.jenkins.io/war-stable/$release/jenkins.war"
    Write-Host "Downloading Jenkins $release..."
    Invoke-WebRequest $url -OutFile "$war.download"
    $expected = '393bf2476352dd726519fd1f92ce66eac7d23c0936e6967420b717060c4c40d0'
    if ((Get-FileHash "$war.download" -Algorithm SHA256).Hash.ToLower() -ne $expected) {
        throw 'Jenkins checksum mismatch. Download was not executed.'
    }
    Move-Item -LiteralPath "$war.download" -Destination $war
}
$env:JAVA_HOME = $JavaHome
$env:JENKINS_HOME = Join-Path $stateDir 'jenkins-home'
$env:PATH = "$JavaHome\bin;$env:PATH"
$java = Join-Path $JavaHome 'bin\java.exe'
if (-not (Test-Path $java)) { throw "Java not found: $java" }
if (Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue) {
    throw 'Port 8080 is already in use. Check http://localhost:8080 before starting another instance.'
}
$process = Start-Process -FilePath $java -ArgumentList @('-jar', ('"' + $war + '"'), '--httpListenAddress=127.0.0.1', '--httpPort=8080') -PassThru -WindowStyle Hidden -WorkingDirectory $projectRoot -RedirectStandardOutput (Join-Path $stateDir 'jenkins.out.log') -RedirectStandardError (Join-Path $stateDir 'jenkins.err.log')
Write-Host "Jenkins started (PID $($process.Id)). Allow a minute, then open http://localhost:8080"
Write-Host "Unlock password is in $env:JENKINS_HOME\secrets\initialAdminPassword (keep it private)."
