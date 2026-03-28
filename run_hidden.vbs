Set WshShell = CreateObject("WScript.Shell")
strDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run """" & strDir & "\.venv\Scripts\pythonw.exe"" """ & strDir & "\speed_test_agent.py""", 0, True
