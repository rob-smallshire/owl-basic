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
        private readonly BaseGraphicsScreenMode screenMode;

        public VduForm(BaseGraphicsScreenMode screenMode)
        {
            this.screenMode = screenMode;
            ClientSize = new Size(screenMode.SquarePixelWidth, screenMode.SquarePixelHeight);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = CreateGraphics();
            screenMode.PaintBitmap(g);

        }
    }
}
