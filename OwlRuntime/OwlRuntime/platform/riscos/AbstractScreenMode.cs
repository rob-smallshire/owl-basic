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
                    // The headless console (and the fallback target). Its initial
                    // size comes from OWL_SCREEN_SIZE, defaulting to MODE 7.
                    int[] init = InitialTextSize();
                    return CreateHeadlessText(vdu, init[0], init[1]);

                // Graphics modes have no live (windowed) renderer in this build.
                // When capturing to a PNG (OWL_CAPTURE_GRAPHICS) they render with
                // SkiaSharp; otherwise they fall back to a headless text mode
                // sized to the requested mode's text geometry, so a program
                // written for that mode at least lays its text out correctly.
                default:
                    if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("OWL_CAPTURE_GRAPHICS")))
                    {
                        int[] g = GraphicsModeParams(number);
                        if (g != null)
                        {
                            return CreateSkiaGraphics(vdu, g);
                        }
                    }
                    int[] dims = ModeTextSize(number);
                    if (dims != null)
                    {
                        return CreateHeadlessText(vdu, dims[0], dims[1]);
                    }
                    throw new NotSupportedException(
                        "Screen mode " + number + " is not available in this build.");
            }
        }

        // Kept in its own method (not inlined into CreateScreenMode) so that the
        // SkiaSharp reference is only resolved -- and SkiaSharp.dll only loaded --
        // when graphics capture is actually used. Programs that never enter a
        // graphics capture mode run without the SkiaSharp dependency present.
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        private static AbstractScreenMode CreateSkiaGraphics(VduSystem vdu, int[] g)
        {
            return new SkiaGraphicsScreenMode(vdu, g[0], g[1], g[2], g[3], (byte) g[4]);
        }

        /// <summary>The text cols/rows, pixel width/height and bits-per-pixel of
        /// a BBC graphics mode, or null if it is not a (known) graphics mode.</summary>
        private static int[] GraphicsModeParams(int mode)
        {
            switch (mode & 127)
            {
                case 0: return new[] { 80, 32, 640, 256, 1 };
                case 1: return new[] { 40, 32, 320, 256, 2 };
                case 2: return new[] { 20, 32, 160, 256, 4 };
                case 4: return new[] { 40, 32, 320, 256, 1 };
                case 5: return new[] { 20, 32, 160, 256, 2 };
                default: return null;
            }
        }

        /// <summary>
        /// A headless text screen mode of the given size: the raw streaming mode,
        /// or -- when OWL_CAPTURE_SCREEN is set -- the grid-capturing mode.
        /// </summary>
        internal static AbstractScreenMode CreateHeadlessText(VduSystem vdu, int width, int height)
        {
            return string.IsNullOrEmpty(Environment.GetEnvironmentVariable("OWL_CAPTURE_SCREEN"))
                ? (AbstractScreenMode) new RawConsoleScreenMode(vdu, width, height)
                : new GridTextScreenMode(vdu, width, height);
        }

        /// <summary>The text columns x rows of a BBC screen mode, or null if the
        /// mode's geometry is unknown.</summary>
        internal static int[] ModeTextSize(int mode)
        {
            switch (mode & 127)
            {
                case 0: return new int[] { 80, 32 };
                case 1: return new int[] { 40, 32 };
                case 2: return new int[] { 20, 32 };
                case 3: return new int[] { 80, 25 };
                case 4: return new int[] { 40, 32 };
                case 5: return new int[] { 20, 32 };
                case 6: return new int[] { 40, 25 };
                case 7: return new int[] { 40, 25 };
                default: return null;
            }
        }

        /// <summary>
        /// The initial headless console size: OWL_SCREEN_SIZE if set, as "WxH"
        /// (e.g. "40x32") or a mode ("MODE1"); otherwise MODE 7 (40x25), the
        /// BBC's power-on mode. A MODE command then resizes from here.
        /// </summary>
        internal static int[] InitialTextSize()
        {
            string spec = Environment.GetEnvironmentVariable("OWL_SCREEN_SIZE");
            if (!string.IsNullOrEmpty(spec))
            {
                spec = spec.Trim().ToUpperInvariant();
                if (spec.StartsWith("MODE") && int.TryParse(spec.Substring(4), out int mode))
                {
                    int[] md = ModeTextSize(mode);
                    if (md != null)
                    {
                        return md;
                    }
                }
                else
                {
                    string[] parts = spec.Split('X');
                    if (parts.Length == 2
                        && int.TryParse(parts[0], out int w) && w > 0
                        && int.TryParse(parts[1], out int h) && h > 0)
                    {
                        return new int[] { w, h };
                    }
                }
            }
            return ModeTextSize(7);
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
        /// Clear the text screen. Return true if the mode handled it; false to
        /// fall back to filling the text window with spaces (the default, used by
        /// the grid and pixel modes). Lets a streaming console clear differently
        /// rather than emitting a screenful of spaces.
        /// </summary>
        public virtual bool TryClearScreen()
        {
            return false;
        }

        /// <summary>
        /// Clear the graphics area to the graphics background colour (CLG / VDU
        /// 16). Return true if the mode handled it; false for modes with no
        /// addressable graphics surface (a streaming console), where CLG is a
        /// no-op.
        /// </summary>
        public virtual bool TryClearGraphics()
        {
            return false;
        }

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
