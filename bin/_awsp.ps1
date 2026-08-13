# Switch AWS profile
cloud-fusion aws config-switch profile
if ($LASTEXITCODE -ne 0) {
    return
}

# Read the selected profile
$selectedProfile = Get-Content "$HOME\.aws\fusion\profile"

# Unset AWS_REGION
Remove-Item Env:AWS_REGION -ErrorAction SilentlyContinue

if ([string]::IsNullOrWhiteSpace($selectedProfile)) {
    # Unset AWS_PROFILE for default profile
    Remove-Item Env:AWS_PROFILE -ErrorAction SilentlyContinue
} else {
    # Set AWS_PROFILE
    $Env:AWS_PROFILE = $selectedProfile
}
