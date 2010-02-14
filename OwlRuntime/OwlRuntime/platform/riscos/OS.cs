using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    public static class OS
    {
        private static VduSystem vdu;

        [Swi(0x00)]
        public static void WriteC(char c)
        {
            vdu.Enqueue(c);
        }

        [Swi(0x01)]
        public static void WriteS(string s)
        {
            vdu.Enqueue(s);
        }
        
        [Swi(0x02)]
        public static void Write0(string s)
        {
            vdu.Enqueue(s);
        }
        
        [Swi(0x03)]
        public static void NewLine()
        {
            vdu.Enqueue((byte)10);
            vdu.Enqueue((byte)13);
        }
        
        [Swi(0x04)]
        public static char ReadC()
        {
            int i = Console.Read();
            char c = Convert.ToChar(i);
            return c;
        }
        
        [Swi(0x05)]
        public static void CLI(string command)
        {
            throw new NotImplementedException();
        }
        
        [Swi(0x06)]
        public static int Byte(int reason, out int r2)
        {
            throw new NotImplementedException();
        }
        
        [Swi(0x07)]
        public static int Word(int reason, byte[] block)
        {
            throw new NotImplementedException();
        }
        
        [Swi(0x38)]
        public static string SWINumberToString(int number)
        {
            throw new NotImplementedException();
        }
        
        [Swi(0x39)]
        public static int SWINumberFromString(string name)
        {
            throw new NotImplementedException();
        }
    }
}
