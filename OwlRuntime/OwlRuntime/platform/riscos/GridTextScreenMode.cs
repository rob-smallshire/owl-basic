using System;

namespace OwlRuntime.platform.riscos
{
    /// <summary>
    /// A headless text mode that places each character on an in-memory 80x25
    /// grid at the text cursor -- honouring TAB(x,y) positioning and CLS -- and
    /// dumps the laid-out screen on Dispose (i.e. at program exit). Unlike
    /// <see cref="RawConsoleScreenMode"/>, which streams characters and so
    /// discards cursor positioning, this preserves the on-screen layout, which
    /// makes it useful for inspecting and testing text formatting.
    ///
    /// Selected by setting the OWL_CAPTURE_SCREEN environment variable; see
    /// <see cref="AbstractScreenMode.CreateScreenMode"/>.
    /// </summary>
    public class GridTextScreenMode : HeadlessTextScreenMode
    {
        private readonly char[,] grid;
        private bool dumped;

        public GridTextScreenMode(VduSystem vdu, int width, int height) :
            base(vdu, width, height)
        {
            grid = new char[TextHeight, TextWidth];
            for (int y = 0; y < TextHeight; ++y)
            {
                for (int x = 0; x < TextWidth; ++x)
                {
                    grid[y, x] = ' ';
                }
            }
            // The generated program does not dispose the VDU system on exit, so
            // dump the captured screen when the process ends (Dispose also dumps
            // if it is reached first; a guard prevents a double dump).
            AppDomain.CurrentDomain.ProcessExit += (sender, e) => DumpGrid();
        }

        public override void PrintCharAtText(char c)
        {
            PlaceChar(c);
        }

        public override void DeleteCharacterAtText()
        {
            PlaceChar(' ');
        }

        // NewLine is intentionally not overridden: the base implementation
        // enqueues VDU 10/13, which the VDU system turns into cursor movement
        // (down a row, back to the left) and a scroll at the bottom -- all of
        // which the grid honours by position. (The raw mode overrides NewLine
        // precisely because a stream cannot honour those movements.)

        public override void ScrollTextArea(int left, int bottom, int right, int top, Direction direction, ScrollMovement movement)
        {
            // Unlike the raw mode (where the host terminal scrolls), the grid is
            // ours to scroll. Move the rows of the region and blank the row that
            // is vacated, so output past the bottom of the screen is preserved as
            // it would be on a real display.
            if (direction == Direction.Up)
            {
                for (int y = top; y < bottom; ++y)
                {
                    for (int x = left; x <= right; ++x)
                    {
                        grid[y, x] = grid[y + 1, x];
                    }
                }
                BlankRow(bottom, left, right);
            }
            else if (direction == Direction.Down)
            {
                for (int y = bottom; y > top; --y)
                {
                    for (int x = left; x <= right; ++x)
                    {
                        grid[y, x] = grid[y - 1, x];
                    }
                }
                BlankRow(top, left, right);
            }
            // Horizontal (Left/Right) text scrolling is rare and not modelled.
        }

        private void BlankRow(int y, int left, int right)
        {
            for (int x = left; x <= right; ++x)
            {
                grid[y, x] = ' ';
            }
        }

        public override void Dispose()
        {
            DumpGrid();
            Console.Out.Flush();
        }

        private void PlaceChar(char c)
        {
            int x = Vdu.TextCursorX;
            int y = Vdu.TextCursorY;
            if (x >= 0 && x < TextWidth && y >= 0 && y < TextHeight)
            {
                grid[y, x] = c;
            }
        }

        /// <summary>
        /// Write the grid as text: each row right-trimmed, with trailing blank
        /// rows dropped, so the captured layout reads cleanly.
        /// </summary>
        private void DumpGrid()
        {
            if (dumped)
            {
                return;
            }
            dumped = true;
            int lastNonBlank = -1;
            string[] rows = new string[TextHeight];
            for (int y = 0; y < TextHeight; ++y)
            {
                char[] row = new char[TextWidth];
                for (int x = 0; x < TextWidth; ++x)
                {
                    row[x] = grid[y, x];
                }
                rows[y] = new string(row).TrimEnd();
                if (rows[y].Length > 0)
                {
                    lastNonBlank = y;
                }
            }
            for (int y = 0; y <= lastNonBlank; ++y)
            {
                Console.Out.Write(rows[y]);
                Console.Out.Write('\n');
            }
        }
    }
}
