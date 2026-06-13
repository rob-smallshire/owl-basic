using System;

namespace OwlRuntime.platform.riscos
{
    /// <summary>
    /// A headless text mode (MODE 47) that streams characters straight to the
    /// host system's standard output. It performs no cursor positioning or
    /// buffer scrolling -- those are left to the host terminal -- so it works
    /// when output is redirected or piped and on any platform, making it the
    /// mode for command-line OWL BASIC programs that talk to a terminal via
    /// stdin and stdout. See <see cref="HeadlessTextScreenMode"/> for the shared
    /// headless behaviour, and <see cref="GridTextScreenMode"/> for the variant
    /// that captures the laid-out screen instead of streaming.
    /// </summary>
    public class RawConsoleScreenMode : HeadlessTextScreenMode
    {
        public RawConsoleScreenMode(VduSystem vdu, int width, int height) :
            base(vdu, width, height)
        {
        }

        public override void PrintCharAtText(char c)
        {
            Console.Out.Write(c);
        }

        public override void DeleteCharacterAtText()
        {
            // Destructive backspace on a host terminal: step back, overwrite the
            // character with a space, and step back again.
            Console.Out.Write('\b');
            Console.Out.Write(' ');
            Console.Out.Write('\b');
        }

        public override void NewLine()
        {
            // The base implementation enqueues VDU 10/13, which the VDU system
            // turns into text-cursor movements that a raw stream cannot honour.
            // Emit a newline directly instead -- but still return the text cursor
            // to column 0, so POS (and any subsequent VDU output) tracks the
            // start of the new line.
            Console.Out.Write('\n');
            Vdu.TextCursorX = 0;
        }

        public override void Dispose()
        {
            Console.Out.Flush();
        }
    }
}
