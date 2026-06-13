using System;
using SkiaSharp;

namespace OwlRuntime.platform.riscos
{
    /// <summary>
    /// A windowless graphics screen mode that renders with SkiaSharp into an
    /// off-screen surface and writes the result as a PNG when the program exits.
    /// Selected by setting OWL_CAPTURE_GRAPHICS to the output file path; a
    /// graphics MODE then draws here instead of falling back to a headless text
    /// mode. This is the first slice of the graphics port (Phase 1): it renders
    /// the line primitives (MOVE/DRAW/PLOT) and the graphics colour. Text in a
    /// graphics mode, fills, circles and an interactive window come later.
    ///
    /// BBC graphics use a logical space of UnitsWidth x UnitsHeight (1280x1024),
    /// origin bottom-left with y increasing upward; the canvas transform flips y
    /// and the surface is that logical size, so primitives draw in logical
    /// coordinates directly.
    /// </summary>
    public class SkiaGraphicsScreenMode : AbstractScreenMode
    {
        private const int UnitsW = 1280;
        private const int UnitsH = 1024;

        private readonly SKSurface surface;
        private readonly SKCanvas canvas;
        private readonly float lineWidth;
        private readonly SKColor[] palette;
        private readonly SKTypeface typeface;
        private readonly float cellWidth;
        private readonly float cellHeight;
        private SKColor foreground;
        private SKColor textForeground;
        private bool written;

        public SkiaGraphicsScreenMode(VduSystem vdu, int textWidth, int textHeight, int pixelWidth, int pixelHeight, byte bitsPerPixel) :
            base(vdu, textWidth, textHeight, UnitsW, UnitsH, bitsPerPixel)
        {
            surface = SKSurface.Create(new SKImageInfo(UnitsW, UnitsH));
            canvas = surface.Canvas;
            canvas.Clear(SKColors.Black);
            // Logical (x, y) with y up -> surface pixels with y down.
            canvas.Translate(0, UnitsH);
            canvas.Scale(1, -1);

            // One mode pixel is this many logical units wide; draw lines about
            // that thick so they look like the mode's pixels.
            lineWidth = pixelWidth > 0 ? (float) UnitsW / pixelWidth : 4f;

            palette = DefaultPalette(LogicalColourCount);
            foreground = palette.Length > 0 ? palette[palette.Length - 1] : SKColors.White;
            textForeground = foreground;

            // Text is placed by character cell; render glyphs in a monospace
            // face sized to the cell.
            typeface = SKTypeface.FromFamilyName("monospace") ?? SKTypeface.Default;
            cellWidth = (float) UnitsW / textWidth;
            cellHeight = (float) UnitsH / textHeight;

            AppDomain.CurrentDomain.ProcessExit += (sender, e) => WritePng();
        }

        // --- line primitives (MOVE/DRAW/PLOT) ---------------------------------
        // Every line draws from the previous graphics cursor to the current one;
        // the VDU system has already updated both. The endpoint-inclusion and
        // dotted variants are drawn as a plain solid line for now.

        public override void SolidLineIncludingBothEndPoints() { DrawCursorLine(); }
        public override void SolidLineExcludingTheFinalPoint() { DrawCursorLine(); }
        public override void SolidLineExcludingtheInitialPoint() { DrawCursorLine(); }
        public override void SolidLineExcludingBothEndPoints() { DrawCursorLine(); }
        public override void DottedLineIncludingBothEndPointsPatternRestarted() { DrawCursorLine(); }
        public override void DottedLineExcludingtheFinalPointPatternRestarted() { DrawCursorLine(); }
        public override void DottedLineExcludingtheInitialPointPatternContinued() { DrawCursorLine(); }
        public override void DottedLineExcludingBothEndPointsPatternContinued() { DrawCursorLine(); }

        private void DrawCursorLine()
        {
            using var paint = new SKPaint
            {
                Color = foreground,
                StrokeWidth = lineWidth,
                IsStroke = true,
                IsAntialias = true,
                StrokeCap = SKStrokeCap.Round,
            };
            canvas.DrawLine(Vdu.OldGraphicsCursorX, Vdu.OldGraphicsCursorY,
                            Vdu.GraphicsCursorIX, Vdu.GraphicsCursorIY, paint);
        }

