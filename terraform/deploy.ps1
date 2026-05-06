# Deploy GeekBrain Bedrock KB with Terraform
# Usage: .\deploy.ps1

param(
    [string]$action = "apply",  # init, plan, apply, destroy
    [switch]$autoApprove = $false
)

$TerraformDir = Get-Location

Write-Host "================================" -ForegroundColor Green
Write-Host "GeekBrain Bedrock KB Terraform" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Check AWS CLI
Write-Host "`nChecking AWS CLI..." -ForegroundColor Yellow
$awsCheck = aws sts get-caller-identity 2>&1
if ($awsCheck -match "An error") {
    Write-Host "❌ AWS CLI not configured" -ForegroundColor Red
    exit 1
}
Write-Host "✓ AWS credentials OK" -ForegroundColor Green

# Check Terraform
Write-Host "`nChecking Terraform..." -ForegroundColor Yellow
$tfVersion = terraform version 2>&1 | Select-Object -First 1
Write-Host $tfVersion -ForegroundColor Green

# Initialize (always safe to run)
Write-Host "`nInitializing Terraform..." -ForegroundColor Yellow
terraform init

# Validate
Write-Host "`nValidating Terraform configuration..." -ForegroundColor Yellow
terraform validate
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Validation failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Validation passed" -ForegroundColor Green

# Plan
Write-Host "`nPlanning infrastructure..." -ForegroundColor Yellow
$planFile = "terraform.tfplan"
terraform plan -out=$planFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Planning failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Plan created" -ForegroundColor Green

# Apply
if ($action -eq "apply" -or $action -eq "apply-auto") {
    Write-Host "`nApplying Terraform plan..." -ForegroundColor Yellow
    
    if ($autoApprove) {
        terraform apply -auto-approve $planFile
    } else {
        Write-Host "`n⚠️  Review the plan above. Type 'yes' to apply, 'no' to cancel." -ForegroundColor Yellow
        $response = Read-Host "Proceed with apply?"
        
        if ($response -eq "yes") {
            terraform apply $planFile
        } else {
            Write-Host "❌ Apply cancelled" -ForegroundColor Red
            exit 1
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Infrastructure deployed successfully!" -ForegroundColor Green
        
        Write-Host "`nOutputs:" -ForegroundColor Yellow
        terraform output
        
        # Extract KB ID
        $kbId = terraform output -raw knowledge_base_id 2>$null
        Write-Host "`n✅ Knowledge Base ID: $kbId" -ForegroundColor Green
        Write-Host "   Saved to: src/kb_id.txt" -ForegroundColor Green
    } else {
        Write-Host "❌ Apply failed" -ForegroundColor Red
        exit 1
    }
} elseif ($action -eq "destroy") {
    Write-Host "`n⚠️  WARNING: This will DELETE all infrastructure!" -ForegroundColor Red
    $response = Read-Host "Type 'destroy' to confirm"
    
    if ($response -eq "destroy") {
        terraform destroy -auto-approve
        Write-Host "✅ Infrastructure destroyed" -ForegroundColor Green
    } else {
        Write-Host "❌ Destroy cancelled" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Unknown action: $action" -ForegroundColor Red
    Write-Host "   Valid actions: init, plan, apply, destroy" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n================================" -ForegroundColor Green
Write-Host "Done!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
