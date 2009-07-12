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
        private int movementX;
        private int movementY;
        private int movementXEOL;
        private int movementYEOL;
        private int multiplier;
        private byte flags;
        private Boolean graphicsActionEOL;

        public TextCursor()
        {
            // default actions
            flags = 0;
            movementX = 1;
            movementY = 0;
            movementXEOL = 0;
            movementYEOL = 1;
            multiplier = 1;

        }

        public int MovementX
        {
            get { return movementX; }
        }

        public int MovementY
        {
            get { return movementY; }
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
                // unsure if i should impliment how the
                // BBC basic manual says this is implimented or how the PRM's do
                flags = value;

                // prm v3-1-594
                //if bit 5 Set then dont move cursor
                multiplier = ((flags & 32) != 0) ? 0 : 1;

                //decode text direction (normal without CRLF or EOL)
                int standardMovementX = 0;
                int standardMovementY = 0;
                standardMovementX = ((flags & 2) == 0) ? multiplier : 0 - multiplier;

                //decode text direction (CRLF or EOL)
                int EOLmovementX = 0;
                int EOLmovementY = 0;
                EOLmovementY = ((flags & 4) == 0) ? multiplier : 0 - multiplier;

                //if Bit 3 then transpose horiz / vert 
                if ((flags & 8) != 0)
                {
                    // transpose standard movement
                    int temp = standardMovementX;
                    standardMovementY = standardMovementX;
                    standardMovementX = temp;

                    //transpose EOL movement
                    temp = EOLmovementX;
                    EOLmovementY = EOLmovementX;
                    EOLmovementX = temp;

                }


                //bit 6 - if set then do not move to next line upon reaching the end of current viewport but only in graphics mode

                graphicsActionEOL = ((flags & 64) != 0) ? true : false;
            
            }
        }


    }
}
