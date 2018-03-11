rd /S /Q dist
%python_dir%python setup.py py2exe
xcopy locale dist\locale /i /e /y
ren dist\Shell.exe FunduckESS.exe