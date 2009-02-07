using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    public abstract class BaseGraphicsScreenMode : AbstractScreenMode
    {
        private readonly VduForm vduForm;
        private bool hasBeenDisposed = false;
        private int pixelWidth;
        private int pixelHeight;
        private Color physicalGraphicsForegroundColour;
        private Color physicalGraphicsBackgroundColour;

        protected BaseGraphicsScreenMode(VduSystem vdu, int textWidth, int textHeight, int squarePixelWidth, int squarePixelHeight) :
            base(vdu, textWidth, textHeight)
        {
            vduForm = new VduForm(squarePixelWidth, squarePixelHeight);
            vduForm.Show(); // TODO: Is this the best place for this?
        }

        public int PixelWidth
        {
            get { return pixelWidth; }
            protected set { pixelWidth = value; }
        }

        public int PixelHeight
        {
            get { return pixelHeight; }
            protected set { pixelHeight = value; }
        }

        public int PixelAspect
        {
            get { return (UnitsHeight / PixelHeight) / (UnitsWidth / PixelWidth); }
        }

        public int SquarePixelWidth
        {
            get { return PixelWidth; }
        }

        public int SquarePixelHeight
        {
            get { return PixelHeight * PixelAspect; }
        }

        public Color PhysicalGraphicsForegroundColour
        {
            get { return physicalGraphicsForegroundColour; }
            protected set { physicalGraphicsForegroundColour = value; }
        }

        public Color PhysicalGraphicsBackgroundColour
        {
            get { return physicalGraphicsBackgroundColour; }
            protected set { physicalGraphicsBackgroundColour = value; }
        }

        protected Graphics CreateGraphics()
        {
            return vduForm.CreateGraphics();
        }

        /// <summary>
        /// Draw a filled rectangle using the current graphics coordinates.
        /// </summary>
        public override void RectangleFill()
        {
            using (Graphics g = CreateGraphics())
            {
                SolidBrush brush = SolidBrush();
                g.FillRectangle(brush, Vdu.OldGraphicsCursorX, Vdu.OldGraphicsCursorY,
                                Vdu.GraphicsCursorIX - Vdu.OldGraphicsCursorX,
                                Vdu.GraphicsCursorIY - Vdu.OldGraphicsCursorY);
            }

            // TODO: Temporary, so we can see something
            vduForm.Refresh();
        }

        public override void DottedLineIncludingBothEndPointsPatternRestarted()
        {
            throw new NotImplementedException();
        }

        public override void DottedLineExcludingtheFinalPointPatternRestarted()
        {
            throw new NotImplementedException();
        }

        public override void SolidLineExcludingtheInitialPoint()
        {
            throw new NotImplementedException();
        }

        public override void SolidLineExcludingBothEndPoints()
        {
            throw new NotImplementedException();
        }

        public override void DottedLineExcludingtheInitialPointPatternContinued()
        {
            throw new NotImplementedException();
        }

        public override void DottedLineExcludingBothEndPointsPatternContinued()
        {
            throw new NotImplementedException();
        }

        public override void HorizontalLineFillLeftRightToNonBackground()
        {
            throw new NotImplementedException();
        }

        public override void PointPlot()
        {
            using (Graphics g = CreateGraphics())
            {
                Pen pen = Pen();
                pen.DashStyle = System.Drawing.Drawing2D.DashStyle.Solid;
                // cant find a method to plot just a point in system.drawing    
                g.DrawLine(pen, Vdu.GraphicsCursorIX, Vdu.GraphicsCursorIY, Vdu.GraphicsCursorIX, Vdu.GraphicsCursorIY);
            }

            // TODO: Temporary, so we can see something
            vduForm.Refresh();
        }

        public override void TriangleFill()
        {
            using (Graphics g = CreateGraphics())
            {
                SolidBrush brush = SolidBrush();
                Point[] points = {new Point(Vdu.OlderGraphicsCursorX, Vdu.OlderGraphicsCursorY),
                                  new Point(Vdu.OldGraphicsCursorX, Vdu.OldGraphicsCursorY),
                                  new Point(Vdu.GraphicsCursorIX, Vdu.GraphicsCursorIY)};
                g.FillPolygon(brush, points);
            }

            // TODO: Temporary, so we can see something
            vduForm.Refresh();
        }

        public override void HorizontalLineFillRightToBackground()
        {
            throw new NotImplementedException();
        }

        public override void HorizontalLineFillLeftToForeground()
        {
            throw new NotImplementedException();
        }

        public override void ParallelogramFill()
        {
            throw new NotImplementedException();
        }

        public override void HorizontalLineFillRightOnlyToNonForeground()
        {
            throw new NotImplementedException();
        }

        public override void FloodToNonBackground()
        {
            throw new NotImplementedException();
        }

        public override void FloodToForeground()
        {
            throw new NotImplementedException();
        }

        public override void CircleOutline()
        {
            throw new NotImplementedException();
        }

        public override void CircleFill()
        {
            throw new NotImplementedException();
        }

        public override void CircularArc()
        {
            throw new NotImplementedException();
        }

        public override void Segment()
        {
            throw new NotImplementedException();
        }

        public override void Sector()
        {
            throw new NotImplementedException();
        }

        public override void RelativeRectangleMove()
        {
            throw new NotImplementedException();
        }

        public override void RelativeRectangleCopy()
        {
            throw new NotImplementedException();
        }

        public override void SpritePlot()
        {
            throw new NotImplementedException();
        }

        public override void FontPrinting()
        {
            throw new NotImplementedException();
        }

        public override void EllipseFill()
        {
            throw new NotImplementedException();
        }

        public override void EllipseOutline()
        {
            throw new NotImplementedException();
        }

        public override void AbsoluteRectangleCopy()
        {
            throw new NotImplementedException();
        }

        public override void AbsoluteRectangleMove()
        {
            throw new NotImplementedException();
        }

        public override void SolidLineExcludingTheFinalPoint()
        {
            throw new NotImplementedException();
        }

        public override void SolidLineIncludingBothEndPoints()
        {
            using (Graphics g = CreateGraphics())
            {
                Pen pen = Pen();
                pen.DashStyle = System.Drawing.Drawing2D.DashStyle.Solid; // TODO: Get current dash style
                g.DrawLine(pen, Vdu.OldGraphicsCursorX, Vdu.OldGraphicsCursorY, Vdu.GraphicsCursorIX, Vdu.GraphicsCursorIY);
            }

            // TODO: Temporary, so we can see something
            vduForm.Refresh();
        }

        private Pen Pen()
        {
            return new Pen(PhysicalGraphicsForegroundColour);
        }

        /// <summary>
        /// Create a brush for painting solid shapes using the current logical
        /// colour settings in conjunction with any palette settings.
        /// </summary>
        /// <returns></returns>
        private SolidBrush SolidBrush()
        {
            return new SolidBrush(PhysicalGraphicsForegroundColour);
        }

        public override void Dispose()
        {
            Dispose(true);
        }

        protected virtual void Dispose(bool disposeManagedObjs)
        {
            if (!hasBeenDisposed)
            {
                try
                {
                    if (disposeManagedObjs)
                    {
                        vduForm.Dispose();
                    }
                    GC.SuppressFinalize(this);
                }
                catch (Exception)
                {
                    hasBeenDisposed = false;
                    throw;
                }

                hasBeenDisposed = true;
            }
        }

        ~BaseGraphicsScreenMode()
        {
            Dispose();
        }
    }
}
