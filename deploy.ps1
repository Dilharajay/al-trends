# ==============================================================================
# AL Trends Docker Hub & Cloud Deployment Automation Script
# ==============================================================================
param (
    [Parameter(Position=0)]
    [ValidateSet("test", "build-frontend", "run-local", "docker-build", "docker-run", "docker-push", "git-push", "help")]
    [string]$Action = "help"
)

# Set execution policy and activate virtual environment
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& "d:\DS-Projects\al-trends\.venv\Scripts\Activate.ps1"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AL Trends Deployment Manager (Virtual Environment Active)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$IMAGE_NAME = "dilhara0592/image-test:latest"

switch ($Action) {
    "test" {
        Write-Host "`n[1/1] Running automated test suite..." -ForegroundColor Yellow
        pytest tests/ -v
    }
    
    "build-frontend" {
        Write-Host "`n[1/1] Building React frontend with Vite..." -ForegroundColor Yellow
        Push-Location "frontend"
        npm run build
        Pop-Location
        Write-Host "Frontend compiled into src/web successfully!" -ForegroundColor Green
    }

    "run-local" {
        Write-Host "`nStarting local FastAPI server with React static mount..." -ForegroundColor Yellow
        uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
    }

    "docker-build" {
        Write-Host "`nBuilding Docker container image for Docker Hub: $IMAGE_NAME..." -ForegroundColor Yellow
        docker build -t $IMAGE_NAME .
    }

    "docker-run" {
        Write-Host "`nRunning container locally on http://localhost:8000..." -ForegroundColor Yellow
        docker run --rm -p 8000:8000 --name al-trends-app $IMAGE_NAME
    }

    "docker-push" {
        Write-Host "`nPushing image to Docker Hub repository: $IMAGE_NAME..." -ForegroundColor Yellow
        docker push $IMAGE_NAME
    }

    "git-push" {
        Write-Host "`nRunning test suite before push..." -ForegroundColor Yellow
        pytest tests/ -q
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Tests passed! Pushing changes to GitHub..." -ForegroundColor Green
            git push origin main
            Write-Host "Pushed to GitHub! Check Actions tab: https://github.com/Dilharajay/al-trends/actions" -ForegroundColor Cyan
        } else {
            Write-Host "Tests failed! Aborting push." -ForegroundColor Red
        }
    }

    Default {
        Write-Host "`nAvailable Actions:" -ForegroundColor Yellow
        Write-Host "  .\deploy.ps1 test            - Run all pytest test cases"
        Write-Host "  .\deploy.ps1 build-frontend   - Build production React frontend into src/web"
        Write-Host "  .\deploy.ps1 run-local        - Start local development server on port 8000"
        Write-Host "  .\deploy.ps1 docker-build     - Build multi-stage Docker image locally ($IMAGE_NAME)"
        Write-Host "  .\deploy.ps1 docker-run       - Run Docker container on http://localhost:8000"
        Write-Host "  .\deploy.ps1 docker-push      - Push image to Docker Hub ($IMAGE_NAME)"
        Write-Host "  .\deploy.ps1 git-push         - Run tests and push to GitHub (triggers Docker Hub Action)"
        Write-Host "`nExample:" -ForegroundColor Gray
        Write-Host "  .\deploy.ps1 test"
    }
}
