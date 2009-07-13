using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing.Imaging;
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
        private readonly Bitmap indexedBitmap;

        public PalettedGraphicsScreenMode(VduSystem vdu, byte bitsPerPixel, int textWidth, int textHeight, int pixelWidth, int pixelHeight, int unitsWidth, int unitsHeight) :
            base(vdu, textWidth, textHeight, pixelWidth, pixelHeight, unitsWidth, unitsHeight, bitsPerPixel)
        {
            palette = new Palette(bitsPerPixel);
            indexedBitmap = new Bitmap(SquarePixelWidth, SquarePixelHeight, PixelFormat.Format8bppIndexed);
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

        protected override Color TextForegroundPlotColour()
        {
            return blueTextForegroundColour;
        }

        protected override Color TextBackgroundPlotColour()
        {
            return blueTextBackgroundColour;
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

        public override void PaintBitmap(Graphics graphics)
        {
            // Set the palette
            ColorPalette pal = indexedBitmap.Palette;
            for (int i = 0; i < (1 << BitsPerPixel); ++i)
            {
                pal.Entries[i] = palette.LogicalToPhysical(i);
            }
            //
            indexedBitmap.Palette = pal;

            IndexedFromBlueBitmap(Bitmap, indexedBitmap);

            // for testing only - need to eventually draw from  indexed bitmap
            graphics.DrawImage(indexedBitmap, 0, 0);
        }

        static private void IndexedFromBlueBitmap(Bitmap sourceBitmap, Bitmap destBitmap)
        {

            BitmapData indexedBitmapData = null;
            try
            {
                Debug.Assert(destBitmap.Height == sourceBitmap.Height);
                Debug.Assert(destBitmap.Width == sourceBitmap.Width);
                Rectangle rectangle = new Rectangle(0, 0, sourceBitmap.Width, sourceBitmap.Height);
                indexedBitmapData = destBitmap.LockBits(
                    rectangle,
                    ImageLockMode.ReadWrite, PixelFormat.Format8bppIndexed);

                BitmapData sourceBitmapData = null;
                try
                {
                    // data for the orig bitmap
                    sourceBitmapData = sourceBitmap.LockBits(
                        rectangle,
                        ImageLockMode.ReadOnly, PixelFormat.Format24bppRgb);
                    // size of the source pixels in bytes
                    const int sourcePixelSize = 3;

                    for (int y = 0; y < sourceBitmapData.Height; ++y)
                    {
                        unsafe
                        {
                            byte* sourceRow = (byte*) sourceBitmapData.Scan0 + (y * sourceBitmapData.Stride);
                            byte* destRow = (byte*) indexedBitmapData.Scan0 + (y * indexedBitmapData.Stride);

                            for (int x = 0; x < sourceBitmapData.Width; ++x)
                            {
                                destRow[x] = sourceRow[x * sourcePixelSize];
                            }
                        }
                    }
                }
                finally
                {
                    sourceBitmap.UnlockBits(sourceBitmapData);
                }
            }
            finally
            {
                destBitmap.UnlockBits(indexedBitmapData);
            }
        }

        protected override Graphics ConfigureGraphics(Graphics graphics)
        {
            // Set the rendering quality to standard - may distort colours when editing palette
            graphics.SmoothingMode = SmoothingMode.None;
            graphics.PixelOffsetMode = PixelOffsetMode.None;
            return graphics;
        }
    }
}
