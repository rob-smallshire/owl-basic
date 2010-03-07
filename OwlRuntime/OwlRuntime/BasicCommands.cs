using System;
using System.Collections;
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
        private static readonly VduSystem vdu;
        private static readonly OS os;
        private static readonly PrintManager printManager;
        private const int owlTrue = -1;
        private const int owlFalse = 0;

        static BasicCommands()
        {
            vdu = new VduSystem();
            os = new OS(vdu);
            printManager = new PrintManager(os, vdu);
        }

        public class NoSuchChannelException : ApplicationException
        {
            private int channel;

            public NoSuchChannelException(string message, int channel) :
                base(message)
            {
                this.channel = channel;
            }
        }

        public static int Asc(string s)
        {
            if (s.Length == 0)
            {
                return -1;    
            }
            return s[0];
        }

        public static string Chr(int i)
        {
            return new string((char) i, 1);
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

        public static int Instr(string searched, string substring)
        {
            return InstrAt(searched, substring, 1);
        }

        public static int InstrAt(string searched, string substring, int startIndex)
        {
            // Do converstion through unsigned int for startIndex
            if (substring.Length == 0)
            {
                return startIndex;
            }
            if (substring.Length > searched.Length)
            {
                return 0;
            }
            int index = searched.IndexOf(substring, startIndex - 1);
            return index + 1;
        }

        /// <summary>
        /// Function returning the left part of a string
        /// </summary>
        /// <param name="s">A string</param>
        /// <param name="length">The number of characters from the left of thge string that
        /// are to be returned.</param>
        /// <returns></returns>
        public static string LeftStr(string s, int length)
        {
            // The conversions through unsigned types are for behavioural compatibility
            // with BBC BASIC.
            int substringLength = (int) Math.Min((uint) length, (uint) s.Length);
            return s.Substring(0, substringLength);
        }

        /// <summary>
        /// Remove the rightmost character from the supplied string
        /// equivalent to LEFT$(s)
        /// </summary>
        /// <param name="s">A string</param>
        /// <returns></returns>
        public static string LeftStr(string s)
        {
            return s.Substring(0, Math.Max(s.Length - 1, 0));
        }

        /// <summary>
        /// Function returning a substring of a string.
        /// </summary>
        /// <param name="s">A string</param>
        /// <param name="startIndex">The one-based position within the string of the first
        /// character required.</param>
        /// <param name="length">The number of characters in the substring.</param>
        /// <returns></returns>
        public static string MidStr(string s, int startIndex, int length)
        {
            // The conversions through unsigned types are for behavioural compatibility
            // with BBC BASIC.
            int zeroBasedStartIndex = (int) (Math.Max((uint) startIndex, 1) - 1);
            if (zeroBasedStartIndex >= s.Length)
            {
                return "";
            }

            int substringLength = (int) Math.Min((uint) length, (uint) (s.Length - zeroBasedStartIndex));
            return s.Substring(zeroBasedStartIndex, substringLength);
        }

        public static string MidStr(string s, int startIndex)
        {
            // The conversions through unsigned types are for behavioural compatibility
            // with BBC BASIC.
            int zeroBasedStartIndex = (int) (Math.Max((uint) startIndex, 1) - 1);
            if (zeroBasedStartIndex >= s.Length)
            {
                return "";
            }

            int substringLength = s.Length - zeroBasedStartIndex;
            return s.Substring(zeroBasedStartIndex, substringLength);    
        }


        /// <summary>
        /// Function returning the rightmost 'length' characters of a string.
        /// </summary>
        /// <param name="s"></param>
        /// <param name="length"></param>
        /// <returns></returns>
        public static string RightStr(string s, int length)
        {
            // The conversions through unsigned types are for behavioural compatibility
            // with BBC BASIC.
            int substringLength = (int) Math.Min((uint) length, (uint) s.Length);
            int startIndex = s.Length - substringLength;
            return s.Substring(startIndex);            
        }

        /// <summary>
        /// Function returning the rightmost character of a string.
        /// </summary>
        /// <param name="s"></param>
        /// <returns></returns>
        public static string RightStr(string s)
        {
            int substringLength = Math.Min(1, s.Length);
            int startIndex = s.Length - substringLength;
            return s.Substring(startIndex, substringLength);
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
            printManager.ResetCount();
            vdu.Enqueue(12);
        }

        public static void Mode(int m)
        {
            vdu.Enqueue(22);
            vdu.Enqueue((byte) m);
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
        
        public static Queue<object> Input(bool prompt, params Type[] types)
        {
            Queue<string> strings = new Queue<string>();
            do
            {
                if (prompt)
                {
                    printManager.Print('?');
                }
                string line = Console.ReadLine();
                foreach (string field in line.Split(','))
                {
                    strings.Enqueue(field);
                }
                prompt = true;
            }
            while (strings.Count < types.Length);

            Queue<object> objects = new Queue<object>();
            foreach (Type type in types)
            {
                string field = strings.Dequeue();

                object obj = null;
                try
                {
                    obj = Convert.ChangeType(field.TrimStart(), type);
                }
                catch (Exception ex)
                {
                    if (ex is FormatException ||
                        ex is OverflowException)
                    {
                        obj = type.IsValueType ? Activator.CreateInstance(type) : null;
                    }
                    else
                    {
                        throw;
                    }
                }

                objects.Enqueue(obj);
            }
            return objects;
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

        public static int Pos()
        {
            return vdu.TextCursorX;
        }
    }

    public class OwlRuntimeException : Exception
    {
        public OwlRuntimeException(string message) :
            base("OwlRuntimeException: " + message)
        {
        }
    }

    public class TypeMismatchException :OwlRuntimeException
    {
        public TypeMismatchException(string message) :
            base("Type mismatch: " + message)
        {
        }
    }

    public class LongJumpException :OwlRuntimeException
    {
        public int TargetLogicalLine;
        public LongJumpException(int targetLogicalLine) :
            base("Longjump to line " + targetLogicalLine)
        {
            TargetLogicalLine = targetLogicalLine;
        }
    }

    /// <summary>
    /// Thrown when ON GOTO argument is out of range
    /// </summary>
    public class OnRangeException :OwlRuntimeException
    {
        public OnRangeException():
            base("On range")
        {
        }
    }

    /// <summary>
    /// Thrown when a program attempts to directly execute a
    /// procedure or function definition. Usually indicated a
    /// missing END statement.  
    /// </summary>
    public class ExecutedDefinitionException :OwlRuntimeException
    {
        public ExecutedDefinitionException(int logicalLineNumber) :
            base("Executed definition at line " + logicalLineNumber)
        {
        }
    }

    /// <summary>
    /// To be thrown by END statements. Caught by exception handlers
    /// in the Main program.
    /// </summary>
    public class EndException :OwlRuntimeException
    {
        public EndException(int logicalLineNumber) :
            base("END at line " + logicalLineNumber)
        {
        }
    }

    /// <summary>
    /// To be thrown by STOP statements. Caught by exception handlers
    /// in the Main program.
    /// </summary>
    public class StopException :OwlRuntimeException
    {
        public StopException(int logicalLineNumber) :
            base("STOP at line " + logicalLineNumber)
        {
        }
    }

    /// <summary>
    /// To be thrown by STOP statements. Caught by exception handlers
    /// in the Main program.
    /// </summary>
    public class QuitException :OwlRuntimeException
    {
        private readonly int returnCode;

        public QuitException(int returnCode, int logicalLineNumber) :
            base("STOP at line " + logicalLineNumber)
        {
            this.returnCode = returnCode;
        }

        public int ReturnCode
        {
            get { return returnCode; }
        }
    }
}
