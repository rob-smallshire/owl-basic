using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    public class Palette
    {
        //private static Palette physicalPalette;
        //private static HashSet<int, Palette> defaultPalettes;

        private readonly int bitsPerPixel;
        private readonly List<Color> palette;

        //static Palette()
        //{
        //    physicalPalette

        //    defaultPalettes = new HashSet<int, Palette>();
            
        //}

        public Palette(byte bitsPerPixel)
        {
            this.bitsPerPixel = bitsPerPixel;
            palette = new List<Color>(1 << bitsPerPixel);
            // Populate palette - reverse enginered from risc os palette file prm1-558

            // TODO Effect of the mode command prm1-597
            // The mode command causes the following actions:
            // Cursor editing is terminated if currently in use
            // VDU 4 mode is entered
            // The text and graphics windows are restored to their default values
            // The text cursor is moved to its home position
            // The graphics cursor is moved to (0,0)
            // The graphics origin is moved to (0,0)
            // Paged mode is terminated if currently in use
            // The text and graphics foreground colours are set to white
            // The text and graphics background colours are set to black (colour 0)
            // The colour patterns are set to their defaults for the new mode
            // The ECF origin is set to (0,0)
            // The dot pattern for dotted lines is reset to &AAAAAAAA
            // The dot pattern repeat length is reset to 8
            // The screen is cleared to the current text background colour (ie black).


            // The logical-physical colour map is set to the new mode’s default
            switch (bitsPerPixel)
            {
                case 1:
                    palette.Add(Color.FromArgb(0, 0, 0));
                    palette.Add(Color.FromArgb(255, 255, 255));
                    break;
                case 2:
                    palette.Add(Color.FromArgb(0, 0, 0));
                    palette.Add(Color.FromArgb(255, 0, 0));
                    palette.Add(Color.FromArgb(255, 255, 0));
                    palette.Add(Color.FromArgb(255, 255, 255));
                    break;
                case 4:
                    palette.Add(Color.FromArgb(0, 0, 0));
                    palette.Add(Color.FromArgb(255, 0, 0));
                    palette.Add(Color.FromArgb(0, 255, 0));
                    palette.Add(Color.FromArgb(255, 255, 0));
                    palette.Add(Color.FromArgb(0, 0, 255));
                    palette.Add(Color.FromArgb(255, 0, 255));
                    palette.Add(Color.FromArgb(0, 255, 255));
                    palette.Add(Color.FromArgb(255, 255, 255));
                    palette.Add(Color.FromArgb(0, 0, 0));
                    palette.Add(Color.FromArgb(255, 0, 0));
                    palette.Add(Color.FromArgb(0, 255, 0));
                    palette.Add(Color.FromArgb(255, 255, 0));
                    palette.Add(Color.FromArgb(0, 0, 255));
                    palette.Add(Color.FromArgb(255, 0, 255));
                    palette.Add(Color.FromArgb(0, 255, 255));
                    palette.Add(Color.FromArgb(255, 255, 255));
                    break;
                case 8:
                    for (int i = 0; i <= 255; i++)
                    {
                        int r = 17*((i & 7) | ((i & 16) >> 1));
                        int g = 17*((i & 3) | ((i & 96) >> 3));
                        int b = 17*((i & 3) | ((i & 8) >> 1) | ((i & 128) >> 4));
                        palette.Add(Color.FromArgb(r, g, b));
                    }
                    break;
                default:
                    throw new ArgumentOutOfRangeException();
            }
        }


        public int BitsPerPixel
        {
            get { return bitsPerPixel; }
        }

        public Color LogicalToPhysical(int logical)
        {
 	        return palette[logical];
        }

        public Color LogicalToPhysical(int logicalColour, int tint)
        {
            if (BitsPerPixel == 8)
            {
                int index = 0;
                index = index | (logicalColour & 33) << 2;
                index = index | (logicalColour & 14) << 3;
                index = index | (logicalColour & 16) >> 1;
                index = index | tint >> 6;
                return LogicalToPhysical(index);
            }
            return LogicalToPhysical(logicalColour);
        }
    }
}
