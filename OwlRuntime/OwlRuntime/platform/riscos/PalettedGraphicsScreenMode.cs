using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Drawing;
using System.Drawing.Drawing2D;

namespace OwlRuntime.platform.riscos
{
    public class PalettedGraphicsScreenMode : BaseGraphicsScreenMode
    {
        private readonly Palette palette;
        private Color blueTextForegroundColour;
        private Color blueTextBackgroundColour;
        private Color blueGraphicsForegroundColour;
        private Color blueGraphicsBackgroundColour;



        public PalettedGraphicsScreenMode(VduSystem vdu, byte bitsPerPixel, int textWidth, int textHeight, int pixelWidth, int pixelHeight, int unitsWidth, int unitsHeight) :
            base(vdu, textWidth, textHeight, pixelWidth, pixelHeight, unitsWidth, unitsHeight, bitsPerPixel)
        {
            palette = new Palette(bitsPerPixel);
        }

        public override void UpdateTextBackgroundColour(int logicalColour, int tint)
        {           
            PhysicalTextBackgroundColour = palette.LogicalToPhysical(logicalColour, tint);
            blueTextBackgroundColour = palette.LogicalToBlue(logicalColour, tint);
        }

        public override void UpdateTextForegroundColour(int logicalColour, int tint)
        {
            PhysicalTextForegroundColour = palette.LogicalToPhysical(logicalColour, tint);
            blueTextForegroundColour = palette.LogicalToBlue(logicalColour, tint);
        }

        // Introduce notion of BluePenColour into this paletted class. This is a 'physical'
        // colour which encodes the logical colour into its blue channel.
        // PhysicalGraphicsForegroundColour should always return what the user sees
        // BluePenGraphicsForegroundColour encodes the LogicalGraphicsForegroundColour into the blue channel

        public override void UpdateGraphicsBackgroundColour(int logicalColour, int tint)
        {
            PhysicalGraphicsBackgroundColour = palette.LogicalToPhysical(logicalColour, tint);
            blueGraphicsBackgroundColour = palette.LogicalToBlue(logicalColour, tint);
        }

        public override void UpdateGraphicsForegroundColour(int logicalColour, int tint)
        {
            PhysicalGraphicsForegroundColour = palette.LogicalToPhysical(logicalColour, tint);
            blueGraphicsForegroundColour = palette.LogicalToBlue(logicalColour, tint);
        }


        /// <summary>
        /// creates the pen using the 'physical' colour which encodes the logical colour into its blue channel.
        /// </summary>
        /// <returns>Pen</returns>
        protected override Pen Pen()
        {
            // TODO ???? may not be correct to use the 'blueGraphicsForegroundColour' here
            // due to it being possible to draw in the background colour (also true for true colour drawing)
            // bottom 6 bits are logical colour and top two are tint.
            return new Pen(blueGraphicsForegroundColour);
        }

        /// <summary>
        /// Create a brush for painting solid shapes using the current logical
        /// colour settings in conjunction with any palette settings.
        /// </summary>
        /// <returns></returns>
        protected override SolidBrush SolidBrush()
        {
            return new SolidBrush(blueGraphicsForegroundColour);
        }

        protected override Graphics CreateGraphics()
        {
            Graphics graphics = vduForm.CreateGraphics();

            // The transform from OWL BASIC units to Windows pixel coordinates
            graphics.ResetTransform();
            graphics.TranslateTransform(0.0f, SquarePixelHeight, MatrixOrder.Prepend);
            graphics.ScaleTransform((SquarePixelWidth / (float)UnitsWidth), -(SquarePixelHeight / (float)UnitsHeight), MatrixOrder.Prepend);

            // Set the rendering quality to standard - may distort colours when editing palette
            graphics.SmoothingMode = SmoothingMode.None;
            graphics.PixelOffsetMode = PixelOffsetMode.None;
            return graphics;
        }

    }
}
