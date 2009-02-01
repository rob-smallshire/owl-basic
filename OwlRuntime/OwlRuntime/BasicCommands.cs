using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace OwlRuntime
{
    public static class BasicCommands
    {
        private static int channelCounter = 0;
        private static readonly Dictionary<int, FileStream> channels = new Dictionary<int, FileStream>();

        public class NoSuchChannelException : ApplicationException
        {
            private int channel;

            public NoSuchChannelException(string message, int channel) :
                base(message)
            {
                this.channel = channel;
            }
        }

        public static void Bput(int channel, byte value)
        {
            if (channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use BPUT with this channel", channel);
            }
            FileStream stream = channels[channel];
            stream.WriteByte(value);
        }
 
        public static int Bget(int channel)
        {
            if (channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use BPUT with this channel", channel);
            }
            FileStream stream = channels[channel];
            return stream.ReadByte();
        }

        public static void Close(int channel)
        {
            if (channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use BPUT with this channel", channel);
            }
            FileStream stream = channels[channel];
            stream.Dispose();
            channels.Remove(channel);
        }

        public static void Print(int channel, params object[] items)
        {
            if (channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use BPUT with this channel", channel);
            }
            FileStream stream = channels[channel];
            foreach (object item in items)
            {
                if (item is int)
                {
                    int i = (int) item;
                }
                else if (item is float)
                {
                    float f = (float) item;
                }
                else if (item is string)
                {
                    string s = (string) item;
                }
            }
        }

        public static long Ext(int channel)
        {
            if (channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use BPUT with this channel", channel);
            }
            FileStream stream = channels[channel];
            return stream.Length;
        }

        public static int Openin(string filename)
        {
            FileStream stream = new FileStream(filename, FileMode.Open, FileAccess.Read);
            int channel = ++channelCounter;
            channels[channel] = stream;
            return channel;
        }

        public static int Openout(string filename)
        {
            FileStream stream = new FileStream(filename, FileMode.Create, FileAccess.Write);
            int channel = ++channelCounter;
            channels[channel] = stream;
            return channel;
        }

        public static int Openup(string filename)
        {
            FileStream stream = new FileStream(filename, FileMode.Open, FileAccess.ReadWrite);
            int channel = ++channelCounter;
            channels[channel] = stream;
            return channel;
        }

        public static void SetPtr(int channel, long offset)
        {
            if (channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use BPUT with this channel", channel);
            }
            FileStream stream = channels[channel];
            stream.Seek(offset, SeekOrigin.Begin);
        }

        public static long GetPtr(int channel)
        {
            if (channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use BPUT with this channel", channel);
            }
            FileStream stream = channels[channel];
            return stream.Position;
        }

        public static object Eval(string expression)
        {
            throw new NotImplementedException();
        }

        public static int Inkey(int factor)
        {
            if (factor >= 0)
            {
                // Wait for keypress for factor milliseconds
            }
            else if (factor == -256)
            {
                
            }
            else if (factor < 0)
            {
                // Use GetAsyncKeyState to determine whether the requested key is down
            }

            // TODO: Return a number indicating the OS version
            return 100;
        }

        public static string InputString()
        {
            throw new NotImplementedException();
        }

        public static int InputInteger()
        {
            throw new NotImplementedException();
        }

        public static double InputFloat()
        {
            throw new NotImplementedException();
        }

        public static double Rnd(int n)
        {
            if (n < 0)
            {
                // Re-seed RNG with n
            }
            else if (n == 0)
            {
                // Return the same as the previous Rnd(1) call
            }
            else if (n == 1)
            {
                // Return double between 0.0 and 1.0
            }
            // TODO: Return an integer between [1, n]
            return n;
        }

        public static int Himem { get; set; }
        public static int Lomem { get; set; }
        public static int End { get; set; }
        public static int Page { get; set; }
        public static int Top { get; set; }

    }
}
