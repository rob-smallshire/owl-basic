using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    public abstract class BaseTextScreenMode : AbstractScreenMode
    {
        protected BaseTextScreenMode(VduSystem vdu, int textWidth, int textHeight, byte bitsPerPixel) :
            base(vdu, textWidth, textHeight, 1280, 1024, bitsPerPixel)
        {
            Console.SetWindowSize(TextWidth, TextHeight);
            Console.SetBufferSize(TextWidth, TextHeight);
        }

        public override void PrintCharAtGraphics(char c)
        {
        }

        public override void PrintCharAtText(char c)
        {
            // check that the co-ords are within the current text window
            int textCursorX = Vdu.TextCursorX;
            int textCursorY = Vdu.TextCursorY;
            // TODO temp code.. until scrolling implimented
            // make sure co-ords are within screen area and not the bottom left
            // hand corner to stop scrolling screen
            Console.SetCursorPosition(textCursorX, textCursorY);
            Console.Write(c);
            if ((textCursorX == (TextWidth - 1)) && (textCursorY == (TextHeight - 1)))
            {
                // todo : we need a special case for printing a char in the bottom left
                //        hand corner of the window. Unsure how to acheive this.
                // Apparently it can be done using Console.MoveBufferArea
                // There is more information here http://stackoverflow.com/questions/739526/disabling-scroll-with-system-console-write
                Console.MoveBufferArea(0, 0, Console.WindowWidth, Console.WindowHeight, 0, 1);
            }
        }

    }
}
