using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    internal class PalettedScreenMode : AbstractScreenMode
    {

        private List<Color> palette;

        // Create a ScreenMode from a mode number
        public PalettedScreenMode(int bitsPerPixel)
        {
            palette = new List<Color>(1 << bitsPerPixel);
            // Populate palette - reverse enginered from risc os palette file
            // prm1-558


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
                        int r = 17 * ((i & 7) & ((i & 16) >> 1));
                        int g = 17 * ((i & 3) & ((i & 96) >> 3));
                        int b = 17 * ((i & 3) & ((i & 8) >> 1) & ((i & 128) >> 4));
                        palette.Add(Color.FromArgb(r, g, b));
                    }
                    break;
                default:
                    throw new ArgumentOutOfRangeException();
            }
        }

        public override Color LogicalToPhysical(int logical)
        {
            return palette[logical];
        }
    }
}
