@echo off
REM Build and push Docker image to Docker Hub.
cd /d "%~dp0"
cd ..

if "%IMAGE_NAME%"=="" set IMAGE_NAME=savant42/retrorecon
if "%IMAGE_TAG%"=="" set IMAGE_TAG=edge

if "%DOCKERHUB_USERNAME%"=="" goto MissingCreds
if "%DOCKERHUB_PAT%"=="" goto MissingCreds

echo Logging in to Docker Hub...
echo %DOCKERHUB_PAT% | docker login --username %DOCKERHUB_USERNAME% --password-stdin
if errorlevel 1 goto Error

echo Building %IMAGE_NAME%:%IMAGE_TAG%...
docker build -t %IMAGE_NAME%:%IMAGE_TAG% .
if errorlevel 1 goto Error

echo Pushing %IMAGE_NAME%:%IMAGE_TAG%...
docker push %IMAGE_NAME%:%IMAGE_TAG%
if errorlevel 1 goto Error

echo Deploy complete.
goto End

:MissingCreds
echo ERROR: DOCKERHUB_USERNAME and DOCKERHUB_PAT must be set.
exit /b 1

:Error
echo ERROR: Command failed.
exit /b 1

:End
exit /b 0
