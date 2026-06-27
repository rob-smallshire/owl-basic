using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Reflection;
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

        // ON ERROR state, set by RecordError on a caught error and read by
        // ERR/ERL/REPORT$/REPORT.
        public static int errorLine = 0;
        public static int errorNumber = 0;
        public static string errorMessage = "";

        /// <summary>Record a caught runtime error for ERR/ERL/REPORT.</summary>
        public static void RecordError(Exception ex)
        {
            // ERL (the line of the error) is not tracked yet: tracking it per
            // line would cost on every line run, so it is left 0 for now. See
            // docs/on-error-erl.md for the planned zero-hot-path-cost approach.
            errorLine = 0;
            if (ex is OwlRuntimeException oe)
            {
                errorNumber = oe.ErrorNumber;
                errorMessage = oe.ReportMessage;
            }
            else if (ex is DivideByZeroException)
            {
                errorNumber = 18;            // BBC "Division by zero"
                errorMessage = "Division by zero";
            }
            else
            {
                errorNumber = 0;
                errorMessage = ex.Message;
            }
        }
        private const string acornDateTimeFormat = "ddd,dd MMM yyyy.HH:mm:ss";
        private const string bb4WDateTimeFormat = "ddd.dd MMM yyyy,HH:mm:ss";
        // BBC BASIC's RND is a 33-bit linear-feedback shift register using the
        // primitive trinomial (33,20,0). This is a clean-room reimplementation of
        // the behaviour of the BASIC II ROM: a 32-bit value (the seed bytes the
        // ROM keeps at &0D-&10) plus a one-bit overflow (the 33rd bit, &11 bit 0).
        // Each RND call advances the register 32 steps; the feedback bit is
        // bit 19 XOR bit 32. The power-on ("cold") seed is the bytes "ARW", and
        // because nothing re-seeds it, a program's "random" sequence is identical
        // on every run from a cold start -- just as on a real machine.
        private const uint coldRandomSeed = 0x00575241; // 'A','R','W' at &0D,&0E,&0F
        private static uint randomSeed;
        private static int randomOverflow;
        private static int time;
        private static int ticksAtTime;

        static BasicCommands()
        {
            vdu = new VduSystem();
            os = new OS(vdu);
            printManager = new PrintManager(os, vdu);

            ticksAtTime = Environment.TickCount;
            time = ticksAtTime / 10;

            // Start from the BBC cold seed (deterministic, matching a real
            // machine). OWL_RANDOM_SEED overrides it for testing, exactly as a
            // RND(-n) reseed would: it sets the 32-bit state and clears overflow.
            randomSeed = coldRandomSeed;
            randomOverflow = 0;
            string seedText = Environment.GetEnvironmentVariable("OWL_RANDOM_SEED");
            int seedValue;
            if (!string.IsNullOrEmpty(seedText) && Int32.TryParse(seedText, out seedValue))
            {
                randomSeed = (uint) seedValue;
            }
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

        public static double Val(string s)
        {
            // BBC VAL: the value of the leading numeric part of the string, or 0
            // if it does not begin with a number. It scans the same numeric
            // literal grammar the rest of BBC BASIC uses -- leading spaces, an
            // optional sign, digits, an optional decimal point, and an optional
            // E exponent -- so VAL, STR$ and the expression parser all agree
            // (e.g. VAL("1E3") = 1000, VAL("1.2E10") = 1.2E10).
            int i = 0;
            int n = s.Length;
            while (i < n && s[i] == ' ')
            {
                i++;
            }
            int start = i;
            if (i < n && (s[i] == '+' || s[i] == '-'))
            {
                i++;
            }
            bool sawDigit = false;
            while (i < n && char.IsDigit(s[i]))
            {
                i++;
                sawDigit = true;
            }
            if (i < n && s[i] == '.')
            {
                i++;
                while (i < n && char.IsDigit(s[i]))
                {
                    i++;
                    sawDigit = true;
                }
            }
            // An E exponent extends the mantissa, but only when it is well-formed
            // (an optional sign and at least one digit) and a mantissa preceded
            // it; otherwise the E is not part of the number and ends it.
            if (sawDigit && i < n && s[i] == 'E')
            {
                int j = i + 1;
                if (j < n && (s[j] == '+' || s[j] == '-'))
                {
                    j++;
                }
                if (j < n && char.IsDigit(s[j]))
                {
                    i = j;
                    while (i < n && char.IsDigit(s[i]))
                    {
                        i++;
                    }
                }
            }
            string number = s.Substring(start, i - start);
            double result;
            if (double.TryParse(number, NumberStyles.Float, CultureInfo.InvariantCulture, out result))
            {
                if (double.IsInfinity(result))
                {
                    // The literal overflows the float range, e.g. VAL("1E999"):
                    // BBC raises "Too big" rather than yielding an infinity.
                    throw new NumberTooBigException();
                }
                return result;
            }
            return 0.0;
        }

        // BBC BASIC V shift operators << >> >>>. Unlike CIL's shl/shr (which mask
        // the count modulo the operand width), BASIC V follows the ARM barrel
        // shifter: a count outside [0, width-1] shifts every bit out, so << and
        // >>> give 0 and >> (arithmetic) gives the sign fill (-1 or 0). A negative
        // count is out of range the same way. >> is the signed/arithmetic shift,
        // >>> the unsigned/logical one. (No BBC BASIC V disassembly to verify
        // against; these match the emulator's observed results.)

        public static int ShiftLeft(int value, int count)
        {
            if (count < 0 || count >= 32)
            {
                return 0;
            }
            return value << count;
        }

        public static long ShiftLeft(long value, int count)
        {
            if (count < 0 || count >= 64)
            {
                return 0;
            }
            return value << count;
        }

        public static int ShiftRight(int value, int count)
        {
            if (count < 0 || count >= 32)
            {
                return value < 0 ? -1 : 0;       // arithmetic: fill with the sign bit
            }
            return value >> count;
        }

        public static long ShiftRight(long value, int count)
        {
            if (count < 0 || count >= 64)
            {
                return value < 0 ? -1L : 0L;
            }
            return value >> count;
        }

        public static int ShiftRightUnsigned(int value, int count)
        {
            if (count < 0 || count >= 32)
            {
                return 0;
            }
            return (int)((uint) value >> count);    // logical: fill with zero
        }

        public static long ShiftRightUnsigned(long value, int count)
        {
            if (count < 0 || count >= 64)
            {
                return 0;
            }
            return (long)((ulong) value >> count);
        }

        public static long EvalHex(string s)
        {
            // The BBC hex-to-integer idiom EVAL("&" + h$) -- VAL is decimal-only,
            // so this is the only way to read a hex string. The '&' must be
            // followed by at least one hex digit, else "Bad hex"; the maximal run
            // of [0-9A-F] (uppercase only, like the ROM) is read and any trailing
            // characters are ignored (EVAL("&FG") = &F = 15). The digits fold into
            // a signed cell as a bit pattern with no overflow check -- 32-bit for
            // up to 8 digits (so "FFFFFFFF" is -1), 64-bit beyond -- exactly as the
            // hex-literal lexer does, so runtime and constant hex agree.
            int n = s.Length;
            int digits = 0;
            ulong raw = 0;
            while (digits < n)
            {
                char c = s[digits];
                int value;
                if (c >= '0' && c <= '9')
                {
                    value = c - '0';
                }
                else if (c >= 'A' && c <= 'F')   // uppercase only, like the ROM
                {
                    value = c - 'A' + 10;
                }
                else
                {
                    break;
                }
                raw = (raw << 4) | (ulong)value;   // wraps past 64 bits
                digits++;
            }
            if (digits == 0)
            {
                throw new BadHexException();
            }
            if (digits <= 8)
            {
                return (int)(uint)raw;       // 32-bit pattern, sign-extended
            }
            return unchecked((long)raw);     // 64-bit pattern as a signed value
        }

        public static string StrString(double n)
        {
            // BBC STR$: the string a number would PRINT as (the inverse of VAL).
            return printManager.NumberToString(n);
        }

        public static string StringString(int count, string s)
        {
            // BBC STRING$(count, s$): s$ repeated count times (empty if count <= 0).
            if (count <= 0 || s.Length == 0)
            {
                return string.Empty;
            }
            var sb = new StringBuilder(s.Length * count);
            for (int i = 0; i < count; ++i)
            {
                sb.Append(s);
            }
            return sb.ToString();
        }

        /// <summary>
        /// The @% print-format control word: the 4-byte BBC packing of STR$
        /// switch, G/E/F format, precision and field width. Driving PRINT, STR$.
        /// </summary>
        public static int AtPercent
        {
            get { return printManager.FormatNumber; }
            set { printManager.FormatNumber = value; }
        }

        /// <summary>
        /// The printf-style string form of @% in later BBC BASIC, e.g.
        /// @%="G10.5" or @%="+F2.4".
        /// </summary>
        public static void SetAtPercentFormat(string format)
        {
            printManager.FormatString = format;
        }

        /// <summary>
        /// The initial value of a resident integer for this run, read from the
        /// OWL_BASIC_RESIDENT_&lt;name&gt; environment variable (0 if unset or
        /// unparseable). BBC BASIC preserves the resident integers @% and A%-Z%
        /// across RUN and CHAIN; OWL seeds them from the environment once at
        /// process start so a CHAINing program can hand values to the program it
        /// launches. <paramref name="name"/> is a single letter "A".."Z".
        /// </summary>
        public static int SeedResident(string name)
        {
            string text = Environment.GetEnvironmentVariable("OWL_BASIC_RESIDENT_" + name);
            int value;
            if (!string.IsNullOrEmpty(text) && Int32.TryParse(text, out value))
            {
                return value;
            }
            return 0;
        }

        /// <summary>
        /// Seed @% (the print-format control word) from OWL_BASIC_RESIDENT_AT,
        /// the same channel as the A%-Z% resident integers. Unlike those, @% has
        /// a non-zero default format, so an absent variable must leave it alone
        /// rather than zeroing it.
        /// </summary>
        public static void SeedAtPercent()
        {
            string text = Environment.GetEnvironmentVariable("OWL_BASIC_RESIDENT_AT");
            int value;
            if (!string.IsNullOrEmpty(text) && Int32.TryParse(text, out value))
            {
                AtPercent = value;
            }
        }

        /// <summary>
        /// Stage one resident integer's current value into the environment, so a
        /// program launched by CHAIN inherits it (the partner of SeedResident).
        /// </summary>
        public static void StageResident(string name, int value)
        {
            Environment.SetEnvironmentVariable(
                "OWL_BASIC_RESIDENT_" + name,
                value.ToString(CultureInfo.InvariantCulture));
        }

        /// <summary>
        /// CHAIN: load and run another program, replacing this one. The resident
        /// integers A%-Z% have already been staged into the environment by the
        /// caller; @% is staged here. The BBC program name is resolved to a .NET
        /// assembly beside this one and launched as a fresh process that inherits
        /// our environment (and so the residents) and standard streams. CHAIN
        /// never returns: we exit with the chained program's status.
        /// </summary>
        public static void Chain(string filename)
        {
            StageResident("AT", AtPercent);

            string artifact = ResolveChainTarget(filename);
            var startInfo = new ProcessStartInfo
            {
                FileName = "dotnet",
                UseShellExecute = false,
            };
            startInfo.ArgumentList.Add(artifact);
            using (Process child = Process.Start(startInfo))
            {
                child.WaitForExit();
                Environment.Exit(child.ExitCode);
            }
        }

        /// <summary>
        /// Map a BBC BASIC program name to the .NET artifact CHAIN should launch:
        /// the &lt;name&gt;.dll beside the chaining assembly. This is the .NET
        /// target's notion of "the right thing"; another target resolves its own
        /// way.
        /// </summary>
        private static string ResolveChainTarget(string name)
        {
            string leaf = name.EndsWith(".dll", StringComparison.OrdinalIgnoreCase)
                ? name : name + ".dll";
            string directory = Path.GetDirectoryName(Assembly.GetEntryAssembly().Location);
            return Path.Combine(directory ?? string.Empty, leaf);
        }

        // OSCLI / a star command: hand the command line to the host OS command
        // interpreter. BBC BASIC's `*HELP`, `*FX n,m`, ... all arrive here (with
        // the leading '*' already stripped) as the text after the star. There is
        // no RISC OS underneath, so commands that are not modelled are ignored
        // rather than failing the program; specific commands can be recognised
        // here as the runtime grows.
        public static void Oscli(string command)
        {
            if (command == null)
            {
                return;
            }
            command = command.Trim();
            // Unmodelled OS commands (e.g. *HELP) are no-ops on this host.
        }

        public static void Bput(int channel, byte value)
        {
            if (!channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use BPUT with this channel", channel);
            }
            FileStream stream = channels[channel];
            stream.WriteByte(value);
        }

        public static int Bget(int channel)
        {
            if (!channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use BGET with this channel", channel);
            }
            FileStream stream = channels[channel];
            return stream.ReadByte();    // -1 at end of file
        }

        /// <summary>EOF#channel: TRUE (-1) when the file pointer is at the end.</summary>
        public static int Eof(int channel)
        {
            if (!channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use EOF with this channel", channel);
            }
            FileStream stream = channels[channel];
            return stream.Position >= stream.Length ? owlTrue : owlFalse;
        }

        public static void Close(int channel)
        {
            if (!channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use CLOSE with this channel", channel);
            }
            FileStream stream = channels[channel];
            stream.Dispose();
            channels.Remove(channel);
        }

        public static void Colour(int logicalColour)
        {
            vdu.Enqueue((byte) 17, (byte) logicalColour);  
        }

        public static void Gcol(int mode, int logicalColour)
        {
            vdu.Enqueue((byte) 18, (byte) mode, (byte) logicalColour);
        }

        public static void GcolTint(int mode, int logicalColour, int tint)
        {
            Gcol(mode, logicalColour);
            int type = logicalColour < 128 ? 2 : 3;
            vdu.Enqueue((byte) 23, (byte) 17, (byte) type, (byte) tint, (byte) 0, (byte) 0, (byte) 0, (byte) 0, (byte) 0, (byte) 0);
        }

        private static FileStream RequireChannel(int channel, string operation)
        {
            if (!channels.ContainsKey(channel))
            {
                throw new NoSuchChannelException("Cannot use " + operation + " with this channel", channel);
            }
            return channels[channel];
        }

        // PRINT# / INPUT# write BASIC's private type-tagged, byte-reversed record
        // format -- not text. A value is a one-byte type tag (&40 integer, &FF
        // real, &00 string) then the value's bytes written by a single
        // down-counting copy loop, so they land big-endian / last-character-first.
        // INPUT# undoes the reversal and validates the tag (Type mismatch on the
        // wrong one -- it does not coerce). See docs/divergences.md and the BBC
        // BASIC II disassembly (print_file / inputf_skip_hash).

        public static void PrintInteger(int channel, int value)
        {
            FileStream stream = RequireChannel(channel, "PRINT#");
            stream.WriteByte(0x40);
            stream.WriteByte((byte) (value >> 24));   // most-significant byte first
            stream.WriteByte((byte) (value >> 16));
            stream.WriteByte((byte) (value >> 8));
            stream.WriteByte((byte) value);
        }

        public static void PrintReal(int channel, double value)
        {
            FileStream stream = RequireChannel(channel, "PRINT#");
            byte[] packed = PackFloat5(value);        // exponent-first in memory
            stream.WriteByte(0xFF);
            for (int i = 4; i >= 0; i--)              // reversed: exponent lands last
            {
                stream.WriteByte(packed[i]);
            }
        }

        public static void PrintString(int channel, string value)
        {
            FileStream stream = RequireChannel(channel, "PRINT#");
            if (value.Length > 255)
            {
                throw new StringTooLongException();
            }
            stream.WriteByte(0x00);
            stream.WriteByte((byte) value.Length);
            for (int i = value.Length - 1; i >= 0; i--)   // characters reversed
            {
                stream.WriteByte((byte) value[i]);
            }
        }

        public static int InputInteger(int channel)
        {
            FileStream stream = RequireChannel(channel, "INPUT#");
            long offset = stream.Position;
            int tag = stream.ReadByte();
            if (tag != 0x40)
            {
                stream.Position = offset;
                throw new TypeMismatchException("INPUT# expected an integer record");
            }
            int b3 = stream.ReadByte();               // most-significant byte first
            int b2 = stream.ReadByte();
            int b1 = stream.ReadByte();
            int b0 = stream.ReadByte();
            return (b3 << 24) | (b2 << 16) | (b1 << 8) | b0;
        }

        public static double InputReal(int channel)
        {
            FileStream stream = RequireChannel(channel, "INPUT#");
            long offset = stream.Position;
            int tag = stream.ReadByte();
            if (tag != 0xFF)
            {
                stream.Position = offset;
                throw new TypeMismatchException("INPUT# expected a real record");
            }
            byte[] packed = new byte[5];
            for (int i = 4; i >= 0; i--)              // wire is reversed -> exponent-first
            {
                packed[i] = (byte) stream.ReadByte();
            }
            return UnpackFloat5(packed);
        }

        public static string InputString(int channel)
        {
            FileStream stream = RequireChannel(channel, "INPUT#");
            long offset = stream.Position;
            int tag = stream.ReadByte();
            if (tag != 0x00)
            {
                stream.Position = offset;
                throw new TypeMismatchException("INPUT# expected a string record");
            }
            int length = stream.ReadByte();
            char[] characters = new char[length];
            for (int i = length - 1; i >= 0; i--)     // characters stored reversed
            {
                characters[i] = (char) stream.ReadByte();
            }
            return new string(characters);
        }

        // BPUT#ch, A$ (BASIC V) writes the string's bytes; unless suppressed with
        // a trailing `;`, a newline (&0A) follows.
        public static void BputString(int channel, string value, int newline)
        {
            FileStream stream = RequireChannel(channel, "BPUT#");
            foreach (char c in value)
            {
                stream.WriteByte((byte) c);
            }
            if (newline != 0)
            {
                stream.WriteByte(0x0A);
            }
        }

        // The BBC 5-byte packed REAL, exponent-first (the ROM's constant-pool
        // order); folds the -128 excess bias and the 2^-32 fraction scale into
        // -160. Ported from oaknut-basic's float5.py for byte-identical interop.
        private const int Float5ExponentFold = 160;

        private static byte[] PackFloat5(double value)
        {
            byte[] packed = new byte[5];
            if (value == 0.0)
            {
                return packed;                        // five zero bytes
            }
            if (double.IsNaN(value) || double.IsInfinity(value))
            {
                throw new NumberTooBigException();
            }
            bool negative = double.IsNegative(value);
            double magnitude = Math.Abs(value);
            int exponent = Math.ILogB(magnitude) + 1;             // 0.5 <= fraction < 1
            double fraction = Math.ScaleB(magnitude, -exponent);
            long significand = (long) Math.Round(Math.ScaleB(fraction, 32), MidpointRounding.ToEven);
            if (significand == (1L << 32))            // rounded up to 1.0: carry into exponent
            {
                significand = 1L << 31;
                exponent += 1;
            }
            int biasedExponent = exponent + 128;
            if (biasedExponent > 0xFF)
            {
                throw new NumberTooBigException();
            }
            if (biasedExponent < 1)
            {
                return new byte[5];                   // underflow: no denormals
            }
            int signAndMsb = (int) ((significand >> 24) & 0x7F);  // drop the implied leading 1
            if (negative)
            {
                signAndMsb |= 0x80;
            }
            packed[0] = (byte) biasedExponent;
            packed[1] = (byte) signAndMsb;
            packed[2] = (byte) ((significand >> 16) & 0xFF);
            packed[3] = (byte) ((significand >> 8) & 0xFF);
            packed[4] = (byte) (significand & 0xFF);
            return packed;
        }

        private static double UnpackFloat5(byte[] packed)
        {
            int exponent = packed[0];
            if (exponent == 0)
            {
                return 0.0;
            }
            int signAndMsb = packed[1];
            bool negative = (signAndMsb & 0x80) != 0;
            long significand = ((long) ((signAndMsb | 0x80) & 0xFF) << 24)
                | ((long) packed[2] << 16) | ((long) packed[3] << 8) | packed[4];
            double value = Math.ScaleB((double) significand, exponent - Float5ExponentFold);
            return negative ? -value : value;
        }

        public static long Ext(int channel)
        {
            FileStream stream = RequireChannel(channel, "EXT#");
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
            FileStream stream = RequireChannel(channel, "PTR#");
            stream.Seek(offset, SeekOrigin.Begin);
        }

        public static long GetPtr(int channel)
        {
            FileStream stream = RequireChannel(channel, "PTR#");
            return stream.Position;
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="expr">The expression to be evaluated</param>
        /// <param name="module">The Type of the module holding the EVAL statement</param>
        /// <returns></returns>
        public static object Eval(string expr, Type module)
        {
            // Assume this is a very simple function call
            if (expr.StartsWith("FN"))
            {
                string name = expr.Substring(2);
                MethodInfo method = module.GetMethod(name);
                if (method == null)
                {
                    throw new NoSuchFnProcException(name); 
                }
                return method.Invoke(null, null);
            }
            // TODO: Syntax error
            return null;
        }

        /// <summary>A library feature OWL compiles but does not yet implement.
        /// The program compiles and runs; only reaching this operation fails, and
        /// loudly -- a deferred backend gap surfaced as a runtime library gap
        /// rather than a refusal to compile.</summary>
        public static void NotImplemented(string feature)
        {
            throw new NotImplementedFeatureException(feature);
        }

        /// <summary>GET$ / INKEY$: like INKEY but as a one-character string ("" on
        /// timeout / no key).</summary>
        public static string InkeyStr(int factor)
        {
            int code = Inkey(factor);
            return code < 0 ? "" : Chr(code);
        }

        public static int Inkey(int factor)
        {
            if (factor >= 0)
            {
                // INKEY(n): wait up to n centiseconds for a keypress; return its
                // code, or -1 if none arrives in time.
                if (Console.IsInputRedirected)
                {
                    // A redirected stream has no real-time keyboard: return a
                    // character if one is already waiting, otherwise -1 (so a
                    // pause-for-key does not block on an exhausted input).
                    return Console.In.Peek() < 0 ? -1 : Console.In.Read();
                }
                long deadline = Environment.TickCount64 + factor * 10L;
                do
                {
                    if (Console.KeyAvailable)
                    {
                        return Console.ReadKey(true).KeyChar;
                    }
                    System.Threading.Thread.Sleep(1);
                }
                while (Environment.TickCount64 < deadline);
                return -1;
            }
            if (factor == -256)
            {
                // INKEY(-256): a number identifying the host machine. The BBC
                // Master returns &FD; report a stable value so programs that
                // branch on the host still run.
                return 0xFD;
            }
            // INKEY(-n): is the key with that negative scan code held down? OWL
            // has no portable key-state source, so report "not pressed".
            return 0;
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
            // ReadKey needs an interactive console; when input is redirected
            // (a pipe or file) fall back to a character read from the stream.
            if (Console.IsInputRedirected)
            {
                int c = Console.Read();
                return c < 0 ? 13 : c;   // EOF -> Return, so prompts don't hang
            }
            ConsoleKeyInfo cki = Console.ReadKey(true);
            return cki.KeyChar;
        }

        /// <summary>
        /// Advance the 33-bit LFSR by 32 steps (one RND call). The feedback bit
        /// is bit 19 XOR bit 32; everything shifts up by one and the feedback
        /// enters at bit 0.
        /// </summary>
        private static void StepRandom()
        {
            for (int i = 0; i < 32; i++)
            {
                int newBit = (int) ((randomSeed >> 19) & 1u) ^ randomOverflow;
                randomOverflow = (int) ((randomSeed >> 31) & 1u);
                randomSeed = (randomSeed << 1) | (uint) newBit;
            }
        }

        /// <summary>
        /// The current state as a real in [0, 1). The ROM copies the seed bytes
        /// &amp;0D,&amp;0E,&amp;0F,&amp;10 into the floating-point mantissa
        /// most-significant-first, so the value is the byte-reversed 32-bit seed
        /// divided by 2^32.
        /// </summary>
        private static double RandomFraction()
        {
            uint m = (randomSeed << 24)
                   | ((randomSeed & 0x0000FF00u) << 8)
                   | ((randomSeed >> 8) & 0x0000FF00u)
                   | (randomSeed >> 24);
            return m / 4294967296.0;
        }

        public static double Rnd()
        {
            // RND with no argument: a full-range 32-bit signed integer.
            StepRandom();
            return (int) randomSeed;
        }

        public static double Rnd(int n)
        {
            if (n < 0)
            {
                // RND(-n): seed the generator from n and return n.
                randomSeed = (uint) n;
                randomOverflow = 0;
                return n;
            }
            if (n == 0)
            {
                // RND(0): repeat the last RND(1) -- the current state, no step.
                return RandomFraction();
            }
            StepRandom();
            if (n == 1)
            {
                // RND(1): a real in [0, 1).
                return RandomFraction();
            }
            // RND(n) for n >= 2: an integer in 1..n.
            return 1 + (int) (RandomFraction() * n);
        }

        public static void Vdu(byte b)
        {
            vdu.Enqueue(b);
        }

        public static void Vdu(short s)
        {
            vdu.Enqueue(s);
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

        public static void Plot(int mode, int xCoord, int yCoord)
        {
            vdu.Enqueue(25);
            vdu.Enqueue((byte) mode);
            vdu.Enqueue((short) xCoord);
            vdu.Enqueue((short) yCoord);
        }

        /// <summary>
        /// POINT(x, y): the logical colour of the pixel at a graphics
        /// coordinate (or -1 if off-screen). Reading the screen back is not yet
        /// implemented, so this is a stub: a program using POINT compiles, but
        /// raises at run time if it actually evaluates one.
        /// </summary>
        public static int Point(int xCoord, int yCoord)
        {
            throw new NotImplementedException(
                "POINT (reading a pixel's colour) is not yet implemented");
        }

        // HIMEM/LOMEM/PAGE/TOP/END introspect the BBC memory map of the BASIC
        // program. OWL targets .NET, where there is no such map, so these are
        // ultimately meaningless -- but programs read and compare them, so we
        // hand back fixed, plausible values in the correct relative order
        // (PAGE <= TOP <= LOMEM <= HIMEM, with END the top of variable space).
        // A program may still assign them; the arithmetic just works on numbers.
        public static int Page { get; set; } = 0x1900;   // start of program text
        public static int Top { get; set; } = 0x2000;    // end of program text
        public static int Lomem { get; set; } = 0x2000;  // start of variables (= TOP)
        public static int End { get; set; } = 0x2000;    // top of variables in use
        public static int Himem { get; set; } = 0x8000;  // top of BASIC's memory

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

        public static void Print(long i)
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
            if (Environment.GetEnvironmentVariable("OWL_RND_TRACE") != null)
            {
                // Diagnostic: the RND state at each input prompt, to diff against
                // the real machine's seed bytes (&0D-&10 + &11 bit 0).
                Console.Error.WriteLine("RND {0:X8} {1}", randomSeed, randomOverflow);
            }
            Queue<string> strings = new Queue<string>();
            do
            {
                if (prompt)
                {
                    printManager.Print('?');
                }
                string line = Console.ReadLine();
                if (line == null)
                {
                    // Genuine end of input on a redirected/headless run (an empty
                    // line is "", not null). There is nothing more to read, so end
                    // the program rather than spin returning empty input forever.
                    Console.Out.Flush();
                    Environment.Exit(0);
                }
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
            // The text cursor column, advanced by all character output and reset
            // to 0 on a newline. The VDU system tracks it for every path (PRINT
            // and VDU alike), whereas the print manager's count follows only
            // PRINT -- so a program that emits text with VDU (as ragged-num does)
            // and then reads POS needs the VDU's column.
            return vdu.TextCursorX;
        }

        public static int VPos()
        {
            return vdu.TextCursorY;
        }

        public static double Sqr(double factor)
        {
            if (factor < 0.0)
            {
                throw new NegativeRootException("Square root of negative number " + factor);
            }
            return Math.Sqrt(factor);
        }

        public static int Pow(int x, int y)
        {
            if (y < 0)
            {
                return (int) Pow((double) x, (double) y);
            }
            int result = 1;
            while (y != 0)
            {
                if ((y & 1) != 0)
                {
                    result *= x;
                }
                y >>= 1;
                x *= x;
            }
            return result;
        }

        public static double Pow(double x, double y)
        {
            double result = Math.Pow(x, y);
            if (Double.IsNaN(result))
            {
                throw new LogRangeException("Cannot raise " + x + " to power " + y);
            }
            if (Double.IsInfinity(result))
            {
                throw new DivisionByZeroException("Cannot raise " + x + " to power " + y);
            }
            return result;
        }

        /// <summary>
        /// Implementation of the MANDEL statement.
        /// MANDEL x,y: sets C% to the Mandelbrot colour of x,y limit D%
        /// </summary>
        /// <param name="x">The real co-ordinate</param>
        /// <param name="y">The imaginary co-ordinate</param>
        public static void Mandel(double cReal, double cImag)
        {
            // This code needs to be equivalent to the Python code
            // def mandel(c): # c is complex
            //     z = 0
            //     for h in range(1, 21):
            //             z = z**2 + c
            //             if abs(z) > 2:
            //                     break
            //     return h
            double zReal = 0.0;
            double zImag = 0.0;
            int d = OwlModule.iD;
            int h = 1;
            for (; h <= d ; ++h)
            {
                // z = z^2 + c
                double zRealNext = zReal * zReal - zImag * zImag + cReal;
                double zImagNext = zImag * zReal + zReal * zImag + cImag;
                double magnitude2 = zReal * zReal + zImag * zImag;
                if (magnitude2 > 4.0)
                {
                    break;
                }
                zReal = zRealNext;
                zImag = zImagNext;
            }
            OwlModule.iC = h;
        }

        public static int Time
        {
            get
            {
                // TIME counts in centiseconds. Advance ticksAtTime only by the
                // whole centiseconds consumed, keeping the leftover < 10 ms for
                // the next read -- otherwise rapid polling (as benchmarks do)
                // discards the sub-centisecond elapsed time and TIME never moves.
                int currentTicks = Environment.TickCount;
                int elapsedCentiseconds = (currentTicks - ticksAtTime) / 10;
                time += elapsedCentiseconds;
                ticksAtTime += elapsedCentiseconds * 10;
                return time;
            }

            set
            {
                time = value;
                ticksAtTime = Environment.TickCount;
            }
        }

        public static string CurrentDateTime
        {
            get
            {
                DateTime now = DateTime.Now;
                string result = now.ToString(acornDateTimeFormat);
                Debug.Assert(result.Length == 24);
                return result;
            }

            set
            {
                DateTime now;
                bool parsed = DateTime.TryParseExact(value, new[] {acornDateTimeFormat, bb4WDateTimeFormat},
                                                     new CultureInfo("en-GB"), DateTimeStyles.None,
                                                     out now);
                if (parsed)
                {
                    Microsoft.VisualBasic.DateAndTime.TimeOfDay = now;        
                }

            }
        }
    }

    public class OwlRuntimeException : Exception
    {
        public OwlRuntimeException(string message) :
            base("OwlRuntimeException: " + message)
        {
        }

        // The BBC error number (ERR) and report message (REPORT/REPORT$).
        // Defaults are a best effort; subclasses with a known BBC error override.
        public virtual int ErrorNumber => 0;
        public virtual string ReportMessage => Message;
    }

    public class TypeMismatchException :OwlRuntimeException
    {
        public TypeMismatchException(string message) :
            base("Type mismatch: " + message)
        {
        }
    }

    public class StringTooLongException :OwlRuntimeException
    {
        public override int ErrorNumber => 19;
        public StringTooLongException() :
            base("String too long")
        {
        }
    }

    /// <summary>A BBC BASIC feature OWL compiles but has not yet implemented in
    /// the runtime. Raised when such an operation is actually executed.</summary>
    public class NotImplementedFeatureException :OwlRuntimeException
    {
        public NotImplementedFeatureException(string feature) :
            base(feature + " is not yet implemented in the OWL runtime")
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

    public class NegativeRootException :OwlRuntimeException
    {
        public NegativeRootException(string message) :
            base("Negative root: " + message)
        {
        }
    }

    public class LogRangeException :OwlRuntimeException
    {
        public LogRangeException(string message) :
            base("Log range: " + message)
        {
        }
    }

    public class DivisionByZeroException :OwlRuntimeException
    {
        public DivisionByZeroException(string message) :
            base("Division by zero: " + message)
        {
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
    /// To be thrown by redimensioned arrays.
    /// </summary>
    public class BadDimException :OwlRuntimeException
    {
        public BadDimException(int logicalLineNumber) :
            base("Bad DIM at line " + logicalLineNumber)
        {
        }
    }

    /// <summary>
    /// Thrown when a 64-bit value is stored into a narrower (32-bit) variable
    /// and does not fit: BBC BASIC error 20, "Number too big".
    /// </summary>
    public class NumberTooBigException :OwlRuntimeException
    {
        public override int ErrorNumber => 20;
        public NumberTooBigException() :
            base("Number too big")
        {
        }
    }

    /// <summary>
    /// Thrown when EVAL("&"+h$) is handed a string whose leading character is
    /// not an (uppercase) hex digit, including the empty string: BBC BASIC's
    /// "Bad hex", error 28 (the ROM's factor_hex raises BRK &1C when its hex
    /// reader consumes zero digits).
    /// </summary>
    public class BadHexException : OwlRuntimeException
    {
        public override int ErrorNumber => 28;
        public BadHexException() :
            base("Bad hex")
        {
        }
    }

    public class NoSuchFnProcException :OwlRuntimeException
    {
        private string name;

        public NoSuchFnProcException(string name) :
            base("No such FN/PROC : " + name)
        {
            this.name = name;
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
