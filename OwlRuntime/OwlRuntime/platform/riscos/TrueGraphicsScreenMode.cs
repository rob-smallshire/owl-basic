using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

using System.Drawing;

namespace OwlRuntime.platform.riscos
{
    public class TrueGraphicsScreenMode : BaseGraphicsScreenMode
    {
        public TrueGraphicsScreenMode(VduSystem vdu, int textWidth, int textHeight, int squarePixelWidth, int squarePixelHeight) :
            base(vdu, textWidth, textHeight, squarePixelWidth, squarePixelHeight)
        {
        }

        protected override Color GraphicsForegroundColour()
        {
            throw new NotImplementedException();
        }
    }
}
