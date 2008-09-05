using System;
using System.Collections.Generic;
using System.Drawing.Drawing2D;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    public class VduForm : Form
    {
        private readonly Bitmap bitmap;

        public VduForm(int width, int height)
        {
            ClientSize = new Size(width, height);
            bitmap = new Bitmap(ClientSize.Width, ClientSize.Height);
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
