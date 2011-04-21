using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    public class OS
    {
        private readonly VduSystem vdu = new VduSystem();

        public OS(VduSystem vdu)
        {
            this.vdu = vdu;
        }

        [Swi(0x00)]
        public void WriteC(char c)
        {
            vdu.Write(c);
        }

        [Swi(0x01)]
        public void WriteS(string s)
        {
            vdu.Write(s);
        }
        
        [Swi(0x02)]
        public void Write0(string s)
        {
            vdu.Write(s);
        }
        
        [Swi(0x03)]
        public void NewLine()
        {
            vdu.NewLine();
        }
        
        [Swi(0x04)]
        public char ReadC()
        {
            // TODO: Move this into VduSystem and/or ScreenMode
            int i = Console.Read();
            char c = Convert.ToChar(i);
            return c;
        }
        
        [Swi(0x05)]
        public void CLI(string command)
        {
            throw new NotImplementedException();
        }
        
        [Swi(0x06)]
        public int Byte(int reason, out int r2)
        {
            throw new NotImplementedException();
        }
        
        [Swi(0x07)]
        public int Word(int reason, byte[] block)
        {
            throw new NotImplementedException();
        }
        
        [Swi(0x38)]
        public string SWINumberToString(int number)
        {
            throw new NotImplementedException();
        }
        
        [Swi(0x39)]
        public int SWINumberFromString(string name)
        {
            throw new NotImplementedException();
        }
    }
}
