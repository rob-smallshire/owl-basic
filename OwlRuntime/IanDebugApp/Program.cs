using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using OwlRuntime;
using OwlRuntime.platform.riscos;

namespace IanDebugApp
{
    class Program
    {
        static void Main(string[] args)
        {
            //VduSystemTest tst = new VduSystemTest();
            //tst.Test25();
            //tst.TestPalette();
            //tst.TestPaletteWheel();
            //tst.TestText();
            //tst.TestTextDirection();
            //tst.TestTextDirectionOverlap();

            // PRINT 42, 3.141, "Hello, World!"
            BasicCommands.Print(42);
            BasicCommands.CompleteField();
            BasicCommands.Print(3.141);
            BasicCommands.CompleteField();
            BasicCommands.Print("Hello, World!");
            BasicCommands.NewLine();
            // PRINT "Line 2"
            BasicCommands.Print("Line 2");
            BasicCommands.NewLine();
        }
    }
}
