'''Tools for subprocesses in IronPython'''
import logging

__author__ = 'rjs'

def execute(name, *args):
    '''Execute an external process, and wait for it to complete.

    Args:
        name: The path name to the executable.

        *args: Remaining positional arguments are stringified and passed in
             order as command line arguments to the process.

    Returns:
        A 3-tuple containing an integer exit code and stdout and stderr as
        strings.
    '''
    logging.debug("process.execute(%s)" % name)
    from System.Diagnostics import Process
    p = Process()
    p.StartInfo.FileName = name
    p.StartInfo.Arguments = ' '.join(map(str, args))
    p.StartInfo.CreateNoWindow = True
    p.StartInfo.UseShellExecute = False
    p.StartInfo.RedirectStandardInput = True
    p.StartInfo.RedirectStandardOutput = True
    p.StartInfo.RedirectStandardError = True
    p.Start()
    p.WaitForExit()
    stdout = p.StandardOutput.ReadToEnd()
    stderr = p.StandardError.ReadToEnd()
    exit_code = p.ExitCode
    p.Close()
    return exit_code, stdout, stderr
  