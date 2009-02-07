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
        private int textWidth;
        private int textHeight;
        private int unitsWidth;
        private int unitsHeight;
        private byte bitsPerPixel;
        private Color physicalTextForgroundColour;
        private Color physicalTextBackgroundColour;

        private readonly VduSystem vdu;
        
        public static AbstractScreenMode CreateScreenMode(VduSystem vdu, byte number)
        {
            AbstractScreenMode mode = null;

            switch (number & 127) // after reading prm only bottom 7 bits are used for setting mode (top bit is for shadow modes) PRM 1-597
            {
                case 0:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 80, 32, 640, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;
                case 1:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 40, 32, 320, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 2:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 20, 32, 160, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 3:
                    mode = new PalettedTextScreenMode(vdu, 1, 80, 25);
                    break;

                case 4:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 40, 32, 320, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 5:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 20, 32, 160, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 6:
                    mode = new PalettedTextScreenMode(vdu, 1, 40, 25);
                    break;

                case 7:
                    mode = new TeletextScreenMode(vdu);
                    mode.TextWidth = 40;
                    mode.TextHeight = 25;
                    break;

                case 8:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 80, 32, 640, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 9:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 40, 32, 320, 256); 
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 10:
                    mode = new PalettedGraphicsScreenMode(vdu, 8, 20, 32, 160, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 11:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 80, 25, 640, 250);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1000;
                    break;

                case 12:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 80, 32, 640, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 13:
                    mode = new PalettedGraphicsScreenMode(vdu, 8, 40, 32, 320, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 14:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 80, 25, 640, 250);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1000;
                    break;

                case 15:
                    mode = new PalettedGraphicsScreenMode(vdu, 8, 80, 32, 640, 256);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 16:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 132, 32, 1056, 256);
                    mode.UnitsWidth = 2112;
                    mode.UnitsHeight = 1024;
                    break;

                case 17:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 132, 25, 1056, 250);
                    mode.UnitsWidth = 2112;
                    mode.UnitsHeight = 1000;
                    break;

                case 18:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 80, 64, 640, 512);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 19:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 80, 64, 640, 512);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 20:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 80, 64, 640, 512);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 21:
                    mode = new PalettedGraphicsScreenMode(vdu, 8, 80, 64, 640, 512);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 22:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 96, 36, 768, 288);
                    mode.UnitsWidth = 768;
                    mode.UnitsHeight = 576;
                    break;

                case 23:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 144, 56, 1152, 896);
                    mode.UnitsWidth = 2304;
                    mode.UnitsHeight = 1792;
                    break;

                case 24:
                    mode = new PalettedGraphicsScreenMode(vdu, 8, 132, 32, 1056, 256);
                    mode.UnitsWidth = 2112;
                    mode.UnitsHeight = 1024;
                    break;

                case 25:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 80, 60,640, 480);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 960;
                    break;

                case 26:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 80, 60, 640, 480);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 960;
                    break;

                case 27:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 80, 60, 640, 480);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 960;
                    break;

                case 28:
                    mode = new PalettedGraphicsScreenMode(vdu, 8, 80, 60, 640, 480);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 960;
                    break;

                case 29:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 100, 75, 800, 600);
                    mode.UnitsWidth = 1600;
                    mode.UnitsHeight = 1200;
                    break;

                case 30:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 100, 75, 800, 600);
                    mode.UnitsWidth = 1600;
                    mode.UnitsHeight = 1200;
                    break;

                case 31:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 100, 75, 800, 600);
                    mode.UnitsWidth = 1600;
                    mode.UnitsHeight = 1200;
                    break;

                case 33:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 96, 36, 768, 288);
                    mode.UnitsWidth = 1536;
                    mode.UnitsHeight = 1152;
                    break;

                case 34:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 96, 36, 768, 288);
                    mode.UnitsWidth = 1536;
                    mode.UnitsHeight = 1152;
                    break;

                case 35:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 96, 36, 768, 288);
                    mode.UnitsWidth = 1536;
                    mode.UnitsHeight = 1152;
                    break;

                case 36:
                    mode = new PalettedGraphicsScreenMode(vdu, 8, 96, 36, 768, 288);
                    mode.UnitsWidth = 1536;
                    mode.UnitsHeight = 1152;
                    break;

                case 37:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 112, 44, 896, 352);
                    mode.UnitsWidth = 1792;
                    mode.UnitsHeight = 1408;
                    break;

                case 38:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 112, 44, 896, 352);
                    mode.UnitsWidth = 1792;
                    mode.UnitsHeight = 1408;
                    break;

                case 39:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 112, 44, 896, 352);
                    mode.UnitsWidth = 1792;
                    mode.UnitsHeight = 1408;
                    break;

                case 40:
                    mode = new PalettedGraphicsScreenMode(vdu, 8, 112, 44, 896, 352);
                    mode.UnitsWidth = 1792;
                    mode.UnitsHeight = 1408;
                    break;

                case 41:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 80, 44, 640, 352);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1408;
                    break;

                case 42:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 80, 44, 640, 352);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1408;
                    break;

                case 43:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 80, 44, 640, 352);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1408;
                    break;

                case 44:
                    mode = new PalettedGraphicsScreenMode(vdu, 1, 80, 25, 640, 200);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 800;
                    break;

                case 45:
                    mode = new PalettedGraphicsScreenMode(vdu, 2, 80, 25, 640, 200);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 800;
                    break;

                case 46:
                    mode = new PalettedGraphicsScreenMode(vdu, 4, 80, 25, 640, 200);
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 800;
                    break;

                default:
                    throw new NoSuchScreenModeException(number);
            }
            return mode;
        }

        protected AbstractScreenMode(VduSystem vdu, int textWidth, int textHeight)
        {
            this.vdu = vdu;
            this.textWidth = textWidth;
            this.textHeight = textHeight;
        }

        public int TextWidth
        {
            get { return textWidth; }
            protected set { textWidth = value; }
        }

        public int TextHeight
        {
            get { return textHeight; }
            protected set { textHeight = value; }
        }

        public int UnitsWidth
        {
            get { return unitsWidth; }
            protected set { unitsWidth = value; }
        }

        public int UnitsHeight
        {
            get { return unitsHeight; }
            protected set { unitsHeight = value; }
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

        public Color PhysicalTextForgroundColour
        {
            get { return physicalTextForgroundColour; }
            protected set { physicalTextForgroundColour = value; }
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
    }
}
