namespace OwlRuntime.platform.riscos
{
    /// <summary>
    /// Shared behaviour for the headless text screen modes: those that run
    /// cross-platform without the managed console's window and cursor APIs
    /// (Console.SetWindowSize / SetCursorPosition / MoveBufferArea), which throw
    /// when output is redirected or piped.
    ///
    /// What differs between the headless modes is only what they do with each
    /// character placed at the text cursor: <see cref="RawConsoleScreenMode"/>
    /// streams it straight to standard output (cursor positioning is left to the
    /// host terminal); <see cref="GridTextScreenMode"/> places it on an in-memory
    /// grid so the laid-out screen can be captured. Colour and scrolling are
    /// no-ops for both.
    ///
    /// The columns x rows are supplied by the factory
    /// (<see cref="AbstractScreenMode.CreateScreenMode"/>): the initial console
    /// size comes from OWL_SCREEN_SIZE (default 80x25), and a MODE command then
    /// resizes to that mode's text geometry.
    /// </summary>
    public abstract class HeadlessTextScreenMode : BaseTextScreenMode
    {
        protected HeadlessTextScreenMode(VduSystem vdu, int width, int height) :
            base(vdu, width, height, 1)
        {
            // Unlike the managed text modes we do NOT call SetConsoleSize(): a
            // headless stream has no window to size, and doing so fails when
            // standard output is redirected.
        }

        public override void ScrollTextArea(int left, int bottom, int right, int top, Direction direction, ScrollMovement movement)
        {
            // Headless text: scrolling is left to the consumer (the host terminal
            // for the raw mode, and unneeded for a single grid snapshot).
        }

        public override void UpdateTextBackgroundColour(int logicalColour, int tint)
        {
            // Headless text: no colour handling.
        }

        public override void UpdateTextForegroundColour(int logicalColour, int tint)
        {
            // Headless text: no colour handling.
        }
    }
}
