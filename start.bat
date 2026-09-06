@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Goa Face Search

set "BLOCKCHAIN_DIR=%~dp0blockchain"
set "RPC_PORT=8545"

echo Checking local blockchain...
powershell -NoProfile -Command "if (Test-NetConnection -ComputerName 127.0.0.1 -Port %RPC_PORT% -InformationLevel Quiet -WarningAction SilentlyContinue) { exit 0 } else { exit 1 }"
if errorlevel 1 (
    echo Starting Hardhat node in a minimized window...
    start "Goa Hardhat Node" /min cmd /k "cd /d ""%BLOCKCHAIN_DIR%"" && npm.cmd run node"
    echo Waiting for Hardhat RPC...
    powershell -NoProfile -Command "$deadline=(Get-Date).AddSeconds(30); do { if (Test-NetConnection -ComputerName 127.0.0.1 -Port %RPC_PORT% -InformationLevel Quiet -WarningAction SilentlyContinue) { exit 0 }; Start-Sleep -Milliseconds 500 } while ((Get-Date) -lt $deadline); exit 1"
    if errorlevel 1 (
        echo ERROR: Hardhat RPC did not start on port %RPC_PORT%.
        pause
        exit /b 1
    )
)

echo Checking configured contract...
python -c "from dotenv import load_dotenv; import os; load_dotenv(r'%~dp0.env'); from web3 import Web3; w=Web3(Web3.HTTPProvider(os.getenv('RPC_URL','http://127.0.0.1:8545'))); a=os.getenv('CONTRACT_ADDRESS'); raise SystemExit(0 if w.is_connected() and a and w.eth.get_code(Web3.to_checksum_address(a)) not in (b'',b'0x') else 1)" >nul 2>&1
if errorlevel 1 (
    echo Deploying PostVerification contract...
    pushd "%BLOCKCHAIN_DIR%"
    set "DEPLOYED_ADDRESS="
    for /f "tokens=4" %%A in ('npx.cmd hardhat run scripts/deploy.js --network localhost ^| findstr /C:"PostVerification deployed to:"') do set "DEPLOYED_ADDRESS=%%A"
    popd
    if not defined DEPLOYED_ADDRESS (
        echo ERROR: Contract deployment failed.
        pause
        exit /b 1
    )
    echo Updating .env with the deployed contract address...
    powershell -NoProfile -Command "$p=Join-Path '%~dp0' '.env'; $lines=Get-Content -LiteralPath $p; $lines=$lines -replace '^CONTRACT_ADDRESS=.*$', 'CONTRACT_ADDRESS=!DEPLOYED_ADDRESS!'; Set-Content -LiteralPath $p -Value $lines"
) else (
    echo Using the configured deployed contract.
)

echo Starting face search...
python main.py --interactive
pause
endlocal