        public override void PointPlot()
        {
            using var paint = new SKPaint { Color = foreground, IsAntialias = true };
            canvas.DrawCircle(Vdu.GraphicsCursorIX, Vdu.GraphicsCursorIY, lineWidth / 2f, paint);
        }

        // --- colour -----------------------------------------------------------

        public override void UpdateGraphicsForegroundColour(int logicalColour, int tint)
        {
            foreground = ColourOf(logicalColour);
        }

        public override void UpdateGraphicsBackgroundColour(int logicalColour, int tint)
        {
            // Background colour is used by CLG / background plots, not yet drawn.
        }

        public override void UpdateTextForegroundColour(int logicalColour, int tint)
        {
            textForeground = ColourOf(logicalColour);
        }

        public override void UpdateTextBackgroundColour(int logicalColour, int tint) { }

        private SKColor ColourOf(int logicalColour)
        {
            if (palette.Length == 0)
            {
                return SKColors.White;
            }
            int index = ((logicalColour % palette.Length) + palette.Length) % palette.Length;
            return palette[index];
        }

        // --- text in a graphics mode ------------------------------------------

        public override void PrintCharAtText(char c)
        {
            // The VDU system has set the text cursor to this character's cell.
            // Text rows count from the top, but the canvas has y flipped for
            // graphics, so draw the glyph with the matrix reset (image space).
            float x = Vdu.TextCursorX * cellWidth;
            float topY = Vdu.TextCursorY * cellHeight;
            using var paint = new SKPaint
            {
                Color = textForeground,
                IsAntialias = true,
                Typeface = typeface,
                TextSize = cellHeight,
            };
            canvas.Save();
            canvas.ResetMatrix();
            // Baseline near the bottom of the cell (leave room for descenders).
            canvas.DrawText(c.ToString(), x, topY + cellHeight * 0.78f, paint);
            canvas.Restore();
        }

        public override void PrintCharAtGraphics(char c) { }
        public override void ScrollTextArea(int left, int bottom, int right, int top, Direction direction, ScrollMovement movement) { }

        // --- output -----------------------------------------------------------

        public override void Dispose()
        {
            WritePng();
            canvas.Dispose();
            surface.Dispose();
        }

        private void WritePng()
        {
            if (written)
            {
                return;
            }
            written = true;
            string path = Environment.GetEnvironmentVariable("OWL_CAPTURE_GRAPHICS");
            if (string.IsNullOrEmpty(path))
            {
                return;
            }
            using SKImage image = surface.Snapshot();
            using SKData png = image.Encode(SKEncodedImageFormat.Png, 100);
            using var stream = System.IO.File.OpenWrite(path);
            png.SaveTo(stream);
        }

        /// <summary>The BBC default logical-colour palette for a mode with the
        /// given number of logical colours (2, 4 or 16).</summary>
        private static SKColor[] DefaultPalette(int colours)
        {
            SKColor black = new SKColor(0, 0, 0);
            SKColor red = new SKColor(255, 0, 0);
            SKColor green = new SKColor(0, 255, 0);
            SKColor yellow = new SKColor(255, 255, 0);
            SKColor blue = new SKColor(0, 0, 255);
            SKColor magenta = new SKColor(255, 0, 255);
            SKColor cyan = new SKColor(0, 255, 255);
            SKColor white = new SKColor(255, 255, 255);
            if (colours <= 2)
            {
                return new[] { black, white };
            }
            if (colours <= 4)
            {
                return new[] { black, red, yellow, white };
            }
            // 16-colour: 0-7 steady, 8-15 are flashing pairs shown as the steady
            // colour for a still capture.
            return new[]
            {
                black, red, green, yellow, blue, magenta, cyan, white,
                black, red, green, yellow, blue, magenta, cyan, white,
            };
        }
    }
}
