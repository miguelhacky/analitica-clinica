$py = "C:\Users\Aprendiz.21-10100886633.000\AppData\Local\Programs\Python\Python312\python.exe"
$proj = "C:\Users\Aprendiz.21-10100886633.000\Desktop\Proyec"
Set-Location $proj
Write-Host "=== HealthAnalytics IPS Server ===" -ForegroundColor Cyan
Write-Host "URL: http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "Login: admin@gmail.com / admin1234" -ForegroundColor Yellow
Write-Host "Presiona Ctrl+C para detener" -ForegroundColor Gray
Write-Host ""
& $py manage.py runserver 0.0.0.0:8000
