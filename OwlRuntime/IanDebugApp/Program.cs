using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using OwlRuntime.platform.riscos;

namespace IanDebugApp
{
    class Program
    {
        static void Main(string[] args)
        {
            VduSystemTest tst = new VduSystemTest();
            //tst.Test25();
            //tst.TestPalette();
            //tst.TestPaletteWheel();
            //tst.TestText();
            tst.TestTextDirection();
        }
    }
}
