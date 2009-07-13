using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Drawing;
using System.Drawing.Drawing2D;

namespace OwlRuntime.platform.riscos
{
    public class TrueGraphicsScreenMode : BaseGraphicsScreenMode
    {
        public TrueGraphicsScreenMode(VduSystem vdu, int textWidth, int textHeight, int pixelWidth, int pixelHeight, int unitsWidth, int unitsHeight, byte bitsPerPixel) :
            base(vdu, textWidth, textHeight, pixelWidth, pixelHeight, unitsWidth, unitsHeight, bitsPerPixel)
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

        protected override Color TextForegroundPlotColour()
        {
            return this.PhysicalTextForegroundColour;
        }

        protected override Color TextBackgroundPlotColour()
        {
            return this.PhysicalTextBackgroundColour;
        }

        // TODO unsure if this should be public or protected
        /// <summary>
        /// creates the pen using the HIcolour value from PhysicalGraphicsForegroundColour
        /// </summary>
        /// <returns>Pen</returns>
        protected override Pen Pen()
        {
            return new Pen(PhysicalGraphicsForegroundColour);
        }

        /// <summary>
        /// Create a brush for painting solid shapes using the current logical
        /// colour settings in conjunction with any palette settings.
        /// </summary>
        /// <returns></returns>
        protected override SolidBrush SolidBrush()
        {
            return new SolidBrush(PhysicalGraphicsForegroundColour);
        }

        public override void PaintBitmap(Graphics graphics)
        {
            graphics.DrawImage(Bitmap, 0, 0);
        }

        protected override Graphics ConfigureGraphics(Graphics graphics)
        {
            // Set the rendering quality
            switch (RenderingQuality)
            {
                case 0:
                    graphics.SmoothingMode = SmoothingMode.None;
                    graphics.PixelOffsetMode = PixelOffsetMode.None;
                    break;
                case 1:
                    graphics.SmoothingMode = SmoothingMode.AntiAlias;
                    graphics.PixelOffsetMode = PixelOffsetMode.None;
                    break;
                case 2:
                    graphics.SmoothingMode = SmoothingMode.AntiAlias;
                    graphics.PixelOffsetMode = PixelOffsetMode.HighQuality;
                    break;
                default:
                    graphics.SmoothingMode = SmoothingMode.None;
                    graphics.PixelOffsetMode = PixelOffsetMode.None;
                    break;
            }
            return graphics;
        }

    }
}
