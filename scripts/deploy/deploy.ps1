param(
  [string]$ContractPath = "contracts/ClaimGuardAI.py",
  [string]$Name = "ClaimGuardAI"
)

$ErrorActionPreference = "Stop"

python -c "import ast; ast.parse(open('$ContractPath', encoding='utf-8').read())"
genlayer lint $ContractPath
genlayer deploy $ContractPath --name $Name
