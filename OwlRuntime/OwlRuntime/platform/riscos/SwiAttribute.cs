using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    internal class SwiAttribute :Attribute
    {
        private int number;

        public SwiAttribute(int number)
        {
            this.number = number;
        }
    }
}
