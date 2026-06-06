using System;

namespace OwlRuntime.platform.riscos
{
    /// <summary>
    /// A screen mode (MODE 47) that talks directly to the host system's
    /// standard streams.
    ///
    /// Structurally this follows the text-mode family (cf. mode 7,
    /// <see cref="TeletextScreenMode"/>): it derives from
    /// <see cref="BaseTextScreenMode"/> and leaves colour handling as no-ops.
    /// The deliberate difference is that it is *raw*: it writes characters
    /// straight to standard output and performs no cursor positioning, window
    /// sizing or buffer scrolling. The managed text modes call
    /// Console.SetWindowSize / SetCursorPosition / MoveBufferArea, which throw
    /// when output is redirected or piped; this mode works in those cases and
    /// on any platform, making it the mode for command-line OWL BASIC programs
    /// that communicate with a host terminal via stdin and stdout.
    /// </summary>
    public class RawConsoleScreenMode : BaseTextScreenMode
    {
        public RawConsoleScreenMode(VduSystem vdu) :
            base(vdu, 80, 25, 1)
        {
            // Note: unlike the managed text modes we do NOT call SetConsoleSize();
            // a raw stream has no window to size and doing so fails when stdout
            // is redirected.
        }

        public override void PrintCharAtText(char c)
        {
            Console.Out.Write(c);
        }

        public override void ScrollTextArea(int left, int bottom, int right, int top, Direction direction, ScrollMovement movement)
        {
            // Raw console: the host terminal manages its own scrolling.
        }

        public override void Dispose()
        {
            Console.Out.Flush();
        }

        public override void UpdateTextBackgroundColour(int logicalColour, int tint)
        {
            // Raw console: no colour handling.
        }

        public override void UpdateTextForegroundColour(int logicalColour, int tint)
        {
            // Raw console: no colour handling.
        }
    }
}
