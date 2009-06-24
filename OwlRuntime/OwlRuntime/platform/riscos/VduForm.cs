using System;
using System.Collections.Generic;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Drawing;
using System.Drawing.Imaging;

namespace OwlRuntime.platform.riscos
{
    public class VduForm : Form
    {
        // this needs to be a different format of bitmap depending on if the screenmode is paletted or not
        private readonly Bitmap bitmap;
        private readonly Bitmap indexedBitmap;

        public VduForm(int width, int height, PixelFormat pixelFormat)
        {
            ClientSize = new Size(width, height);
            bitmap = new Bitmap(ClientSize.Width, ClientSize.Height, pixelFormat);
        }

        public VduForm(int width, int height)
        {
            // TODO may need to remove this constructor
            // only left it in while testing for the palletted modes
            ClientSize = new Size(width, height);
            bitmap = new Bitmap(ClientSize.Width, ClientSize.Height, PixelFormat.Format24bppRgb);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = base.CreateGraphics(); 
            g.DrawImage(bitmap, 0, 0);
        }

        public new Graphics CreateGraphics()
        {
            return Graphics.FromImage(bitmap);
        }
    }
}
