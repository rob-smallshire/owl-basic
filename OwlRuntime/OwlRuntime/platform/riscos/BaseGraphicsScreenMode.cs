﻿using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    public abstract class BaseGraphicsScreenMode : AbstractScreenMode
    {
        private readonly VduForm vduForm;
        private bool hasBeenDisposed = false;
        private readonly int pixelWidth;
        private readonly int pixelHeight;
        private Color physicalGraphicsForegroundColour;
        private Color physicalGraphicsBackgroundColour;
        private byte renderingQuality;

        protected BaseGraphicsScreenMode(VduSystem vdu, int textWidth, int textHeight, int pixelWidth, int pixelHeight, int unitsWidth, int unitsHeight) :
            base(vdu, textWidth, textHeight, unitsWidth, unitsHeight)
        {
            this.pixelWidth = pixelWidth;
            this.pixelHeight = pixelHeight;
            vduForm = new VduForm(SquarePixelWidth, SquarePixelHeight);
            vduForm.BackColor = Color.Black;
            vduForm.Show(); // TODO: Is this the best place for this?
        }

        public int PixelWidth
        {
            get { return pixelWidth; }
        }

        public int PixelHeight
        {
            get { return pixelHeight; }
        }

        public float PixelAspect
        {
            get
            {
                float widthRatio = UnitsWidth / (float) PixelWidth;
                float heightRatio = UnitsHeight / (float) PixelHeight;
                return widthRatio / heightRatio;
            }
        }

        public int SquarePixelWidth
        {
            get
            {
                if (PixelAspect < 1.0)
                {
                    // TODO dont think this will work with mode 2, 5 or 10
                    // PixelAspect will be 0 and should be 0.5
                    return PixelWidth;
                }

                return (int) (PixelWidth * PixelAspect);
            }
        }

        public int SquarePixelHeight
        {
            get
            {
                if (PixelAspect < 1.0)
                {
                    // TODO dont think this will work with mode 2, 5 or 10
                    // PixelAspect will be 0 and should be 0.5
                    return (int) (PixelHeight / PixelAspect);
                }
                return PixelHeight;
            }
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

        public byte RenderingQuality
        {
            get { return renderingQuality; }
            protected set { renderingQuality = value; }
        }

        // Refactoring for Paletted screen modes:
        // 1. Make the CreateGraphics method abstract in this class
        // 2. Override CreateGraphics in TrueGraphicsScreenMode with this original implementation
        // 3. Override CreateGraphics in PalettedGraphicsScreenMode with a new implementation
        //    that creates a Graphics object for a bitmap
        // 4. 
        protected Graphics CreateGraphics()
        {
            Graphics graphics = vduForm.CreateGraphics();

            // The transform from OWL BASIC units to Windows pixel coordinates
            graphics.ResetTransform();
            graphics.TranslateTransform(0.0f, SquarePixelHeight, MatrixOrder.Prepend);
            graphics.ScaleTransform( (SquarePixelWidth / (float)UnitsWidth), -(SquarePixelHeight / (float)UnitsHeight) , MatrixOrder.Prepend);

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
            using (Graphics g = CreateGraphics())
            {
                Pen pen = Pen();
                pen.DashStyle = System.Drawing.Drawing2D.DashStyle.Solid;
                int diffX = Vdu.GraphicsCursorIX - Vdu.OldGraphicsCursorX;
                int diffY = Vdu.GraphicsCursorIY - Vdu.OldGraphicsCursorY;
                int radius = (int)Math.Sqrt((diffX * diffX) + (diffY * diffY));
                g.DrawEllipse(pen, Vdu.OldGraphicsCursorX - radius,
                                     Vdu.OldGraphicsCursorY - radius, radius * 2, radius * 2);
            }

            // TODO needs testing

            // TODO: Temporary, so we can see something
            vduForm.Refresh();
        }

        public override void CircleFill()
        {
            using (Graphics g = CreateGraphics())
            {
                SolidBrush brush = SolidBrush();
                int diffX = Vdu.GraphicsCursorIX - Vdu.OldGraphicsCursorX;
                int diffY = Vdu.GraphicsCursorIY - Vdu.OldGraphicsCursorY;
                int radius = (int)Math.Sqrt((diffX * diffX) + (diffY * diffY));
                g.FillEllipse(brush, Vdu.OldGraphicsCursorX - radius,
                                     Vdu.OldGraphicsCursorY - radius, radius*2, radius*2);
            }

            // TODO: Temporary, so we can see something
            vduForm.Refresh();
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
            // Extract this next line into a virtual Refresh method in this class
            // override in the paletted class to do the conversion to physical colours
            vduForm.Refresh();
        }

        // 1. Make this protected abstract in this class
        // 2. Push this implementation down into an override in TrueGraphicsScreenMode
        // 3. Create a new override in PalettedGraphicsScreenMode which sets the pen to blue index colour
        private Pen Pen()
        {
            return new Pen(PhysicalGraphicsForegroundColour);
        }

        // 1. Make this protected abstract in this class
        // 2. Push this implementation down into an override in TrueGraphicsScreenMode
        // 3. Create a new override in PalettedGraphicsScreenMode which sets the pen to blue index colour
        /// <summary>
        /// Create a brush for painting solid shapes using the current logical
        /// colour settings in conjunction with any palette settings.
        /// </summary>
        /// <returns></returns>
        private SolidBrush SolidBrush()
        {
            return new SolidBrush(PhysicalGraphicsForegroundColour);
        }

        public override void UpdateRenderingQuality(byte quality)
        {
            RenderingQuality = quality;
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
