$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$composePath = Join-Path $repoRoot 'docker-compose.yml'
$definitionsPath = Join-Path $PSScriptRoot 'content-dlq.json'

& docker compose --project-directory $repoRoot -f $composePath cp $definitionsPath rabbitmq:/tmp/briefly-content-dlq.json
if ($LASTEXITCODE -ne 0) { throw 'Could not copy RabbitMQ definitions.' }

& docker compose --project-directory $repoRoot -f $composePath exec -T rabbitmq rabbitmqctl import_definitions /tmp/briefly-content-dlq.json
if ($LASTEXITCODE -ne 0) { throw 'Could not import RabbitMQ definitions.' }

& docker compose --project-directory $repoRoot -f $composePath exec -T rabbitmq rabbitmqctl list_policies -p /
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect RabbitMQ policies.' }
