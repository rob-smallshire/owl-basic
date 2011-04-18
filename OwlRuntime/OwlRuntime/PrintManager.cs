using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

using OwlRuntime.platform.riscos;

namespace OwlRuntime
{
    internal class PrintManager
    {
        private readonly VduSystem vdu;
        private readonly OS os;

        private enum NumberBase
        {
            Decimal,
            Hexadecimal
        }

        private  NumberBase numberBase;

        private enum Justification
        {
            Left,
            Right
        }

        private Justification numberJustification;

        private int count = 0;
        private int width = 0; // A width of 0 means that width is ignored

        // Variables for @% functionality

        /// <summary>
        /// Corresponds to byte 4 of @%, which can be which can be 1 or 0. corresponds to the
        /// + STR$ switch. If this byte is 1, STR$ uses the format specified by the rest of @%.
        /// If it is 0, STR$ uses its default value of &00000A00.
        /// </summary>
        private bool affectStr; // True if @% affects STR$ - corresponds to byte 4 of @%
                                
        /// <summary>
        /// The three numeric formats supported by BBC BASIC.
        /// </summary>
        enum NumberFormat
        {
            General = 0,
            Exponent = 1,
            Fixed = 2
        }

        /// <summary>
        /// Corresponds to byte 3 of @%. The format used for displaying numbers.
        /// </summary>
        private NumberFormat numberFormat;

        /// <summary>
        /// Corresponds to byte 2 of @%.  Can take values from 1 to 10, determines the
        /// number of digits printed. In General format, this is the number of digits
        /// which may be printed before reverting to Exponent format (1 to 10); in
        /// Exponent format it gives the number of significant figures to be printed
        /// after the decimal point (1 to 10). In fixed format it gives the number of
        /// digits (exactly) that follow the decimal point.
        /// </summary>
        private byte precision;

        /// <summary>
        /// Corresponds to byte 1 of @%. in the range 0 to 255, gives the print field
        /// width for tabulating using commas. 
        /// </summary>
        private byte fieldWidth;

        public PrintManager(OS os, VduSystem vdu)
        {
            this.os = os;
            this.vdu = vdu;
            FormatNumber = 0x90A;
        }

        /// <summary>
        /// Set the BBC BASIC @% value according to the rules specified by the
        /// BBC BASIC V 1.05 interpreter.
        /// The value of @% is specified in ANSI printf format,
        /// as follows:
        /// @%="expression"
        /// where expression takes the form [+]Ax.y, and must be in quotes.
        /// A defines the format, and can take the following values:
        ///   G (General format). In G format, x defines the field width and y defines
        ///     the number of digits to be printed. Note that if x is less than 0.01, printing
        ///     reverts to E format.
        ///   E (Exponent format). In E format, x defines the field width and y defines the
        ///     number of significant figures to be printed after the decimal point. Note that
        ///     E format allows 3 digits for the exponent, and an optional minus sign. This will
        ///     leave up to three trailing spaces if the exponent is positive and only one or two
        ///     digits long. 
        ///   F (Fixed format). In F format, x defines the number of figures (exactly) to be
        ///     printed after the decimal point and y defines the field width.
        /// 
        /// The optional+ sign is a switch affecting the STR$ function. If supplied, it forces
        /// STR$ to use the format determined by @%. If it is not supplied, STR$ uses a default
        /// format equivalent to @%="+G0.10". Note that there must not be any spaces in the
        /// definition of @%.
        /// 
        /// The BASIC 1.05 interpreter supports partial setting of @%, which means you do not 
        /// have to supply all the arguments.
        public string FormatString
        {
            get
            {
                StringBuilder sb = new StringBuilder();
                if (affectStr)
                {
                    sb.Append("+");
                }
                sb.Append(FormatChar);
                sb.Append(fieldWidth);
                sb.Append('.');
                sb.Append(precision);
                return sb.ToString();
            }

            set
            {
                Match match = Regex.Match(value, @"^(\+?)([GEF]?)(\d*)(\.\d+)?");
                if (match.Success)
                {
                    affectStr = match.Groups[1].ToString() == "+";

                    string format = match.Groups[2].ToString();
                    if (format.Length > 0)
                    {
                        switch (format[0])
                        {
                            case 'G':
                                numberFormat = NumberFormat.General;
                                break;
                            case 'E':
                                numberFormat = NumberFormat.Exponent;
                                break;
                            case 'F':
                                numberFormat = NumberFormat.Fixed;
                                break;
                        }
                    }

                    Byte.TryParse(match.Groups[3].ToString(), out fieldWidth);
                    Byte.TryParse(match.Groups[4].ToString(), out precision);
                }
            }
        }

