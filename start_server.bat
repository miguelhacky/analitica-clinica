@echo off
cd /d "C:\Users\Aprendiz.21-10100886633.000\Desktop\Proyec"
set PATH=C:\Users\Aprendiz.21-10100886633.000\AppData\Local\Programs\Python\Python312\Scripts;C:\Users\Aprendiz.21-10100886633.000\AppData\Local\Programs\Python\Python312;%PATH%
start /B python manage.py runserver 0.0.0.0:8000
