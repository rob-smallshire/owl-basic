using System;
using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;
using System.Drawing.Imaging;




namespace testPalette
{
    public partial class Form1 : Form
    {
        private Bitmap myBitmap; // Our Bitmap declaration
        private Bitmap indexedBitmap;


        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            // draw red circles on the 
            myBitmap = new Bitmap(ClientRectangle.Width, ClientRectangle.Height, PixelFormat.Format24bppRgb);
            indexedBitmap = new Bitmap(myBitmap.Width, myBitmap.Height, PixelFormat.Format8bppIndexed);

            // Set the palette
            ColorPalette pal = indexedBitmap.Palette;
            for (int i = 0; i < 128; i++)
            {
                pal.Entries[i] = Color.FromArgb(0, 255 - (i*2), 0);
                pal.Entries[255 - i] = Color.FromArgb(0, 255 - (i * 2), 0);
            }
            indexedBitmap.Palette = pal;
            
            //following dosnt change any data - unknown reason
            //indexedBitmap.Palette.Entries[0] = Color.FromArgb(0, 0, 0);
            
            //cleat the graphics object to logical colour 0
            Graphics graphicsObj = Graphics.FromImage(myBitmap);
            graphicsObj.Clear(Color.FromArgb(0, 0, 0));
            
            for (int i = 0; i <= 255; ++i)
            {
                Pen myPen = new Pen(Color.FromArgb(0, 0, i), 3);
                graphicsObj.DrawEllipse(myPen, new Rectangle(0 + i, 0 + i, 512-(2*i), 512-(2*i)));
            }
            graphicsObj.Dispose();

            IndexedFromBlueBitmap(myBitmap, indexedBitmap, 8);
        }

        private void Form1_Paint(object sender, PaintEventArgs e)
        {
            //data for the indexed bitmap
            e.Graphics.DrawImage(indexedBitmap, 0, 0);
        }

        static private void IndexedFromBlueBitmap(Bitmap sourceBitmap, Bitmap destBitmap, byte destBpp)
        {
            PixelFormat bppFormat;
            switch (destBpp)
            {
                case 1:
                    bppFormat = PixelFormat.Format1bppIndexed;
                    break;
                case 2:
                    //2bpp format is Not supported by DotNet
                    bppFormat = PixelFormat.Format4bppIndexed;
                    break;
                case 4:
                    bppFormat = PixelFormat.Format4bppIndexed;
                    break;
                case 8:
                    bppFormat = PixelFormat.Format8bppIndexed;
                    break;
                default:
                    // not sure if i need to impliment 16/24(32)
                    throw new ArgumentOutOfRangeException();
            }

            BitmapData indexedBitmapData = null;
            try
            {
                Debug.Assert(destBitmap.Height == sourceBitmap.Height);
                Debug.Assert(destBitmap.Width == sourceBitmap.Width);
                Rectangle rectangle = new Rectangle(0, 0, sourceBitmap.Width, sourceBitmap.Height);
                indexedBitmapData = destBitmap.LockBits(
                    rectangle,
                    ImageLockMode.ReadWrite, bppFormat);

                BitmapData sourceBitmapData = null;
                try
                {
                    // data for the orig bitmap
                    sourceBitmapData = sourceBitmap.LockBits(
                        rectangle,
                        ImageLockMode.ReadOnly, PixelFormat.Format24bppRgb);
                    // size of the source pixels in bytes
                    const int sourcePixelSize = 3;

                    for (int y = 0; y < sourceBitmapData.Height; ++y)
                    {
                        unsafe
                        {
                            byte* sourceRow = (byte*) sourceBitmapData.Scan0 + (y * sourceBitmapData.Stride);
                            byte* destRow = (byte*) indexedBitmapData.Scan0 + (y * indexedBitmapData.Stride);

                            for (int x = 0; x < sourceBitmapData.Width; ++x)
                            {
                                destRow[x] = sourceRow[x * sourcePixelSize];
                            }
                        }
                    }
                }
                finally
                {
                    sourceBitmap.UnlockBits(sourceBitmapData);      
                }
            }
            finally
            {
                destBitmap.UnlockBits(indexedBitmapData);
            }
        }

        private void timer1_Tick(object sender, EventArgs e)
        {
            // cycle the palette
            ColorPalette pal = indexedBitmap.Palette;
            Color tmp = pal.Entries[0];
            for (int i = 0; i < pal.Entries.Length-1; i++)
            {
                pal.Entries[i] = pal.Entries[i+1];
            }
            pal.Entries[pal.Entries.Length - 1] = tmp;
            indexedBitmap.Palette = pal;
            Invalidate();
        }
    }
}
