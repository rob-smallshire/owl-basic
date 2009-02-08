using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    public abstract class BaseTextScreenMode : AbstractScreenMode
    {
        protected BaseTextScreenMode(VduSystem vdu, int textWidth, int textHeight) :
            base(vdu, textWidth, textHeight, 1280, 1024)
        {  
        }
    }
}
