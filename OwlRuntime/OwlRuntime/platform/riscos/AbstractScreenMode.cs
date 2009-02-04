using System;
using System.Collections.Generic;
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

    public abstract class AbstractScreenMode
    {
        private int textWidth;
        private int textHeight;
        private int pixelWidth;
        private int pixelHeight;
        private int unitsWidth;
        private int unitsHeight;
        private byte bitsPerPixel;
        
        public static AbstractScreenMode CreateScreenMode(byte number)
        {

            
            AbstractScreenMode mode = null;

            switch (number & 127) // after reading prm only bottom 7 bits are used for setting mode (top bit is for shadow modes) PRM 1-597
            {
                case 0:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 80;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;
                case 1:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 40;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 320;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 2:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 20;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 160;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 3:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 80;
                    mode.TextHeight = 25;
                    break;

                case 4:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 40;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 320;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 5:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 20;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 160;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 6:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 40;
                    mode.TextHeight = 25;
                    break;

                case 7:
                    mode = new TeletextScreenMode();
                    mode.TextWidth = 40;
                    mode.TextHeight = 25;
                    break;

                case 8:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 80;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 9:
                    mode = new PalettedScreenMode(4); 
                    mode.TextWidth = 40;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 320;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 10:
                    mode = new PalettedScreenMode(8);
                    mode.TextWidth = 20;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 160;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 11:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 80;
                    mode.TextHeight = 25;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 250;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1000;
                    break;

                case 12:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 80;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 13:
                    mode = new PalettedScreenMode(8);
                    mode.TextWidth = 40;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 320;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 14:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 80;
                    mode.TextHeight = 25;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 250;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1000;
                    break;

                case 15:
                    mode = new PalettedScreenMode(8);
                    mode.TextWidth = 80;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 16:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 132;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 1056;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 2112;
                    mode.UnitsHeight = 1024;
                    break;

                case 17:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 132;
                    mode.TextHeight = 25;
                    mode.PixelWidth = 1056;
                    mode.PixelHeight = 250;
                    mode.UnitsWidth = 2112;
                    mode.UnitsHeight = 1000;
                    break;

                case 18:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 80;
                    mode.TextHeight = 64;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 512;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 19:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 80;
                    mode.TextHeight = 64;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 512;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 20:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 80;
                    mode.TextHeight = 64;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 512;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 21:
                    mode = new PalettedScreenMode(8);
                    mode.TextWidth = 80;
                    mode.TextHeight = 64;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 512;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1024;
                    break;

                case 22:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 96;
                    mode.TextHeight = 36;
                    mode.PixelWidth = 768;
                    mode.PixelHeight = 288;
                    mode.UnitsWidth = 768;
                    mode.UnitsHeight = 576;
                    break;

                case 23:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 144;
                    mode.TextHeight = 56;
                    mode.PixelWidth = 1152;
                    mode.PixelHeight = 896;
                    mode.UnitsWidth = 2304;
                    mode.UnitsHeight = 1792;
                    break;

                case 24:
                    mode = new PalettedScreenMode(8);
                    mode.TextWidth = 132;
                    mode.TextHeight = 32;
                    mode.PixelWidth = 1056;
                    mode.PixelHeight = 256;
                    mode.UnitsWidth = 2112;
                    mode.UnitsHeight = 1024;
                    break;

                case 25:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 80;
                    mode.TextHeight = 60;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 480;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 960;
                    break;

                case 26:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 80;
                    mode.TextHeight = 60;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 480;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 960;
                    break;

                case 27:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 80;
                    mode.TextHeight = 60;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 480;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 960;
                    break;

                case 28:
                    mode = new PalettedScreenMode(8);
                    mode.TextWidth = 80;
                    mode.TextHeight = 60;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 480;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 960;
                    break;

                case 29:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 100;
                    mode.TextHeight = 75;
                    mode.PixelWidth = 800;
                    mode.PixelHeight = 600;
                    mode.UnitsWidth = 1600;
                    mode.UnitsHeight = 1200;
                    break;

                case 30:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 100;
                    mode.TextHeight = 75;
                    mode.PixelWidth = 800;
                    mode.PixelHeight = 600;
                    mode.UnitsWidth = 1600;
                    mode.UnitsHeight = 1200;
                    break;

                case 31:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 100;
                    mode.TextHeight = 75;
                    mode.PixelWidth = 800;
                    mode.PixelHeight = 600;
                    mode.UnitsWidth = 1600;
                    mode.UnitsHeight = 1200;
                    break;

                case 33:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 96;
                    mode.TextHeight = 36;
                    mode.PixelWidth = 768;
                    mode.PixelHeight = 288;
                    mode.UnitsWidth = 1536;
                    mode.UnitsHeight = 1152;
                    break;

                case 34:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 96;
                    mode.TextHeight = 36;
                    mode.PixelWidth = 768;
                    mode.PixelHeight = 288;
                    mode.UnitsWidth = 1536;
                    mode.UnitsHeight = 1152;
                    break;

                case 35:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 96;
                    mode.TextHeight = 36;
                    mode.PixelWidth = 768;
                    mode.PixelHeight = 288;
                    mode.UnitsWidth = 1536;
                    mode.UnitsHeight = 1152;
                    break;

                case 36:
                    mode = new PalettedScreenMode(8);
                    mode.TextWidth = 96;
                    mode.TextHeight = 36;
                    mode.PixelWidth = 768;
                    mode.PixelHeight = 288;
                    mode.UnitsWidth = 1536;
                    mode.UnitsHeight = 1152;
                    break;

                case 37:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 112;
                    mode.TextHeight = 44;
                    mode.PixelWidth = 896;
                    mode.PixelHeight = 352;
                    mode.UnitsWidth = 1792;
                    mode.UnitsHeight = 1408;
                    break;

                case 38:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 112;
                    mode.TextHeight = 44;
                    mode.PixelWidth = 896;
                    mode.PixelHeight = 352;
                    mode.UnitsWidth = 1792;
                    mode.UnitsHeight = 1408;
                    break;

                case 39: 
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 112;
                    mode.TextHeight = 44;
                    mode.PixelWidth = 896;
                    mode.PixelHeight = 352;
                    mode.UnitsWidth = 1792;
                    mode.UnitsHeight = 1408;
                    break;

                case 40:
                    mode = new PalettedScreenMode(8);
                    mode.TextWidth = 112;
                    mode.TextHeight = 44;
                    mode.PixelWidth = 896;
                    mode.PixelHeight = 352;
                    mode.UnitsWidth = 1792;
                    mode.UnitsHeight = 1408;
                    break;

                case 41:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 80;
                    mode.TextHeight = 44;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 352;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1408;
                    break;

                case 42:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 80;
                    mode.TextHeight = 44;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 352;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1408;
                    break;

                case 43:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 80;
                    mode.TextHeight = 44;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 352;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 1408;
                    break;

                case 44:
                    mode = new PalettedScreenMode(1);
                    mode.TextWidth = 80;
                    mode.TextHeight = 25;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 200;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 800;
                    break;

                case 45:
                    mode = new PalettedScreenMode(2);
                    mode.TextWidth = 80;
                    mode.TextHeight = 25;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 200;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 800;
                    break;

                case 46:
                    mode = new PalettedScreenMode(4);
                    mode.TextWidth = 80;
                    mode.TextHeight = 25;
                    mode.PixelWidth = 640;
                    mode.PixelHeight = 200;
                    mode.UnitsWidth = 1280;
                    mode.UnitsHeight = 800;
                    break;

                default:
                    throw new NoSuchScreenModeException(number);
            }
            return mode;
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

        // TODO: Wrong design - Move this out of the base class
        public abstract System.Drawing.Color LogicalToPhysical(int logical);
    }
}
