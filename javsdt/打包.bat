@echo off
ECHO. ===============================================================================
echo. =                                                                             =
echo. =         [1]打包 素人Jav321  [2]打包 创建ini    [3] 打包 javdbFc2            =
echo. =                                                                             =
echo. =         [4]打包 Javbus无码  [5]打包 Javbus有码 [6] 打包 Javlib有码          = 
echo. =                                                                             =
ECHO. ===============================================================================
echo.
:choice
set choice=
set /p choice= 请输入选项:
if /i "%choice%"=="1" goto jav321
if /i "%choice%"=="2" goto Fc2
if /i "%choice%"=="3" goto Createini
if /i "%choice%"=="4" goto BusW
if /i "%choice%"=="5" goto BusY
if /i "%choice%"=="6" goto lib
echo. 输入无效
echo.
goto choice



:jav321
echo. 开始打包
pyinstller -F Jav321.py 
cd %~dp0\dist
move /y Jav321.exe 【素人】jav321须翻墙.exe
goto end

:Fc2
echo. 开始打包
pyinstaller -F JavdbFc2.py
cd dist
move /y JavdbFc2.exe 【FC2】javdb.exe
goto end

:Createini
echo. 开始打包
pyinstaller -F CrateIni.py
cd dist
move /y CrateIni.exe 重新创建ini.exe
goto end

:BusW
echo. 开始打包
pyinstaller -F -i favicon.ico JavBusWuma.py
cd dist
move /y JavBusWuma.exe 【无码】Javbus.exe
goto end

:BusY
echo. 开始打包
pyinstaller -F -i favicon.ico JavBusYouma.py
cd dist
move /y JavBusYouma.exe 【有码】Javbus.exe
goto end

:lib
echo. 开始打包
pyinstaller -F javlibrary.py
cd dist
move /y javlibrary.exe 【有码】javlibrary.exe
goto end

:end
echo. 结束
pause 1>nul 2>nul