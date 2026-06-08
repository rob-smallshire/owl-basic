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

        // Bump pointer for DIM byte-block allocation. Starts above low memory so
        // a block's base address looks like a pointer (and is non-zero), leaving
        // low addresses free for direct ?/! indirection.
        private const int HeapBase = 0x100;
        private static int free = HeapBase;

        static MemoryMap()
        {
            const int numBytes = 32 * 1024;
            memory = new byte[numBytes];
        }

        public static byte[] Memory
        {
            get { return memory; }
        }

        /// <summary>
        /// Reserve <paramref name="count"/> contiguous bytes (BBC <c>DIM b n</c>)
        /// and return the base address. Throws on a negative size or when the
        /// heap is exhausted.
        /// </summary>
        public static int Allocate(int count)
        {
            if (count < 0 || free + count > memory.Length)
            {
                throw new BadDimException(0);
            }
            int address = free;
            free += count;
            return address;
        }

        /// <summary>Reset the heap (used by RUN, which clears variables).</summary>
        public static void ResetHeap()
        {
            free = HeapBase;
        }
    }
}
