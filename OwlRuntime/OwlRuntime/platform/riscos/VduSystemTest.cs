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
            Assert.AreEqual(7, vdu.LogicalGraphicsBackgroundColour);
        }

        [Test]
        public void Test22()
        {
            // Change to mode 12
            vdu.Enqueue(22, 12);
            Assert.AreEqual(12, vdu.ModeNumber);
        }

        [Test]
        public void Test25()
        {
            
            vdu.Enqueue((byte) 22, (byte) 22); // Change to mode 2
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
            const int size = 16;
            for (int y = 0; y < size; ++y)
            {
                for (int x = 0; x < size; ++x)
                {   
                    // TINT action (2) color (c & 192)
                    vdu.Enqueue((byte)23, (byte)17, (byte)2, (byte)(c & 192));
                    vdu.Enqueue((byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0);

                    // GCOL action (0) color (c & 63)
                    vdu.Enqueue((byte)18, (byte)0, (byte)(c & 63));

                    // MOVE
                    vdu.Enqueue((byte)25, (byte)4);
                    vdu.Enqueue((short)(x * size), (short)(y * size));

                    // PLOT rectangle fill
                    vdu.Enqueue((byte)25, (byte)101);
                    vdu.Enqueue((short)((x * size) + (size - 1)), (short)((y * size) + (size - 1)));

                    ++c;
                } 
            }
            Console.WriteLine("End");
        }



        [Test]
        public void TestPaletteWheel()
        {
            // 8bpp modes tested 10,13, 15, 28,21,24,36,40
            vdu.Enqueue((byte)22, (byte)28); // Change to mode 28
            const short size = 220;
            int radius = 250;

            for (int t = 1; t < 5; ++t)
            {
                radius -= 30;
                int c = 3;
                int cntr = 0;
                int colDiff = 0;

                for (int circle = 100; circle < 450; circle+=20)
                {
                    cntr++;

                    // TINT action (2) color (t * 64)
                    vdu.Enqueue((byte)23, (byte)17, (byte)2, (byte)((t-1) *64));
                    vdu.Enqueue((byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0);

                    // GCOL action (0) color (c & 63)
                    vdu.Enqueue((byte)18, (byte)0, (byte)(c & 63));


                    short mov1x = (short)(size + (Math.Cos((circle - 20) * (Math.PI / 180)) * radius));
                    short mov1y = (short)(size + (Math.Sin((circle - 20) * (Math.PI / 180)) * radius));
                    short mov2x = (short)(size + (Math.Cos((circle) * (Math.PI / 180)) * radius));
                    short mov2y = (short)(size + (Math.Sin((circle) * (Math.PI / 180)) * radius));

                    // MOVE
                    vdu.Enqueue((byte)25, (byte)4);
                    vdu.Enqueue(size, size);

                    // MOVE
                    vdu.Enqueue((byte)25, (byte)4);
                    vdu.Enqueue(mov1x, mov1y);

                    // PLOT triangle fill
                    vdu.Enqueue((byte)25, (byte)85);
                    vdu.Enqueue(mov2x, mov2y);

                    //GCOL 0,0
                    //vdu.Enqueue((byte)18, (byte)0, (byte)(0));

                    // plot black border
                    // MOVE
                    //vdu.Enqueue((byte)25, (byte)4);
                    //vdu.Enqueue(mov2x, mov2y);

                    // DRAW
                    //vdu.Enqueue((byte)25, (byte)5);
                    //vdu.Enqueue(mov1x, mov1y);


                    switch (cntr)
                    {
                        case 1:
                            colDiff = 4;
                            break;
                        case 4:
                            colDiff = -1;
                            break;
                        case 7:
                            colDiff = 16;
                            break;
                        case 10:
                            colDiff = -4;
                            break;
                        case 13:
                            colDiff = 1;
                            break;
                        case 16:
                            colDiff = -16;
                            break;
                    }
                    c += colDiff; // add the difference to the colour number
                }
            }

            // plot the circles in the centre
            radius -= 25;            

            for (int c = 0; c < 64; c += 21)
            {
                for (int t = 0; t < 255; t += 64)
                {
                    radius -= 5;
                    // TINT action (2) color (t * 64)
                    vdu.Enqueue((byte)23, (byte)17, (byte)2, (byte)t);
                    vdu.Enqueue((byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0);

                    // GCOL action (0) color (c & 63)
                    vdu.Enqueue((byte)18, (byte)0, (byte)(c));

                    // MOVE to centre
                    vdu.Enqueue((byte)25, (byte)4);
                    vdu.Enqueue(size, size);

                    // PLOT the circle
                    vdu.Enqueue((byte)25, (byte)157);
                    vdu.Enqueue((short)(size + radius), (short)size);
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
