using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    public class PalettedGraphicsScreenMode : BaseGraphicsScreenMode, IPalette
    {
        private readonly Palette palette;

        public PalettedGraphicsScreenMode(VduSystem vdu, byte bitsPerPixel, int textWidth, int textHeight, int squarePixelWidth, int squarePixelHeight) :
            base(vdu, textWidth, textHeight, squarePixelWidth, squarePixelHeight)
        {
            palette = new Palette(bitsPerPixel);
        }

        public Color LogicalToPhysical(int logical)
        {
            return palette.LogicalToPhysical(logical);
        }

        protected override Color GraphicsForegroundColour()
        {
            return palette.LogicalToPhysical(Vdu.GraphicsForegroundPaletteIndex);
        }
    }
}
