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

        // Typed indirection access. ? (byte) is emitted inline against Memory;
        // these back the wider ! (4-byte integer), $ (CR-terminated string) and
        // | (float) indirection operators as both r-values and l-values.

        /// <summary>Read a 4-byte little-endian integer (<c>!addr</c>).</summary>
        public static int ReadInteger(int address)
        {
            return memory[address]
                 | (memory[address + 1] << 8)
                 | (memory[address + 2] << 16)
                 | (memory[address + 3] << 24);
        }

        /// <summary>Write a 4-byte little-endian integer (<c>!addr = v</c>).</summary>
        public static void WriteInteger(int address, int value)
        {
            memory[address] = (byte)value;
            memory[address + 1] = (byte)(value >> 8);
            memory[address + 2] = (byte)(value >> 16);
            memory[address + 3] = (byte)(value >> 24);
        }

        /// <summary>Read a CR-terminated string (<c>$addr</c>); bytes are Latin-1.</summary>
        public static string ReadString(int address)
        {
            int end = address;
            while (memory[end] != 0x0D)
            {
                end++;
            }
            var builder = new StringBuilder(end - address);
            for (int i = address; i < end; i++)
            {
                builder.Append((char)memory[i]);
            }
            return builder.ToString();
        }

        /// <summary>Write a string and its CR (&amp;0D) terminator (<c>$addr = s$</c>).</summary>
        public static void WriteString(int address, string value)
        {
            int i = address;
            foreach (char c in value)
            {
                memory[i++] = (byte)c;
            }
            memory[i] = 0x0D;
        }

        /// <summary>Read an 8-byte IEEE double (<c>|addr</c>, OWL's float width).</summary>
        public static double ReadFloat(int address)
        {
            return BitConverter.ToDouble(memory, address);
        }

        /// <summary>Write an 8-byte IEEE double (<c>|addr = v</c>).</summary>
        public static void WriteFloat(int address, double value)
        {
            byte[] bytes = BitConverter.GetBytes(value);
            Array.Copy(bytes, 0, memory, address, bytes.Length);
        }
    }
}
