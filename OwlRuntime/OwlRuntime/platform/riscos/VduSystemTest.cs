using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;
using NUnit.Framework;

namespace OwlRuntime.platform.riscos
{
    
    [TestFixture]
    public class VduSystemTest
    {
        private readonly VduSystem vdu = new VduSystem();

        [Test]
        public void Test18()
        {

            vdu.Enqueue((byte)18, (byte)0, (byte)135);  // GCOL action color
        }

        [Test]
        public void Test22()
        {
            // Change to mode 12
            vdu.Enqueue(7, 22, 12, 7);
        }

        [Test]
        public void Test25()
        {
            
            vdu.Enqueue((byte) 22, (byte) 28); // Change to mode 28
            vdu.Enqueue((byte) 25, (byte) 4);  // MOVE
            vdu.Enqueue((short) 320, (short) 240);
            vdu.Enqueue((byte) 25, (byte) 5);  // DRAW
            vdu.Enqueue((short) 640, (short) 480);
            Console.WriteLine("End");
        }

        [Test]
        public void TestRectangle()
        {

            vdu.Enqueue((byte)22, (byte)28); // Change to mode 28
            vdu.Enqueue((byte)18, (byte)0, (byte)135);  // GCOL action color
            vdu.Enqueue((byte)25, (byte)4);  // MOVE
            vdu.Enqueue((short)320, (short)240);
            vdu.Enqueue((byte)25, (byte)101);  // RECTANGLE FILL
            vdu.Enqueue((short)640, (short)480);
            Console.WriteLine("End");
        }

        [Test]
        public void TestPalette()
        {
            vdu.Enqueue(7);
            vdu.Enqueue((byte)22, (byte)28); // Change to mode 28
            int c = 0;
            for (int y = 0; y <= 255; y++)
            {
                for (int x = 0; x <= 255; x++)
                {   

                    // TINT action (2) color (c & 192)
                    vdu.Enqueue((byte)23, (byte)17, (byte)2, (byte)(c & 192));
                    vdu.Enqueue((byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0);
                    // GCOL action (0) color (c & 63)

                    vdu.Enqueue((byte)18, (byte)0, (byte)(c & 63));
                    // MOVE
                    vdu.Enqueue((byte)25, (byte)4);
                    vdu.Enqueue((short)(x*16), (short)(y * 16));
                    // PLOT rectangle fill
                    vdu.Enqueue((byte)25, (byte)101);
                    vdu.Enqueue((short)((x * 16) + 16), (short)((y * 16) + 16));
                    c++;
                } 
            }
            Console.WriteLine("End");
        }
        [Test]
        public void VduFormTest()
        {
            VduForm form = new VduForm(200, 200);
            form.Show();
            Graphics g = form.CreateGraphics();
            Pen pen = new Pen(Color.Red, 1); // TODO: Get current colour
            pen.DashStyle = System.Drawing.Drawing2D.DashStyle.Solid;
            g.DrawLine(pen, 0, 0, 200, 200);
            form.Refresh();
            form.Close();
        }
    }
}
