using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Drawing.Imaging;




namespace testPalette
{
    public partial class Form1 : Form
    {
        private System.Drawing.Bitmap myBitmap; // Our Bitmap declaration
        private System.Drawing.Bitmap indexedBitmap;


        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            // draw red circles on the 
            Graphics graphicsObj;
            myBitmap = new Bitmap(this.ClientRectangle.Width, this.ClientRectangle.Height, System.Drawing.Imaging.PixelFormat.Format24bppRgb);
            indexedBitmap = new Bitmap(myBitmap.Width, myBitmap.Height, System.Drawing.Imaging.PixelFormat.Format8bppIndexed);

            // Set the palette
            ColorPalette pal = indexedBitmap.Palette;
            for (int i = 0; i < 128; i++)
            {
                pal.Entries[i] = Color.FromArgb(255, 255 - (i*2), 0);
                pal.Entries[255 - i] = Color.FromArgb(255, 255 - (i * 2), 0);
            }
            indexedBitmap.Palette = pal;
            
            //following dosnt change any data - unknown reason
            //indexedBitmap.Palette.Entries[0] = Color.FromArgb(0, 0, 0);
            
            //cleat the graphics object to logical colour 0
            graphicsObj = Graphics.FromImage(myBitmap);
            graphicsObj.Clear(System.Drawing.Color.FromArgb(0, 0, 0));
            
            for (int i = 0; i <= 255; i++)
            {
                Pen myPen = new Pen(System.Drawing.Color.FromArgb(0, 0, i), 3);
                graphicsObj.DrawEllipse(myPen, new Rectangle(0 + i, 0 + i, 512-(2*i), 512-(2*i)));
            }
            graphicsObj.Dispose();

            indexedFromBlueBitmap(myBitmap, indexedBitmap);



        }



        private void Form1_Paint(object sender, PaintEventArgs e)
        {
            Graphics graphicsObj = e.Graphics;

             //data for the indexed bitmap

            e.Graphics.DrawImage(indexedBitmap, 0, 0);
        
        }

        unsafe private void indexedFromBlueBitmap(Bitmap sourceBitmap, Bitmap destBitmap)
        {
            BitmapData indexedBitmapData = destBitmap.LockBits(
                new Rectangle(0, 0, destBitmap.Width, destBitmap.Height), ImageLockMode.ReadWrite, PixelFormat.Format8bppIndexed);
            // data for the orig bitmap
            BitmapData sourceBitmapData = sourceBitmap.LockBits(
                new Rectangle(0, 0, sourceBitmap.Width, sourceBitmap.Height),
                ImageLockMode.ReadWrite, PixelFormat.Format24bppRgb);
            // size of the pixels in bytes
            int sourcePixelSize = 3;

            for (int y = 0; y < sourceBitmapData.Height; y++)
            {

                byte* sourceRow = (byte*)sourceBitmapData.Scan0 + (y * sourceBitmapData.Stride);
                byte* destRow = (byte*)indexedBitmapData.Scan0 + (y * indexedBitmapData.Stride);

                for (int x = 0; x < sourceBitmapData.Width; x++)
                {

                    destRow[x] = sourceRow[x * sourcePixelSize];

                }
            }

            destBitmap.UnlockBits(indexedBitmapData);
            sourceBitmap.UnlockBits(sourceBitmapData);
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
            this.Invalidate();
        }


    }
}
