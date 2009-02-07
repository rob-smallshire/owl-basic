using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    /// <summary>
    /// Only used for MODE 3 and MODE 6
    /// </summary>
    public class PalettedTextScreenMode : BaseTextScreenMode, IPalette
    {
        private readonly Palette palette;

        public PalettedTextScreenMode(VduSystem vdu, byte bitsPerPixel, int textWidth, int textHeight) :
            base(vdu, textWidth, textHeight)
        {
            palette = new Palette(bitsPerPixel);
        }

        public Color LogicalToPhysical(int logical)
        {
            return palette.LogicalToPhysical(logical);
        }

        public override void Dispose()
        {
            // Do nothing
        }
    }
}
