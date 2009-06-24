using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OwlRuntime.platform.riscos
{
    public class TeletextScreenMode : BaseTextScreenMode
    {
        public TeletextScreenMode(VduSystem vdu) :
            base(vdu, 40, 25, 4) // 4 bits per pixel in last argument for the colours in teletext (7+flashing)
        {
        }

        public override void Dispose()
        {
            // Do nothing
        }

        public override void UpdateTextBackgroundColour(int logicalColour, int tint)
        {
            // Do nothing
        }

        public override void UpdateTextForegroundColour(int logicalColour, int tint)
        {
            // Do nothing
        }
    }
}
