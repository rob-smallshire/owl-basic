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
            if (((Vdu.TextCursorX <= Vdu.TextWindowRightCol) && (Vdu.TextCursorX >= (Vdu.TextWindowLeftCol)) &&
               (Vdu.TextCursorY <= Vdu.TextWindowBottomRow) && (Vdu.TextCursorY >= (Vdu.TextWindowTopRow))))
            {

                // TODO temp code.. until scrolling implimented
                // make sure co-ords are within screen area and not the bottom left
                // hand corner to stop scrolling screen
                if (((Vdu.TextCursorX < TextWidth) &&
                   (Vdu.TextCursorX > -1) &&
                   (Vdu.TextCursorY < TextHeight) &&
                   (Vdu.TextCursorY > -1)) &&
                   !((Vdu.TextCursorX == (TextWidth - 1)) && (Vdu.TextCursorY == (TextHeight - 1))))
                {
                    // todo : we need a special case for printing a char in the bottom left hand corner of the window. Unsure how to acheive this.
                    Console.SetCursorPosition(Vdu.TextCursorX, Vdu.TextCursorY);
                    Console.Write(c);
                }




            }
            else
            {
            }
            Vdu.TextCursorX += TextCursor.MovementX;
            Vdu.TextCursorY += TextCursor.MovementY;
        }
    }
}
