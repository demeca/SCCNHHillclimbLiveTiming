<#
BackupEvent.ps1

Takes the most recent event file and makes a copies of
the event db and it's metadata db into a destination folder of 
your choosing. In this case I am placing the backup into 
a folder that is synced to AWS S3 for livetiming.

Designed to run via scheduled task every 10 min, so
the file is checked if it has been modified in the last 10 min.

!!! Assumes the destination folder strucutre exists !!!
#>

$last10Min = (Get-Date).AddMinutes(-10)
$monitoredPath = "C:\CHANGEME!!!!!!!!!!!!!!!!!!!!!!!"
$lastModified = (Get-ChildItem $monitoredPath | Sort-Object LastWriteTime | Select-Object -last 1).BaseName
$outputFileName1 = ($lastModified + ".FILE1EXT- CHANGEME!!!!!!!!!!")
$outputFileName2 = ($lastModified + ".FILE2EXT- CHANGEME!!!!!!!!!!")
$monitoredFile1 = ($monitoredPath + $outputFileName1)
$monitoredFile2 = ($monitoredPath + $outputFileName2)
$outputFolder = "C:\CHANGEME!!!!!!!!!!!!!!!!!!!!!"
$fileDate = get-date -Format "yyyyMMdd-hhmmss"

Write-Host "Starting Backup"

if ((Get-ItemProperty -Path $monitoredFile1 -Name LastWriteTime).LastWriteTime -gt $last10Min -or (Get-ItemProperty -Path $monitoredFile2 -Name LastWriteTime).LastWriteTime -gt $last10Min) {
    Write-Host "Copy $monitoredFile1 to $outputFolder"
    Copy-Item -Path ($monitoredFile1) -Destination ($outputFolder + $fileDate + "_" + $outputFileName1 + ".bak")
    Write-Host "Copy $monitoredFile2 to $outputFolder"
    Copy-Item -Path ($monitoredFile2) -Destination ($outputFolder + $fileDate + "_" + $outputFileName2 + ".bak")
}
else {
    Write-Host "No backup needed"
}