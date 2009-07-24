using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    class TextCursor
    {
        // private int positionX;
        // private int positionY;

        private int standardMovementX;
        private int standardMovementY;
        private int movementXEOL;
        private int movementYEOL;
        private int multiplier;
        private byte flags;
        private Boolean graphicsActionEOL;
        private Boolean transposed;
        // multipliers for the x and y directions.
        // values are +1, 0 or -1 (0 not used at the moment but will be needed later)
        private int directionX;
        private int directionY;

        // thinking of storing the bounds(text window), cursor position,  home position and the scroll position in this class
        // this will allow all of the maths to do with cursor to be in one place.
        // this also allows all of the code to positioning the cursor to be placed in here

        public int DirectionY
        {
            get { return directionY; }
        }

        public int DirectionX
        {
            get { return directionX; }
        }


        public TextCursor()
        {
            // default actions
            flags = 0;
            standardMovementX = 1;
            standardMovementY = 0;
            movementXEOL = 0;
            movementYEOL = 1;
            multiplier = 1;
            transposed = false;

        }

        public Boolean Transposed
        {
            get { return transposed; }
        }

        public int MovementX
        {
            get { return standardMovementX; }
        }

        public int MovementY
        {
            get { return standardMovementY; }
        }

        public int MovementXEOL
        {
            get { return movementXEOL; }
        }

        public int MovementYEOL
        {
            get { return movementYEOL; }
        }

        public Boolean GraphicsActionEOL
        {
            get { return graphicsActionEOL; }
        }

        public byte Flags
        {
            get { return flags; }
            set {
                flags = value;

                // prm v3-1-594
                //if bit 5 Set then dont move cursor
                multiplier = ((flags & 32) != 0) ? 0 : 1;

                int transpose = ((flags & 8) >> 3);
                transposed = (transpose == 1);
                int xbit = 1 << (1 + transpose);
                int ybit = 1 << (2 - transpose);

                //decode text direction (normal without CRLF or EOL)
                standardMovementX = 0;
                standardMovementY = 0;
                standardMovementX = ((flags & xbit) == 0) ? multiplier : 0 - multiplier;

                directionX = ((flags & xbit) == 0) ? 1 : -1;
                directionY = ((flags & ybit) == 0) ? 1 : -1;

                //decode text direction (CRLF or EOL)
                movementXEOL = 0;
                movementYEOL = 0;
                movementYEOL = ((flags & ybit) == 0) ? multiplier : 0 - multiplier; //TODO: not sure if multiplier is needed here or a static 1

                //if Bit 3 then transpose horiz / vert 
                if (transpose == 1)
                {
                    // transpose standard movement
                    int temp = standardMovementY;
                    standardMovementY = standardMovementX;
                    standardMovementX = temp;

                    //transpose EOL movement
                    temp = movementYEOL;
                    movementYEOL = movementXEOL;
                    movementXEOL = temp;

                }


                //bit 6 - if set then do not move to next line upon reaching the end of current viewport but only in graphics mode

                graphicsActionEOL = ((flags & 64) != 0) ? true : false;
            
            }
        }


    }
}
