using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OwlRuntime
{
    /// <summary>
    /// A memory map for backwards compatibility 
    /// </summary>
    public static class MemoryMap
    {
        private static readonly byte[] memory;

        static MemoryMap()
        {
            const int numBytes = 32 * 1024;
            memory = new byte[numBytes];
        }

        public static byte[] Memory
        {
            get { return memory; }
        }
    }
}
