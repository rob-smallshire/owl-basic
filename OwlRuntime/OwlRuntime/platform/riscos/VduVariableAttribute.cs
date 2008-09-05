using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    internal class VduVariableAttribute: Attribute
    {
        private int number;

        public VduVariableAttribute(int number)
        {
            this.number = number;
        }
    }
}
