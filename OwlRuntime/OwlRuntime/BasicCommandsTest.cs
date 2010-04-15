using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using NUnit.Framework;

namespace OwlRuntime
{
    [TestFixture]
    public class BasicCommandsTest
    {
        [Test]
        public void PrintHelloWorld()
        {
            BasicCommands.Print(10.5);
            BasicCommands.CompleteField();
            BasicCommands.Print(42);
            BasicCommands.CompleteField();
            BasicCommands.Print("Hello, World!");
            BasicCommands.NewLine();
        }
    }
}
