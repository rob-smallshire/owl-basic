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
            // after reading prm only bottom 7 bits are used for setting mode (top bit is for shadow modes) PRM 1-597
            switch (number & 127)
            {
                // Text-only modes work headless and cross-platform.
                case 3: return new PalettedTextScreenMode(vdu, 1, 80, 25); // 1280, 1000 checked by using mouse co-ords in this mode
                case 6: return new PalettedTextScreenMode(vdu, 1, 40, 25); // 1280, 1000
                case 7: return new TeletextScreenMode(vdu); // 1280, 1000
                case 47:
                    // The headless console mode either streams characters or, when
                    // OWL_CAPTURE_SCREEN is set, captures the laid-out screen into
                    // a grid (an inspection/testing aid for text formatting).
                    return string.IsNullOrEmpty(Environment.GetEnvironmentVariable("OWL_CAPTURE_SCREEN"))
                        ? (AbstractScreenMode) new RawConsoleScreenMode(vdu)
                        : new GridTextScreenMode(vdu);

                // Graphics modes (0-2, 4, 5, 8-46) are temporarily unavailable: the
                // GDI+/WinForms graphics layer that implemented them is excluded
                // from this build pending a SkiaSharp/Avalonia port. The full mode
                // table is preserved in version control.
                default:
                    throw new NotSupportedException(
                        "Screen mode " + number + " is not available in this build. " +
                        "Graphics modes are temporarily disabled while the GDI+/WinForms " +
                        "renderer is ported to SkiaSharp/Avalonia; use a text mode (3, 6, 7) " +
                        "or the raw console mode (47).");
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

        /// <summary>
        /// Destructively delete the character to the left of the text cursor
        /// (VDU 127). The default does nothing; text modes that drive a host
        /// terminal override it.
        /// </summary>
        public virtual void DeleteCharacterAtText()
        {
            // Do nothing by default.
        }
        public abstract void ScrollTextArea(int left, int bottom, int right, int top, Direction direction, ScrollMovement movement);

        public virtual void NewLine()
        {
            // This default implementation calls back to the VDU system
            vdu.Enqueue((byte) 10);
            vdu.Enqueue((byte) 13);
        }

        public virtual void Write(char c)
        {
            // This default implemenatation calls back to the VDU system
            vdu.Enqueue(c);   
        }

        public virtual void Write(string s)
        {
            // This default implementation calls back to the VDU system
            vdu.Enqueue(s);
        }
    }
}
