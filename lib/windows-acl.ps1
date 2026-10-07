# Native ownership-state privacy and settings ACL preservation. Called only on Windows.
param(
    [ValidateSet('create', 'validate', 'copy')][string]$Action,
    [string]$Path,
    [string]$Destination
)
$ErrorActionPreference = 'Stop'
$sidType = [System.Security.Principal.SecurityIdentifier]
$userSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$trusted = @($userSid.Value, 'S-1-5-18', 'S-1-5-32-544')

function Assert-Private([string]$ItemPath) {
    $item = Get-Item -LiteralPath $ItemPath -Force
    if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        throw 'Ownership state contains a reparse point'
    }
    $acl = Get-Acl -LiteralPath $ItemPath
    if ($acl.GetOwner($sidType).Value -notin $trusted) {
        throw 'Ownership state has an untrusted owner'
    }
    # OWNER RIGHTS is safe only after checking the actual owner above (Python 3.13's 0700 ACL).
    $allowed = $trusted + 'S-1-3-4'
    # A null DACL grants everyone access. Use the descriptor to distinguish it from an empty ACL.
    $descriptor = [System.Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorSddlForm('All'))
    if ($null -eq $descriptor.DiscretionaryAcl) { throw 'Ownership state has no DACL' }
    foreach ($rule in $acl.GetAccessRules($true, $true, $sidType)) {
        if ($rule.AccessControlType -eq 'Allow' -and
            -not ($rule.PropagationFlags -band [System.Security.AccessControl.PropagationFlags]::InheritOnly) -and
            $rule.IdentityReference.Value -notin $allowed -and [int]$rule.FileSystemRights -ne 0) {
            throw 'Ownership state allows another principal access'
        }
    }
}

switch ($Action) {
    'create' {
        if (Test-Path -LiteralPath $Path) { throw 'Ownership state already exists' }
        $acl = [System.Security.AccessControl.DirectorySecurity]::new()
        $acl.SetOwner($userSid)
        $acl.SetAccessRuleProtection($true, $false)
        foreach ($sid in $trusted) {
            $identity = [System.Security.Principal.SecurityIdentifier]::new($sid)
            $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
                $identity, 'FullControl', 'ContainerInherit, ObjectInherit', 'None', 'Allow')
            $acl.AddAccessRule($rule)
        }
        # Apply the protected, inheritable DACL during creation, before snapshots are written.
        [System.IO.Directory]::CreateDirectory($Path, $acl) | Out-Null
        Assert-Private $Path
    }
    'validate' {
        $pending = [System.Collections.Generic.Queue[string]]::new()
        $pending.Enqueue($Path)
        while ($pending.Count -gt 0) {
            $current = $pending.Dequeue()
            Assert-Private $current
            if ((Get-Item -LiteralPath $current -Force).PSIsContainer) {
                Get-ChildItem -LiteralPath $current -Force | ForEach-Object { $pending.Enqueue($_.FullName) }
            }
        }
    }
    'copy' {
        $acl = Get-Acl -LiteralPath $Path
        Set-Acl -LiteralPath $Destination -AclObject $acl
    }
}
