copy /Y "C:\Users\kos\Adobe Flash Builder 4.6\Test\src\Test.as" flex_sdk_3.6a
del /F flex_sdk_3.6a\test.swf
cd flex_sdk_3.6a
start /WAIT start.bat
copy /Y test.swf C:\nginx-1.2.0\html
