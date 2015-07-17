**This is all very rough-and-ready for the time being!**

# Downloading the code #

Currently the code is only available directly from Mercurial.

TODO

# Compiling the OWL Runtime Library #

In order to use OWL BASIC, you must first compile the OWL Runtime library against which all OWL BASIC programs must be dynamically linked. This only needs to be done once - or whenever the runtime library has been updated to a new version.

Open the OwlRuntime.sln solution in Visual Studio 2008 and 'Build Solution' (Ctrl-Shift-B). This will build the runtime library at a path such as `owl_basic\OwlRuntime\OwlRuntime\bin\Debug\OwlRuntime.dll`

The `OwlRuntime.dll` must be copied to the `owl_basic\compiler\codegen\clr` directory so it can be located by the compiler.

# Compiling an OWL BASIC program #

Create a simple OWL BASIC program in a text editor, such as:

```
REM hello_world.owl
MODE 7
PRINT "Hello, World!"
FOR N% = 1 TO 10
    PRINT "N% = ";N%
NEXT
REM Wait for key-press
A = GET 
```

and save it as `hello_world.owl` in `owl_basic\compiler\` then open a console and:

```
> cd owl_basic\compiler
> ipy main.py hello_world.owl
2011-04-17 22:27:22,432 - root - DEBUG - readFile
2011-04-17 22:27:22,526 - root - DEBUG - detokenize
2011-04-17 22:27:22,556 - root - DEBUG - indexLineNumbers

... lots of debugging output omitted...

2011-04-17 22:27:24,969 - root - DEBUG - Creating hello_world.exe
```

and check that the executable has indeed been created.

Now run the executable:

```
> hello_world.exe
```

which should pop up a window containing the output:

```
Hello, World!
N% = 1
N% = 2
N% = 3
N% = 4
N% = 5
N% = 6
N% = 7
N% = 8
N% = 9
N% = 10
```