# 修复 Python comtypes 库权限问题
$comtypesGenDir = "C:\Users\青松\AppData\Local\Programs\Python\Python310\Lib\site-packages\comtypes\gen"

# 获取当前用户
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

# 设置权限
$acl = Get-Acl $comtypesGenDir
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule($currentUser, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.SetAccessRule($rule)
Set-Acl $comtypesGenDir $acl

# 递归设置子文件权限
Get-ChildItem $comtypesGenDir -Recurse | ForEach-Object {
    $acl = Get-Acl $_.FullName
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($currentUser, "FullControl", "Allow")
    $acl.SetAccessRule($rule)
    Set-Acl $_.FullName $acl
}

Write-Host "权限修复完成！"
