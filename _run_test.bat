@echo off
cd /d c:\Users\hari1\CRICKBUSS
py _test_bugs.py > test_run_stdout.txt 2> test_run_stderr.txt
echo EXITCODE:%ERRORLEVEL%
