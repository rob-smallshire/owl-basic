using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using OwlRuntime.platform.riscos;

namespace OwlRuntime
{
    public static class BasicCommands
    {
        private static int channelCounter = 0;
        private static readonly Dictionary<int, FileStream> channels = new Dictionary<int, FileStream>();
        private static readonly VduSystem vdu = new VduSystem();
        private static readonly PrintManager printManager = new PrintManager();
        private const int owlTrue = -1;
        private const int owlFalse = 0;

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

        /// <summary>
        /// Get the next key pressed on the console.
        /// </summary>
        /// <returns>An integer Unicode value.</returns>
        public static int Get()
        {
            ConsoleKeyInfo cki = Console.ReadKey(true);
            int code = cki.KeyChar;
            return code;
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

        public static void Vdu(byte b)
        {
            vdu.Enqueue(b);
        }

        public static void VduFlush()
        {
            vdu.Enqueue(0, 0, 0, 0, 0, 0, 0, 0, 0);
        }

        public static void Cls()
        {
            vdu.Enqueue(12);
        }

        public static int Himem { get; set; }
        public static int Lomem { get; set; }
        public static int End { get; set; }
        public static int Page { get; set; }
        public static int Top { get; set; }

        public static void TabH(int x)
        {
            printManager.TabH(x);
        }

        public static void TabXY(int x, int y)
        {
            printManager.TabXY(x, y);
        }

        /// <summary>
        /// Set the printing system to hex format numbers
        /// </summary>
        public static void HexFormat()
        {
            printManager.HexFormat();
        }

        public static void DecFormat()
        {
            printManager.DecFormat();
        }

        /// <summary>
        /// Print a newline
        /// </summary>
        public static void NewLine()
        {
            printManager.NewLine();   
        }

        public static void DisableRightJustifyNumerics()
        {
            printManager.DisableRightJustifyNumerics();
        }

        public static void RightJustifyNumerics()
        {
            printManager.RightJustifyNumerics();
        }

        public static void CompleteField()
        {
            printManager.CompleteField();
        }

        public static void Spc(int padding)
        {
            printManager.Spc(padding);
        }

        public static void Print(string s)
        {
            printManager.Print(s);
        }

        public static void Print(int i)
        {
            printManager.Print(i);
        }

        public static void Print(double d)
        {
            printManager.Print(d);
        }

        public static void Print(object o)
        {
            printManager.Print(o);
        }

        // Operators
        /// <summary>
        /// Numeric addition of a value boxed in an object and an integer. The result type
        /// is double, since the object may contain a double. If the type object is non-numeric
        /// a TypeMismatch exception will be thrown.
        /// </summary>
        /// <param name="lhs">Left hand side: A boxed numeric value type</param>
        /// <param name="rhs">Right hand side: An integer</param>
        /// <returns>lhs plus rhs</returns>
        /// <exception cref="TypeMismatchException">Thrown if lhs does not contain a boxed numeric type</exception>
        public static double Add(object lhs, int rhs)
        {
            if (lhs is int)
            {
                return (int) lhs + rhs;
            }

            if (lhs is double)
            {
                return (double) lhs + rhs;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot add {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Numeric addition of a value boxed in an object and a double. The result type
        /// is double. If the type object is non-numeric
        /// a TypeMismatch exception will be thrown.
        /// </summary>
        /// <param name="lhs">Left hand side: A boxed numeric value type</param>
        /// <param name="rhs">Right hand side: An double</param>
        /// <returns>lhs plus rhs</returns>
        /// <exception cref="TypeMismatchException">Thrown if lhs does not contain a boxed numeric type</exception>
        public static double Add(object lhs, double rhs)
        {
            if (lhs is int)
            {
                return (int) lhs + rhs;
            }

            if (lhs is double)
            {
                return (double) lhs + rhs;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot add {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// String concatenation of a string value boxed in lhs and a string. The result
        /// type is string. If the boxed object is not a string a TypeMismatch exception will be thrown.
        /// </summary>
        /// <param name="lhs">Left hand side: A boxed string value</param>
        /// <param name="rhs">Right hand side: A string value</param>
        /// <returns></returns>
        public static string Concatenate(object lhs, string rhs)
        {
            if (lhs is string)
            {
                return (string) lhs + rhs;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot concatenate {0} and {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Add operation on two boxed value types.  If both boxed values are numeric, does addition.
        /// If both boxed values are strings, does concatenation. Otherwise, throws a TypeMismatchException.
        /// </summary>
        /// <param name="lhs">Left hand side: Boxed value type</param>
        /// <param name="rhs">Right hand side: Boxed value type</param>
        /// <returns>Boxed value type containing an integer, double or string depending on the type of the operands</returns>
        /// <exception cref="TypeMismatchException">Thrown if the arguments are a mixture of numeric and string types</exception>
        public static object Add(object lhs, object rhs)
        {
            if (lhs is int)
            {
                if (rhs is int)
                {
                    object result = (int) lhs + (int) rhs;
                    return result;
                }

                if (rhs is double)
                {
                    object result = (int) lhs + (double) rhs;
                    return result;
                }
            }

            if (lhs is double)
            {
                if (rhs is int)
                {
                    object result = (double) lhs + (int) rhs;
                    return result;
                }

                if (rhs is double)
                {
                    object result = (double) lhs + (double) rhs;
                    return result;
                }
            }

            if (lhs is string && rhs is string)
            {
                object result = (string) lhs + (string) rhs;
                return result;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot add {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int Equal(object lhs, object rhs)
        {
            if (ReferenceEquals(lhs, rhs))
            {
                return owlTrue;
            }
            if (lhs is int)
            {
                if (rhs is int)
                {
                    return (int) lhs == (int) rhs ? owlTrue : owlFalse;
                }
                if (rhs is double)
                {
                    return (int) lhs == (double) rhs ? owlTrue : owlFalse;
                }
            }
            else if (lhs is double)
            {
                if (rhs is int)
                {
                    return (double) lhs == (int) rhs ? owlTrue : owlFalse;
                }
                if (rhs is double)
                {
                    return (double) lhs == (double) rhs ? owlTrue : owlFalse;
                }
            }
            else if (lhs is string)
            {
                if (rhs is string)
                {
                    return (string) lhs == (string) rhs ? owlTrue : owlFalse;
                }
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }



        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int Equal(object lhs, int rhs)
        {
            if (lhs is int)
            {
                return (int) lhs == rhs ? owlTrue : owlFalse;
            }
            if (lhs is double)
            {
                return (double) lhs == rhs ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int Equal(object lhs, double rhs)
        {
            if (lhs is int)
            {
                return (int) lhs == rhs ? owlTrue : owlFalse;
            }
            if (lhs is double)
            {
                return (double) lhs == rhs ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int Equal(object lhs, string rhs)
        {
            if (lhs is string)
            {
                return String.Equals((string) lhs, rhs) ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int Equal(int lhs, object rhs)
        {
            if (rhs is int)
            {
                return lhs == (int) rhs ? owlTrue : owlFalse;
            }
            if (rhs is double)
            {
                return lhs == (double) rhs ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int Equal(double lhs, object rhs)
        {
            if (rhs is int)
            {
                return lhs == (int) rhs ? owlTrue : owlFalse;
            }
            if (rhs is double)
            {
                return lhs == (double) rhs ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int Equal(string lhs, object rhs)
        {
            if (rhs is string)
            {
                return String.Equals(lhs, (string) rhs) ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are not equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are not equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int NotEqual(object lhs, object rhs)
        {
            if (ReferenceEquals(lhs, rhs))
            {
                return owlTrue;
            }
            if (lhs is int)
            {
                if (rhs is int)
                {
                    return (int) lhs != (int) rhs ? owlTrue : owlFalse;
                }
                if (rhs is double)
                {
                    return (int) lhs != (double) rhs ? owlTrue : owlFalse;
                }
            }
            else if (lhs is double)
            {
                if (rhs is int)
                {
                    return (double) lhs != (int) rhs ? owlTrue : owlFalse;
                }
                if (rhs is double)
                {
                    return (double) lhs != (double) rhs ? owlTrue : owlFalse;
                }
            }
            else if (lhs is string)
            {
                if (rhs is string)
                {
                    return (string) lhs != (string) rhs ? owlTrue : owlFalse;
                }
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }



        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are not equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are not equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int NotEqual(object lhs, int rhs)
        {
            if (lhs is int)
            {
                return (int) lhs != rhs ? owlTrue : owlFalse;
            }
            if (lhs is double)
            {
                return (double) lhs != rhs ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are not equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are not equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int NotEqual(object lhs, double rhs)
        {
            if (lhs is int)
            {
                return (int) lhs != rhs ? owlTrue : owlFalse;
            }
            if (lhs is double)
            {
                return (double) lhs != rhs ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are not equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are not equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int NotEqual(object lhs, string rhs)
        {
            if (lhs is string)
            {
                return String.Equals((string) lhs, rhs) ? owlFalse : owlTrue;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are not equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are not equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int NotEqual(int lhs, object rhs)
        {
            if (rhs is int)
            {
                return lhs != (int) rhs ? owlTrue : owlFalse;
            }
            if (rhs is double)
            {
                return lhs != (double) rhs ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are not equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are not equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int NotEqual(double lhs, object rhs)
        {
            if (rhs is int)
            {
                return lhs != (int) rhs ? owlTrue : owlFalse;
            }
            if (rhs is double)
            {
                return lhs != (double) rhs ? owlTrue : owlFalse;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }

        /// <summary>
        /// Detmerine if the left hand side and right hand side operands are not equal
        /// </summary>
        /// <param name="lhs">The left hand side operand</param>
        /// <param name="rhs">The right hand side operand</param>
        /// <returns>True (-1) if the objects are not equal, otherwise False (0)</returns>
        /// <exception cref="TypeMismatchException">Thrown if the argument types are incompatible</exception>
        public static int NotEqual(string lhs, object rhs)
        {
            if (rhs is string)
            {
                return String.Equals(lhs, (string) rhs) ? owlFalse : owlTrue;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("Cannot compare {0} to {1}", lhs.GetType().FullName, rhs.GetType().FullName);
            throw new TypeMismatchException(sb.ToString());
        }
    }

    public class TypeMismatchException : Exception
    {
        public TypeMismatchException(string message) :
            base("Type mismatch: " + message)
        {
        }
    }
}
