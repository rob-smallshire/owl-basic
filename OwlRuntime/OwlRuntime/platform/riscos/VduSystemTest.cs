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

        public void plot(byte code, short x, short y)
        {
            // move the graphics cursor to x,y)
            vdu.Enqueue((byte)25, (byte)code);  // MOVE
            vdu.Enqueue((short)x, (short)y);
        }

        public void move(short x, short y)
        {
            // move the graphics cursor to x,y)
            vdu.Enqueue((byte)25, (byte)4);  // MOVE
            vdu.Enqueue((short)x, (short)y);
        }

        public void textColourFG(byte colour, byte tint)
        {
            vdu.Enqueue((byte)23);
            vdu.Enqueue((byte)17);
            vdu.Enqueue((byte)0);
            vdu.Enqueue((byte)tint);
            vduflush();
            //23,17,0,tint
            // 17,col
            vdu.Enqueue((byte)17);
            vdu.Enqueue((byte)(colour & 127));


        }

        public void textColourBG(byte colour, byte tint)
        {
            //23,17,1,tint
            vdu.Enqueue((byte)23);
            vdu.Enqueue((byte)17);
            vdu.Enqueue((byte)1);
            vdu.Enqueue((byte)tint);
            vduflush();
            // 17,col
            vdu.Enqueue((byte)17);
            vdu.Enqueue((byte)((colour & 127) | 128));
 
        }

        public void vduflush()
        {
            for (int i = 0; i < 10; ++i)
            {
                vdu.Enqueue((byte)0);
            }
        }

        [Test]
        public void TestText()
        {
            vdu.Enqueue((byte)22, (byte)28); // Change to mode 28

            // TODO need to draw a rectangle to calibrate the text plotting position
            move(100, 100);   // MOVE
            move(0, 100);   // MOVE
            plot(85, 100, 0);   // triangle

            // need some good tests for changing the cursor print direction (vdu 23,16,x,y)
            vdu.Enqueue("test");
            Console.WriteLine("End");
            textColourFG(0, 0); // should be black
            textColourBG(63, 192); // should be white
            vdu.Enqueue((byte)65);
            vdu.Enqueue((byte)66);
            vdu.Enqueue((byte)67);
            vdu.Enqueue((byte)68);
            vdu.Enqueue((byte)69);
            vdu.Enqueue((byte)70);
            vdu.Enqueue((byte)71);
            vdu.Enqueue((byte)72);
            vdu.Enqueue((byte)73);
            vdu.Enqueue((byte)74);
            vdu.Enqueue((byte)169);
            Console.WriteLine("End");
            vdu.Enqueue((byte)23, (byte)17, (byte)5); // swap text foreground and background colours
            vduflush(); // flush the vdu queue with 0's
            vdu.Enqueue((byte)31, (byte) 10, (byte) 10); // move text cursor to 10,10
            vdu.Enqueue((byte)132); // plot the risc os x FOR WINDOWS
            vdu.Enqueue((byte)8); // plot backspace (non destructive)
            vdu.Enqueue((byte)8);
            vdu.Enqueue((byte)136); // left arrow
            vdu.Enqueue((byte)9);   // move cursor right one
            vdu.Enqueue((byte)137); // right arrow
            vdu.Enqueue((byte)8); // plot backspace (non destructive)
            vdu.Enqueue((byte)8);
            vdu.Enqueue((byte)10); // line feed
            vdu.Enqueue((byte)138);
            vdu.Enqueue((byte)8); // plot backspace (non destructive)
            vdu.Enqueue((byte)11); // cursor up
            vdu.Enqueue((byte)11); 
            vdu.Enqueue((byte)139);

            move(100, 100);   // MOVE

            vdu.Enqueue((byte)5); // plot at graphics cursor

            vdu.Enqueue((byte)23);// reprogram char (c) symbol
            vdu.Enqueue((byte)169);
            vdu.Enqueue((byte)129);
            vdu.Enqueue((byte)66);
            vdu.Enqueue((byte)36);
            vdu.Enqueue((byte)24);
            vdu.Enqueue((byte)24);
            vdu.Enqueue((byte)60);
            vdu.Enqueue((byte)126);
            vdu.Enqueue((byte)255);
            vdu.Enqueue((byte)169); // should be reprogrammed (c) to look like X with bottom triabgle filled in
            // todo test 23,17,7
            move(200, 400);   // MOVE
            vdu.Enqueue((byte)23, (byte)17, (byte)7, (byte)6);
            vdu.Enqueue((short)128, (short)128);
            vduflush(); // flush the vdu queue with 0's
            vdu.Enqueue((byte)169); // should be reporgrammed (c) to look like X
            vdu.Enqueue((byte)4); // plot at text cursor 
            vdu.Enqueue((byte)169); // should be reporgrammed (c) to look like X in the top right corner of the arrows
            Console.WriteLine("End");
        }

        [Test]
        public void TestTextDirection()
        {
            vdu.Enqueue((byte)22, (byte)28); // Change to mode 3

            vdu.Enqueue((byte)28); // define text window
            vdu.Enqueue((short)10, (short)25);
            vdu.Enqueue((short)40, (short)5);

            vdu.Enqueue((byte)23, (byte)16, (byte)12, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)30);
            vdu.Enqueue("*up");
            vdu.Enqueue((byte)10);
            vdu.Enqueue("right");


            vdu.Enqueue((byte)23, (byte)16, (byte)14, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)30);
            vdu.Enqueue("*up");
            vdu.Enqueue((byte)10);
            vdu.Enqueue("left");


            vdu.Enqueue((byte)23, (byte)16, (byte)8, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)30);
            vdu.Enqueue("*down");
            vdu.Enqueue((byte)10);
            vdu.Enqueue("right");


            vdu.Enqueue((byte)23, (byte)16, (byte)10, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)30);
            vdu.Enqueue("*down");
            vdu.Enqueue((byte)10);
            vdu.Enqueue("left");


            vdu.Enqueue((byte)23, (byte)16, (byte)2, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)30);
            vdu.Enqueue("*left");
            vdu.Enqueue((byte)10);
            vdu.Enqueue("down");


            vdu.Enqueue((byte)23, (byte)16, (byte)6, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)30);
            vdu.Enqueue("*left");
            vdu.Enqueue((byte)10);
            vdu.Enqueue("up");


            vdu.Enqueue((byte)23, (byte)16, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)30);
            vdu.Enqueue("*right");
            vdu.Enqueue((byte)10);
            vdu.Enqueue("down");

            vdu.Enqueue((byte)23, (byte)16, (byte)4, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)0, (byte)30);
            vdu.Enqueue("*right");
            vdu.Enqueue((byte)10);
            vdu.Enqueue("up");
            
            Console.WriteLine("End");
        }

        [Test]
        public void TestPalette()
        {
            vdu.Enqueue(7);
            vdu.Enqueue((byte)22, (byte)28); // Change to mode 28
            int c = 0;
            const int size = 32;
            for (int y = 0; y < 16; ++y)
            {
                for (int x = 0; x < 16; ++x)
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
                    vdu.Enqueue((short)((x * size) + (size - 2)), (short)((y * size) + (size - 2)));

                    ++c;
                } 
            }
            Console.WriteLine("End");
        }



        [Test]
        public void TestPaletteWheel()
        {
            // 8bpp modes tested 10,13,15,21,24,28,36,40
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
        public void ModeSizeTest0()
        {
            vdu.Enqueue((byte) 22, (byte) 0);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(640, mode.SquarePixelWidth);
            Assert.AreEqual(512, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest1()
        {
            vdu.Enqueue((byte) 22, (byte) 1);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(320, mode.SquarePixelWidth);
            Assert.AreEqual(256, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest2()
        {
            vdu.Enqueue((byte) 22, (byte) 2);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(320, mode.SquarePixelWidth);
            Assert.AreEqual(256, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest16()
        {
            vdu.Enqueue((byte) 22, (byte) 16);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(1056, mode.SquarePixelWidth);
            Assert.AreEqual(512, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest17()
        {
            vdu.Enqueue((byte) 22, (byte) 17);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(1056, mode.SquarePixelWidth);
            Assert.AreEqual(500, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest23()
        {
            vdu.Enqueue((byte) 22, (byte) 23);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(1152, mode.SquarePixelWidth);
            Assert.AreEqual(896, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest24()
        {
            vdu.Enqueue((byte) 22, (byte) 24);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(1056, mode.SquarePixelWidth);
            Assert.AreEqual(512, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest44()
        {
            vdu.Enqueue((byte) 22, (byte) 44);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(640, mode.SquarePixelWidth);
            Assert.AreEqual(400, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest22()
        {
            vdu.Enqueue((byte) 22, (byte) 22);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(768, mode.SquarePixelWidth);
            Assert.AreEqual(576, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest45()
        {
            vdu.Enqueue((byte) 22, (byte) 45);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(640, mode.SquarePixelWidth);
            Assert.AreEqual(400, mode.SquarePixelHeight);
        }

        [Test]
        public void ModeSizeTest46()
        {
            vdu.Enqueue((byte) 22, (byte) 46);
            BaseGraphicsScreenMode mode = (BaseGraphicsScreenMode) vdu.ScreenMode;
            Assert.AreEqual(640, mode.SquarePixelWidth);
            Assert.AreEqual(400, mode.SquarePixelHeight);
        }
    }
}
