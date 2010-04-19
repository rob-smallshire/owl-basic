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
            if (textCursorX == (TextWidth - 1))
            {
                if (textCursorY == (TextHeight - 1))
                {
                    // todo : we need a special case for printing a char in the bottom left
                    //        hand corner of the window. Unsure how to acheive this.
                    // Apparently it can be done using Console.MoveBufferArea
                    // There is more information here http://stackoverflow.com/questions/739526/disabling-scroll-with-system-console-write
                    Console.MoveBufferArea(0, 0, Console.WindowWidth, Console.WindowHeight, 0, 1);
                }
            }
        }

        public override void ScrollTextArea(int left, int bottom, int right, int top, Direction direction, ScrollMovement movement)
        {
            int leftSourceOffset = 0;
            int topSourceOffset = 0;
            int widthOffset = 0;
            int heightOffset = 0;
            int leftTargetOffset = 0;
            int topTargetOffset = 0;

            switch (direction)
            {                         
                case Direction.Up:    
                    {
                        leftSourceOffset = 0;
                        topSourceOffset  = 1; 
                        widthOffset      = 1;
                        heightOffset     = 0;
                        leftTargetOffset = 0;
                        topTargetOffset  = 0;
                        break;
                    }
                case Direction.Down:
                    {
                        leftSourceOffset = 0;
                        topSourceOffset  = 0;
                        widthOffset      = 1; 
                        heightOffset     = 0;
                        leftTargetOffset = 0;
                        topTargetOffset  = 1;
                        break;
                    }
                case Direction.Left:
                    {
                        leftSourceOffset = 1;
                        topSourceOffset  = 0; 
                        widthOffset      = 0;
                        heightOffset     = 1;
                        leftTargetOffset = 0;
                        topTargetOffset  = 0;
                        break;
                    }
                case Direction.Right:
                    {
                        leftSourceOffset = 0;
                        topSourceOffset  = 0;
                        widthOffset      = 0;
                        heightOffset     = 1;
                        leftTargetOffset = 1;
                        topTargetOffset  = 0;
                        break;
                    }
            }
            int leftSourceBuffer = left + leftSourceOffset;
            int topSourceBuffer = top + topSourceOffset;
            int widthBuffer = right - left + widthOffset;
            int heightBuffer = bottom - top + heightOffset;
            int leftTargetBuffer = left + leftTargetOffset;
            int topTargetBuffer = top + topTargetOffset;

            Console.MoveBufferArea(leftSourceBuffer, topSourceBuffer,
                widthBuffer, heightBuffer,
                leftTargetBuffer, topTargetBuffer);
        }
    }
}
