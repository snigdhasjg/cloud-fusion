# Switch AWS region
cloud-fusion aws config-switch region
if ($LASTEXITCODE -ne 0) {
    return
}

# Read the selected region
$selectedRegion = Get-Content "$HOME\.aws\fusion\region"

# Check if the selected region is empty
if ([string]::IsNullOrWhiteSpace($selectedRegion)) {
    # Unset AWS_REGION as it matches the one in the current profile
    Remove-Item Env:AWS_REGION -ErrorAction SilentlyContinue
} else {
    # Set AWS_REGION
    $Env:AWS_REGION = $selectedRegion
}