        private char FormatChar
        {
            get
            {
                switch (numberFormat)
                {
                    case NumberFormat.General:
                        return 'G';
                    case NumberFormat.Exponent:
                        return 'E';
                    case NumberFormat.Fixed:
                        return 'F';
                }
                return ' ';
            }
        }

        /// <summary>
        /// You can set the variable @% to produce the same results as the BASIC 1.05 interpreter. 
        /// The value of @% is specified using a hexadecimal word four bytes long, as follows:
        /// @%=&wwxxyyzz
        /// l Byte 4, which can be 1 or 0, corresponds to the + STR$ switch. If this byte is 1, 
        /// STR$ uses the format specified by the rest of @%. If it is 0, STR$ uses its default 
        /// value of &00000A00.
        /// l Byte 3, which can be 0, 1 or 2, selects the G, E or F format.
        /// l Byte 2, which can take values from 1 to 10, determines the number of digits printed. 
        /// In General format, this is the number of digits which may be printed before 
        /// reverting to Exponent format (1 to 10); in Exponent format it gives the number of 
        /// significant figures to be printed after the decimal point (1 to 10). In fixed format it 
        /// gives the number of digits (exactly) that follow the decimal point.
        /// l Byte 1, which is in the range 0 to 255, gives the print field width for tabulating using 
        /// commas.
        /// </summary>
        public int FormatNumber
        {
            get
            {
                int byte4 = (affectStr ? 1 : 0) << 24;
                int byte3 = (int) numberFormat  << 16;
                int byte2 = precision          << 8;
                int byte1 = fieldWidth;
                return byte4 | byte3 | byte2 | byte1;
            }

            set
            {
                int byte4 = (value >> 24) & 0xFF;
                int byte3 = (value >> 16)  & 0xFF;
                int byte2 = (value >> 8) & 0xFF;
                int byte1 = value & 0xFF;

                affectStr = (byte4 != 0);
                numberFormat = (NumberFormat) byte3;
                precision = (byte) byte2;
                fieldWidth = (byte) byte1;
            }
        }

        public int Count
        {
            get { return count; }
        }

        public void ResetCount()
        {
            count = 0;
        }

        public int Width
        {
            get { return width; }
            set { width = value; }
        }

        public void TabH(int xCoord)
        {
            int offset = xCoord - count;
            if (offset > 0)
            {
                Spc(offset);
            }
            else if (offset < 0)
            {
                NewLine();
                Spc(xCoord);
            }
        }

        public void TabXY(int xCoord, int yCoord)
        {
            vdu.Enqueue(31, (byte) xCoord, (byte) yCoord);
        }

        public void HexFormat()
        {
            numberBase = NumberBase.Hexadecimal;
        }

        public void DecFormat()
        {
            numberBase = NumberBase.Decimal;
        }

        public void DisableRightJustifyNumerics()
        {
            numberJustification = Justification.Left;
        }

        public void RightJustifyNumerics()
        {
            numberJustification = Justification.Right;
        }

        public void NewLine()
        {
            os.NewLine();
            count = 0;
        }

        /// <summary>
        /// Write spaces to move us to the beginning of the next output field
        /// </summary>
        public void CompleteField()
        {
            if (fieldWidth == 0)
            {
                return;
            }

            if (count == 0)
            {
                return;
            }

            if (fieldWidth != 0 && count != 0)
            {
                Spc(fieldWidth - count % fieldWidth);
            }
        }

        public void Spc(int padding)
        {
            for (int i = 0; i < padding; ++i)
            {
                Print(' ');
            }
        }

        public void Print(string s)
        {
            foreach (char c in s)
            {
                Print(c);
            }
        }

        public void Print(char c)
        {
            if (width > 0 && count > width)
            {
                NewLine();
            }
            ++count;
            os.WriteC(c);
            if (c == 0x0d)
            {
                count = 0;
            }
        }

        public void Print(int i)
        {
            string format = numberBase == NumberBase.Decimal
                            ? FormatChar + precision.ToString()
                            : "X" + precision;

            string s = i.ToString(format);
            if (numberJustification == Justification.Right)
            {
                Spc(fieldWidth - s.Length);
            }
            Print(s);
        }

        public void Print(double d)
        {
            if (numberBase == NumberBase.Hexadecimal)
            {
                Print((int) d);
            }
            else
            {
                string format = FormatChar + precision.ToString();
                string s = d.ToString(format);
                if (numberJustification == Justification.Right)
                {
                    Spc(fieldWidth - s.Length);
                }
                Print(s);
            }
        }

        public void Print(object o)
        {
            if (o is int)
            {
                Print((int) o);
            }
            else if(o is double)
            {
                Print((double) o);
            }
            else if(o is string)
            {
                Print((string) o);
            }
            else
            {
                Print(o.ToString());
            }
        }
    }
}
