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
    public class PalettedTextScreenMode : BaseTextScreenMode
    {
        private readonly Palette palette;

        public PalettedTextScreenMode(VduSystem vdu, byte bitsPerPixel, int textWidth, int textHeight) :
            base(vdu, textWidth, textHeight, bitsPerPixel)
        {
            palette = new Palette(bitsPerPixel);
        }

        public override void Dispose()
        {
            // Do nothing
        }

        public override void UpdateTextBackgroundColour(int logicalColour, int tint)
        {
            PhysicalTextBackgroundColour = palette.LogicalToPhysical(logicalColour, tint);
        }

        public override void UpdateTextForegroundColour(int logicalColour, int tint)
        {
            PhysicalTextForegroundColour = palette.LogicalToPhysical(logicalColour, tint);
        }
    }
}
