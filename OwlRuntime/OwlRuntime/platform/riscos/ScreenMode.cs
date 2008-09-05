using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Drawing;

internal class ScreenMode
{
    public static ScreenMode CreateScreenMode(byte number)
    {
        return new ScreenMode(number);
    }

    private int textWidth;
    private int textHeight;
    private int pixelWidth;
    private int pixelHeight;
    private int unitsWidth;
    private int unitsHeight;
    private byte bitsPerPixel;

    private Color[] palette;

    // Create a ScreenMode from a mode number
    private ScreenMode(byte number)
    {
        switch (number)
        {
            case 0:
                TextWidth = 80;
                TextHeight = 32;
                PixelWidth = 640;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 1;
                break;

            case 1:
                TextWidth = 40;
                TextHeight = 32;
                PixelWidth = 320;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 2;
                break;

            case 2:
                TextWidth = 20;
                TextHeight = 32;
                PixelWidth = 160;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 4;
                break;

            case 3:
                TextWidth = 80;
                TextHeight = 25;
                BitsPerPixel = 1;
                break;

            case 4:
                TextWidth = 40;
                TextHeight = 32;
                PixelWidth = 320;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 1;
                break;

            case 5:
                TextWidth = 20;
                TextHeight = 32;
                PixelWidth = 160;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 2;
                break;

            case 6:
                TextWidth = 40;
                TextHeight = 25;
                BitsPerPixel = 1;
                break;

            case 7:
                TextWidth = 40;
                TextHeight = 25;
                BitsPerPixel = 4;
                break;

            case 8:
                TextWidth = 80;
                TextHeight = 32;
                PixelWidth = 640;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 2;
                break;

            case 9:
                TextWidth = 40;
                TextHeight = 32;
                PixelWidth = 320;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 4;
                break;

            case 10:
                TextWidth = 20;
                TextHeight = 32;
                PixelWidth = 160;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 8;
                break;

            case 11:
                TextWidth = 80;
                TextHeight = 25;
                PixelWidth = 640;
                PixelHeight = 250;
                UnitsWidth = 1280;
                UnitsHeight = 1000;
                BitsPerPixel = 2;
                break;

            case 12:
                TextWidth = 80;
                TextHeight = 32;
                PixelWidth = 640;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 4;
                break;

            case 13:
                TextWidth = 40;
                TextHeight = 32;
                PixelWidth = 320;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 8;
                break;

            case 14:
                TextWidth = 80;
                TextHeight = 25;
                PixelWidth = 640;
                PixelHeight = 250;
                UnitsWidth = 1280;
                UnitsHeight = 1000;
                BitsPerPixel = 4;
                break;

            case 15:
                TextWidth = 80;
                TextHeight = 32;
                PixelWidth = 640;
                PixelHeight = 256;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 8;
                break;

            case 16:
                TextWidth = 132;
                TextHeight = 32;
                PixelWidth = 1056;
                PixelHeight = 256;
                UnitsWidth = 2112;
                UnitsHeight = 1024;
                BitsPerPixel = 4;
                break;

            case 17:
                TextWidth = 132;
                TextHeight = 25;
                PixelWidth = 1056;
                PixelHeight = 250;
                UnitsWidth = 2112;
                UnitsHeight = 1000;
                BitsPerPixel = 4;
                break;

            case 18:
                TextWidth = 80;
                TextHeight = 64;
                PixelWidth = 640;
                PixelHeight = 512;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 1;
                break;

            case 19:
                TextWidth = 80;
                TextHeight = 64;
                PixelWidth = 640;
                PixelHeight = 512;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 2;
                break;

            case 20:
                TextWidth = 80;
                TextHeight = 64;
                PixelWidth = 640;
                PixelHeight = 512;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 4;
                break;

            case 21:
                TextWidth = 80;
                TextHeight = 64;
                PixelWidth = 640;
                PixelHeight = 512;
                UnitsWidth = 1280;
                UnitsHeight = 1024;
                BitsPerPixel = 8;
                break;

            case 22:
                TextWidth = 96;
                TextHeight = 36;
                PixelWidth = 768;
                PixelHeight = 288;
                UnitsWidth = 768;
                UnitsHeight = 576;
                BitsPerPixel = 4;
                break;

            case 23:
                TextWidth = 144;
                TextHeight = 56;
                PixelWidth = 1152;
                PixelHeight = 896;
                UnitsWidth = 2304;
                UnitsHeight = 1792;
                BitsPerPixel = 1;
                break;

            case 24:
                TextWidth = 132;
                TextHeight = 32;
                PixelWidth = 1056;
                PixelHeight = 256;
                UnitsWidth = 2112;
                UnitsHeight = 1024;
                BitsPerPixel = 8;
                break;

            case 25:
                TextWidth = 80;
                TextHeight = 60;
                PixelWidth = 640;
                PixelHeight = 480;
                UnitsWidth = 1280;
                UnitsHeight = 960;
                BitsPerPixel = 1;
                break;

            case 26:
                TextWidth = 80;
                TextHeight = 60;
                PixelWidth = 640;
                PixelHeight = 480;
                UnitsWidth = 1280;
                UnitsHeight = 960;
                BitsPerPixel = 2;
                break;

            case 27:
                TextWidth = 80;
                TextHeight = 60;
                PixelWidth = 640;
                PixelHeight = 480;
                UnitsWidth = 1280;
                UnitsHeight = 960;
                BitsPerPixel = 4;
                break;

            case 28:
                TextWidth = 80;
                TextHeight = 60;
                PixelWidth = 640;
                PixelHeight = 480;
                UnitsWidth = 1280;
                UnitsHeight = 960;
                BitsPerPixel = 8;
                break;

            case 29:
                TextWidth = 100;
                TextHeight = 75;
                PixelWidth = 800;
                PixelHeight = 600;
                UnitsWidth = 1600;
                UnitsHeight = 1200;
                BitsPerPixel = 1;
                break;

            case 30:
                TextWidth = 100;
                TextHeight = 75;
                PixelWidth = 800;
                PixelHeight = 600;
                UnitsWidth = 1600;
                UnitsHeight = 1200;
                BitsPerPixel = 2;
                break;

            case 31:
                TextWidth = 100;
                TextHeight = 75;
                PixelWidth = 800;
                PixelHeight = 600;
                UnitsWidth = 1600;
                UnitsHeight = 1200;
                BitsPerPixel = 4;
                break;

            case 33:
                TextWidth = 96;
                TextHeight = 36;
                PixelWidth = 768;
                PixelHeight = 288;
                UnitsWidth = 1536;
                UnitsHeight = 1152;
                BitsPerPixel = 1;
                break;

            case 34:
                TextWidth = 96;
                TextHeight = 36;
                PixelWidth = 768;
                PixelHeight = 288;
                UnitsWidth = 1536;
                UnitsHeight = 1152;
                BitsPerPixel = 2;
                break;

            case 35:
                TextWidth = 96;
                TextHeight = 36;
                PixelWidth = 768;
                PixelHeight = 288;
                UnitsWidth = 1536;
                UnitsHeight = 1152;
                BitsPerPixel = 4;
                break;

            case 36:
                TextWidth = 96;
                TextHeight = 36;
                PixelWidth = 768;
                PixelHeight = 288;
                UnitsWidth = 1536;
                UnitsHeight = 1152;
                BitsPerPixel = 8;
                break;

            case 37:
                TextWidth = 112;
                TextHeight = 44;
                PixelWidth = 896;
                PixelHeight = 352;
                UnitsWidth = 1792;
                UnitsHeight = 1408;
                BitsPerPixel = 1;
                break;

            case 38:
                TextWidth = 112;
                TextHeight = 44;
                PixelWidth = 896;
                PixelHeight = 352;
                UnitsWidth = 1792;
                UnitsHeight = 1408;
                BitsPerPixel = 2;
                break;

            case 39:
                TextWidth = 112;
                TextHeight = 44;
                PixelWidth = 896;
                PixelHeight = 352;
                UnitsWidth = 1792;
                UnitsHeight = 1408;
                BitsPerPixel = 4;
                break;

            case 40:
                TextWidth = 112;
                TextHeight = 44;
                PixelWidth = 896;
                PixelHeight = 352;
                UnitsWidth = 1792;
                UnitsHeight = 1408;
                BitsPerPixel = 8;
                break;

            case 41:
                TextWidth = 80;
                TextHeight = 44;
                PixelWidth = 640;
                PixelHeight = 352;
                UnitsWidth = 1280;
                UnitsHeight = 1408;
                BitsPerPixel = 1;
                break;

            case 42:
                TextWidth = 80;
                TextHeight = 44;
                PixelWidth = 640;
                PixelHeight = 352;
                UnitsWidth = 1280;
                UnitsHeight = 1408;
                BitsPerPixel = 2;
                break;

            case 43:
                TextWidth = 80;
                TextHeight = 44;
                PixelWidth = 640;
                PixelHeight = 352;
                UnitsWidth = 1280;
                UnitsHeight = 1408;
                BitsPerPixel = 4;
                break;

            case 44:
                TextWidth = 80;
                TextHeight = 25;
                PixelWidth = 640;
                PixelHeight = 200;
                UnitsWidth = 1280;
                UnitsHeight = 800;
                BitsPerPixel = 1;
                break;

            case 45:
                TextWidth = 80;
                TextHeight = 25;
                PixelWidth = 640;
                PixelHeight = 200;
                UnitsWidth = 1280;
                UnitsHeight = 800;
                BitsPerPixel = 2;
                break;

            case 46:
                TextWidth = 80;
                TextHeight = 25;
                PixelWidth = 640;
                PixelHeight = 200;
                UnitsWidth = 1280;
                UnitsHeight = 800;
                BitsPerPixel = 4;
                break;
        }

        palette = new Color[1 << BitsPerPixel];
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

    public int LogicalColours
    {
        get { return 1 << bitsPerPixel; }
    }

    public byte BitsPerPixel
    {
        get { return bitsPerPixel; }
        protected set { bitsPerPixel = value; }
    }

    public Color PalettePhysical(int colour)
    {
        if (bitsPerPixel <= 8)
        {
            
        }
        // else convert to int to RGBA bytes
        return Color.FromArgb(colour);
    }
}
