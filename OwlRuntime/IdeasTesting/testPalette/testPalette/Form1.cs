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

            AcornFont testFont = new AcornFont();
            testFont.setBackgroundColour(Color.FromArgb(0,0,127));
            testFont.setForegroundColour(Color.FromArgb(0,0,255));


            myBitmap = new Bitmap(ClientRectangle.Width, ClientRectangle.Height, PixelFormat.Format24bppRgb);
            indexedBitmap = new Bitmap(myBitmap.Width, myBitmap.Height, PixelFormat.Format8bppIndexed);










            // Set the palette
            ColorPalette pal = indexedBitmap.Palette;
            for (int i = 0; i < 64; i++)
            {
                pal.Entries[i] = Color.FromArgb(0, 255 - (i*4), 0);
                pal.Entries[127 - i] = Color.FromArgb(0, 255 - (i * 4), 0);
            }
            for (int i = 0; i < 64; i++)
            {
                pal.Entries[128 + i] = Color.FromArgb(0, 255 - (i * 4), 0);
                pal.Entries[128 + (127 - i)] = Color.FromArgb(0, 255 - (i * 4), 0);
            }
            pal.Entries[255] = Color.FromArgb(255, 255 , 255);
            indexedBitmap.Palette = pal;
            
            //following dosnt change any data - unknown reason
            //indexedBitmap.Palette.Entries[0] = Color.FromArgb(0, 0, 0);
            
            //cleat the graphics object to logical colour 0
            Graphics graphicsObj = Graphics.FromImage(myBitmap);
            graphicsObj.Clear(Color.FromArgb(0, 0, 128));
            
            for (int i = 0; i <= 127; ++i)
            {
                Pen myPen = new Pen(Color.FromArgb(0, 0, i), 3);
                graphicsObj.DrawEllipse(myPen, new Rectangle(0 + i, 0 + i, 512-(2*i), 512-(2*i)));
            }
            // TextureBrush brush = new TextureBrush(acornAscii); // SolidBrush(Color.FromArgb(0, 0, 255));
            // graphicsObj.FillRectangle(brush, 256, 160, 8, 8);



            // print ascii A-Z
            for (int i = 65; i < 91; ++i)
            {
                graphicsObj.DrawImageUnscaled(testFont.getBitmap(i), ((i-64)*8), 100);
            }

            // print ascii A-Z
            testFont.setTransparentBackground(true);
            for (int i = 65+32; i < (91+32); ++i)
            {
                graphicsObj.DrawImageUnscaled(testFont.getBitmap(i), ((i - 96) * 8), 120);
            }

            // print ascii A-Z
            testFont.setTransparentBackground(false);
            for (int i = 48; i < 58; ++i)
            {
                graphicsObj.DrawImageUnscaled(testFont.getBitmap(i), ((i - 48) * 8), 140);
            }




            graphicsObj.Dispose();

            IndexedFromBlueBitmap(myBitmap, indexedBitmap, 8);
        }

        private void Form1_Paint(object sender, PaintEventArgs e)
        {
            //data for the indexed bitmap
            e.Graphics.DrawImageUnscaled (indexedBitmap, 0, 0);
        }

        static private void IndexedFromBlueBitmap(Bitmap sourceBitmap, Bitmap destBitmap, byte destBpp)
        {

            BitmapData indexedBitmapData = null;
            try
            {
                Debug.Assert(destBitmap.Height == sourceBitmap.Height);
                Debug.Assert(destBitmap.Width == sourceBitmap.Width);
                Rectangle rectangle = new Rectangle(0, 0, sourceBitmap.Width, sourceBitmap.Height);
                indexedBitmapData = destBitmap.LockBits(
                    rectangle,
                    ImageLockMode.ReadWrite, PixelFormat.Format8bppIndexed);

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
            for (int i = 0; i < (pal.Entries.Length/2)-1; i++)
            {
                pal.Entries[i] = pal.Entries[i+1];
            }
            pal.Entries[(pal.Entries.Length/2) - 1] = tmp;
            indexedBitmap.Palette = pal;
            Invalidate();
        }


    }
}
