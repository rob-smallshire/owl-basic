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
            Console.SetCursorPosition(Vdu.TextCursorX, Vdu.TextCursorY);
            Console.Write(c);
            Vdu.TextCursorX += TextCursor.MovementX;
            Vdu.TextCursorY += TextCursor.MovementY;
        }
    }
}
