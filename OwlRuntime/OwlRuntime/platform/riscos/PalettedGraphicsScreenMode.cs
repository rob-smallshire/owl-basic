﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    public class PalettedGraphicsScreenMode : BaseGraphicsScreenMode
    {
        private readonly Palette palette;
        // private Colour bluePenColour;

        public PalettedGraphicsScreenMode(VduSystem vdu, byte bitsPerPixel, int textWidth, int textHeight, int pixelWidth, int pixelHeight, int unitsWidth, int unitsHeight) :
            base(vdu, textWidth, textHeight, pixelWidth, pixelHeight, unitsWidth, unitsHeight)
        {
            palette = new Palette(bitsPerPixel);
        }

        public override void UpdateTextBackgroundColour(int logicalColour, int tint)
        {           
            PhysicalTextBackgroundColour = palette.LogicalToPhysical(logicalColour, tint);
        }

        public override void UpdateTextForegroundColour(int logicalColour, int tint)
        {
            PhysicalTextForegroundColour = palette.LogicalToPhysical(logicalColour, tint);
        }

        // Introduce notion of BluePenColour into this paletted class. This is a 'physical'
        // colour which encodes the logical colour into its blue channel.
        // PhysicalGraphicsForegroundColour should always return what the user sees
        // BluePenGraphicsForegroundColour encodes the LogicalGraphicsForegroundColour into the blue channel

        public override void UpdateGraphicsBackgroundColour(int logicalColour, int tint)
        {
            PhysicalGraphicsBackgroundColour = palette.LogicalToPhysical(logicalColour, tint);
        }

        public override void UpdateGraphicsForegroundColour(int logicalColour, int tint)
        {
            PhysicalGraphicsForegroundColour = palette.LogicalToPhysical(logicalColour, tint);
        }
    }
}
