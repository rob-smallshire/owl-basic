using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    public class NoSuchScreenModeException : ApplicationException
    {
        private byte number;

        public NoSuchScreenModeException(byte number)
        {
            this.number = number;
        }
    }

    public abstract class AbstractScreenMode : IDisposable
    {
        private readonly int textWidth;
        private readonly int textHeight;
        private readonly int unitsWidth;
        private readonly int unitsHeight;
        private byte bitsPerPixel;
        private Color physicalTextForegroundColour;
        private Color physicalTextBackgroundColour;

        private readonly VduSystem vdu;

        public static AbstractScreenMode CreateScreenMode(VduSystem vdu, byte number)
        {
            switch (number & 127) // after reading prm only bottom 7 bits are used for setting mode (top bit is for shadow modes) PRM 1-597
            {
                case 0: return new PalettedGraphicsScreenMode(vdu, 1, 80, 32, 640, 256, 1280, 1024);
                case 1: return new PalettedGraphicsScreenMode(vdu, 2, 40, 32, 320, 256, 1280, 1024);
                case 2: return new PalettedGraphicsScreenMode(vdu, 4, 20, 32, 160, 256, 1280, 1024);
                case 3: return new PalettedTextScreenMode(vdu, 1, 80, 25); // 1280, 1000 checked by using mouse co-ords in this mode
                case 4: return new PalettedGraphicsScreenMode(vdu, 1, 40, 32, 320, 256, 1280, 1024);
                case 5: return new PalettedGraphicsScreenMode(vdu, 2, 20, 32, 160, 256, 1280, 1024);
                case 6: return new PalettedTextScreenMode(vdu, 1, 40, 25); // 1280, 1000
                case 7: return new TeletextScreenMode(vdu); // 1280, 1000
                case 8: return new PalettedGraphicsScreenMode(vdu, 2, 80, 32, 640, 256, 1280, 1024);
                case 9: return new PalettedGraphicsScreenMode(vdu, 4, 40, 32, 320, 256, 1280, 1024); 
                case 10: return new PalettedGraphicsScreenMode(vdu, 8, 20, 32, 160, 256, 1280, 1024);
                case 11: return new PalettedGraphicsScreenMode(vdu, 2, 80, 25, 640, 250, 1280, 1000);
                case 12: return new PalettedGraphicsScreenMode(vdu, 4, 80, 32, 640, 256, 1280, 1024);
                case 13: return new PalettedGraphicsScreenMode(vdu, 8, 40, 32, 320, 256, 1280, 1024);
                case 14: return new PalettedGraphicsScreenMode(vdu, 4, 80, 25, 640, 250, 1280, 1024);
                case 15: return new PalettedGraphicsScreenMode(vdu, 8, 80, 32, 640, 256, 1280, 1024);
                case 16: return new PalettedGraphicsScreenMode(vdu, 4, 132, 32, 1056, 256, 2112, 1024);
                case 17: return new PalettedGraphicsScreenMode(vdu, 4, 132, 25, 1056, 250, 2112, 1000);
                case 18: return new PalettedGraphicsScreenMode(vdu, 1, 80, 64, 640, 512, 1280, 1024);
                case 19: return new PalettedGraphicsScreenMode(vdu, 2, 80, 64, 640, 512, 1280, 1024);
                case 20: return new PalettedGraphicsScreenMode(vdu, 4, 80, 64, 640, 512, 1280, 1024);
                case 21: return new PalettedGraphicsScreenMode(vdu, 8, 80, 64, 640, 512, 1280, 1024);
                case 22: return new PalettedGraphicsScreenMode(vdu, 4, 96, 36, 768, 288, 768, 576);
                case 23: return new PalettedGraphicsScreenMode(vdu, 1, 144, 56, 1152, 896, 2304, 1792);
                case 24: return new PalettedGraphicsScreenMode(vdu, 8, 132, 32, 1056, 256, 2112, 1024);
                case 25: return new PalettedGraphicsScreenMode(vdu, 1, 80, 60,640, 480, 1280, 960);
                case 26: return new PalettedGraphicsScreenMode(vdu, 2, 80, 60, 640, 480, 1280, 960);
                case 27: return new PalettedGraphicsScreenMode(vdu, 4, 80, 60, 640, 480, 1280, 960);
                case 28: return new PalettedGraphicsScreenMode(vdu, 8, 80, 60, 640, 480, 1280, 960);
                case 29: return new PalettedGraphicsScreenMode(vdu, 1, 100, 75, 800, 600, 1600, 1200);
                case 30: return new PalettedGraphicsScreenMode(vdu, 2, 100, 75, 800, 600, 1600, 1200);
                case 31: return new PalettedGraphicsScreenMode(vdu, 4, 100, 75, 800, 600, 1600, 1200);
                case 33: return new PalettedGraphicsScreenMode(vdu, 1, 96, 36, 768, 288, 1536, 1152);
                case 34: return new PalettedGraphicsScreenMode(vdu, 2, 96, 36, 768, 288, 1536, 1152);
                case 35: return new PalettedGraphicsScreenMode(vdu, 4, 96, 36, 768, 288, 1536, 1152);
                case 36: return new PalettedGraphicsScreenMode(vdu, 8, 96, 36, 768, 288, 1536, 1152);
                case 37: return new PalettedGraphicsScreenMode(vdu, 1, 112, 44, 896, 352, 1792, 1408);
                case 38: return new PalettedGraphicsScreenMode(vdu, 2, 112, 44, 896, 352, 1792, 1408);
                case 39: return new PalettedGraphicsScreenMode(vdu, 4, 112, 44, 896, 352, 1792, 1408);
                case 40: return new PalettedGraphicsScreenMode(vdu, 8, 112, 44, 896, 352, 1792, 1408);
                case 41: return new PalettedGraphicsScreenMode(vdu, 1, 80, 44, 640, 352, 1280, 1408);
                case 42: return new PalettedGraphicsScreenMode(vdu, 2, 80, 44, 640, 352, 1280, 1408);
                case 43: return new PalettedGraphicsScreenMode(vdu, 4, 80, 44, 640, 352, 1280, 1408);
                case 44: return new PalettedGraphicsScreenMode(vdu, 1, 80, 25, 640, 200, 1280, 800);
                case 45: return new PalettedGraphicsScreenMode(vdu, 2, 80, 25, 640, 200, 1280, 800);
                case 46: return new PalettedGraphicsScreenMode(vdu, 4, 80, 25, 640, 200, 1280, 800);
                default: throw new NoSuchScreenModeException(number);
            }
        }

        protected AbstractScreenMode(VduSystem vdu, int textWidth, int textHeight, int unitsWidth, int unitsHeight, byte bitsPerPixel)
        {
            this.vdu = vdu;
            this.textWidth = textWidth;
            this.textHeight = textHeight;
            this.unitsWidth = unitsWidth;
            this.unitsHeight = unitsHeight;
            this.bitsPerPixel = bitsPerPixel;
        }

        public int TextWidth
        {
            get { return textWidth; }
        }

        public int TextHeight
        {
            get { return textHeight; }
        }

        public int UnitsWidth
        {
            get { return unitsWidth; }
        }

        public int UnitsHeight
        {
            get { return unitsHeight; }
        }

        public int LogicalColourCount
        {
            get { return 1 << bitsPerPixel; }
        }

        public byte BitsPerPixel
        {
            get { return bitsPerPixel; }
            protected set { bitsPerPixel = value; }
        }

        protected VduSystem Vdu
        {
            get { return vdu; }
        }

        public Color PhysicalTextForegroundColour
        {
            get { return physicalTextForegroundColour; }
            protected set { physicalTextForegroundColour = value; }
        }

        public Color PhysicalTextBackgroundColour
        {
            get { return physicalTextBackgroundColour; }
            protected set { physicalTextBackgroundColour = value; }
        }

        /// <summary>
        /// Draw a filled rectangle using the current graphics coordinates.
        /// This default implementation does nothing.
        /// </summary>
        public virtual void RectangleFill()
        {
        }

        public virtual void DottedLineIncludingBothEndPointsPatternRestarted()
        {
        }

        public virtual void DottedLineExcludingtheFinalPointPatternRestarted()
        {
        }

        public virtual void SolidLineExcludingtheInitialPoint()
        {
        }

        public virtual void SolidLineExcludingBothEndPoints()
        {
        }

        public virtual void DottedLineExcludingtheInitialPointPatternContinued()
        {
        }

        public virtual void DottedLineExcludingBothEndPointsPatternContinued()
        {
        }

        public virtual void HorizontalLineFillLeftRightToNonBackground()
        {
        }

        public virtual void PointPlot()
        {
        }

        public virtual void TriangleFill()
        {
        }

        public virtual void HorizontalLineFillRightToBackground()
        {
        }

        public virtual void HorizontalLineFillLeftToForeground()
        {
        }

        public virtual void ParallelogramFill()
        {
        }

        public virtual void HorizontalLineFillRightOnlyToNonForeground()
        {
        }

        public virtual void FloodToNonBackground()
        {
        }

        public virtual void FloodToForeground()
        {
        }

        public virtual void CircleOutline()
        {
        }

        public virtual void CircleFill()
        {
        }

        public virtual void CircularArc()
        {
        }

        public virtual void Segment()
        {
        }

        public virtual void Sector()
        {
        }

        public virtual void RelativeRectangleMove()
        {
        }

        public virtual void RelativeRectangleCopy()
        {
        }

        public virtual void SpritePlot()
        {
        }

        public virtual void FontPrinting()
        {
        }

        public virtual void EllipseFill()
        {
        }

        public virtual void EllipseOutline()
        {
        }

        public virtual void AbsoluteRectangleCopy()
        {
        }

        public virtual void AbsoluteRectangleMove()
        {
        }

        public virtual void SolidLineExcludingTheFinalPoint()
        {
        }

        public virtual void SolidLineIncludingBothEndPoints()
        {
        }

        public abstract void Dispose();

        public virtual void UpdateGraphicsBackgroundColour(int logicalColour, int tint)
        {
            // Do nothing
        }

        public virtual void UpdateGraphicsForegroundColour(int logicalColour, int tint)
        {
            // Do nothing
        }

        public abstract void UpdateTextBackgroundColour(int logicalColour, int tint);

        public abstract void UpdateTextForegroundColour(int logicalColour, int tint);

        /// <summary>
        /// Update the palette for the current screen mode by mapping the logicalColour
        /// index to the colour of the entry in the physical (i.e. default) palette.
        /// </summary>
        /// <param name="logicalColourIndex">The logical colour to be redefined</param>
        /// <param name="physcialColourIndex">An index into the physcial (i.e. default) palette.</param>
        public virtual void UpdatePalette(byte logicalColourIndex, byte physcialColourIndex)
        {
            // Do nothing
        }

        /// <summary>
        /// Update the palette for the current screen mode by mapping the logicalColour
        /// index to the colour specified by red, green and blue.
        /// </summary>
        /// <param name="logicalColour">A logical colour - index into the palette</param>
        /// <param name="red">Red channel 0-255</param>
        /// <param name="green">Green channel 0-255</param>
        /// <param name="blue">Blue channel 0-255</param>
        public virtual void UpdatePalette(byte logicalColour, byte red, byte green, byte blue)
        {
            // Do nothing
        }

        public virtual void UpdatePaletteFirstFlash(byte colour, byte red, byte green, byte blue)
        {
            // Do nothing
        }

        public virtual void UpdatePaletteSecondFlash(byte colour, byte red, byte green, byte blue)
        {
            // Do nothing
        }

        public virtual void UpdatePaletteBorder(byte colour, byte red, byte green, byte blue)
        {
            // Do nothing
        }

        public virtual void UpdatePointerPalette(byte colour, byte red, byte green, byte blue)
        {
            // Do nothing
        }

        public virtual void UpdateRenderingQuality(byte quality)
        {
            // Do nothing
        }

        /// <summary>
        /// Reset to the default palette. Reset text and graphics, background and foreground colours to
        /// the default for the mode.
        /// </summary>
        public void ResetPaletteAndColours()
        {
            // Do nothing
        }

        public abstract void PrintCharAtGraphics(char c);
        public abstract void PrintCharAtText(char c);
        public abstract void ScrollTextArea(int left, int bottom, int right, int top, Direction direction, ScrollMovement movement);
    }
}
