using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    public class TrueGraphicsScreenMode : BaseGraphicsScreenMode
    {
        public TrueGraphicsScreenMode(VduSystem vdu, int textWidth, int textHeight, int squarePixelWidth, int squarePixelHeight) :
            base(vdu, textWidth, textHeight, squarePixelWidth, squarePixelHeight)
        {
        }

        /// <summary>
        /// Updates the current PhysicalTextBackgroundColour for this screen mode.
        /// </summary>
        /// <param name="logicalColour">Packed ARGB integer - which for these modes is actually a physical colour</param>
        /// <param name="tint">Unused</param>
        public override void UpdateTextBackgroundColour(int logicalColour, int tint)
        {
            PhysicalTextBackgroundColour = Color.FromArgb(logicalColour);
        }

        /// <summary>
        /// Updates the current PhysicalTextForegroundColour for this screen mode.
        /// </summary>
        /// <param name="logicalColour">Packed ARGB integer - which for these modes is actually a physical colour</param>
        /// <param name="tint">Unused</param>
        public override void UpdateTextForegroundColour(int logicalColour, int tint)
        {
            PhysicalTextForegroundColour = Color.FromArgb(logicalColour);
        }

        /// <summary>
        /// Updates the current PhysicalGraphicsBackgroundColour for this screen mode.
        /// </summary>
        /// <param name="logicalColour">Packed ARGB integer - which for these modes is actually a physical colour</param>
        /// <param name="tint">Unused</param>
        public override void UpdateGraphicsBackgroundColour(int logicalColour, int tint)
        {
            PhysicalGraphicsBackgroundColour = Color.FromArgb(logicalColour);
        }

        /// <summary>
        /// Updates the current PhysicalGraphicsForegroundColour for this screen mode.
        /// </summary>
        /// <param name="logicalColour">Packed ARGB integer - which for these modes is actually a physical colour</param>
        /// <param name="tint">Unused</param>
        public override void UpdateGraphicsForegroundColour(int logicalColour, int tint)
        {
            PhysicalGraphicsForegroundColour = Color.FromArgb(logicalColour);
        }
    }
}
