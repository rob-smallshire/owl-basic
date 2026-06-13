using System.IO;
using SkiaSharp;
using Xunit;

namespace OwlRuntime.Tests
{
    // Confirms the SkiaSharp package and its native library load and render on
    // this platform/runtime: draw into an off-screen surface and encode a PNG.
    public class SkiaSmokeTests
    {
        [Fact]
        public void RendersAnOffScreenPngWithExpectedPixels()
        {
            using SKSurface surface = SKSurface.Create(new SKImageInfo(16, 16));
            SKCanvas canvas = surface.Canvas;
            canvas.Clear(SKColors.Black);
            using (var paint = new SKPaint { Color = SKColors.Red })
            {
                canvas.DrawRect(new SKRect(4, 4, 12, 12), paint);
            }

            using SKImage image = surface.Snapshot();

            // The drawn rectangle is red; a corner is the black background.
            using (SKBitmap bitmap = SKBitmap.FromImage(image))
            {
                Assert.Equal(SKColors.Red, bitmap.GetPixel(8, 8));
                Assert.Equal(SKColors.Black, bitmap.GetPixel(0, 0));
            }

            using SKData png = image.Encode(SKEncodedImageFormat.Png, 100);
            Assert.True(png.Size > 0);
            byte[] bytes = png.ToArray();
            // PNG signature.
            Assert.Equal(new byte[] { 0x89, 0x50, 0x4E, 0x47 }, bytes[0..4]);
        }
    }
}
