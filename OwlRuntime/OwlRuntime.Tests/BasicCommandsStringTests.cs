using OwlRuntime;
using Xunit;

namespace OwlRuntime.Tests
{
    /// <summary>
    /// Tests the platform-neutral string functions of <see cref="BasicCommands"/>,
    /// pinning down BBC BASIC semantics (1-based indexing, clamping, the empty
    /// string and not-found conventions).
    /// </summary>
    public class BasicCommandsStringTests
    {
        [Theory]
        [InlineData("A", 65)]
        [InlineData("0", 48)]
        [InlineData("", -1)]   // ASC of the empty string is -1 in BBC BASIC
        public void Asc_returns_first_character_code_or_minus_one(string s, int expected)
        {
            Assert.Equal(expected, BasicCommands.Asc(s));
        }

        [Fact]
        public void Chr_converts_a_code_to_a_one_character_string()
        {
            Assert.Equal("A", BasicCommands.Chr(65));
        }

        [Fact]
        public void Asc_and_Chr_round_trip()
        {
            Assert.Equal(66, BasicCommands.Asc(BasicCommands.Chr(66)));
        }

        [Theory]
        [InlineData("HELLO", 2, "HE")]
        [InlineData("HELLO", 0, "")]
        [InlineData("HELLO", 10, "HELLO")]   // length is clamped to the string
        public void LeftStr_returns_the_left_substring(string s, int length, string expected)
        {
            Assert.Equal(expected, BasicCommands.LeftStr(s, length));
        }

        [Theory]
        [InlineData("HELLO", 2, "LO")]
        [InlineData("HELLO", 10, "HELLO")]
        public void RightStr_returns_the_right_substring(string s, int length, string expected)
        {
            Assert.Equal(expected, BasicCommands.RightStr(s, length));
        }

        [Theory]
        [InlineData("HELLO", 2, 3, "ELL")]   // MID$ start index is 1-based
        [InlineData("HELLO", 1, 5, "HELLO")]
        public void MidStr_returns_a_one_based_substring(string s, int start, int length, string expected)
        {
            Assert.Equal(expected, BasicCommands.MidStr(s, start, length));
        }

        [Theory]
        [InlineData("HELLO", "L", 3)]   // INSTR result is 1-based
        [InlineData("HELLO", "Z", 0)]   // not found is 0
        public void Instr_returns_a_one_based_position_or_zero(string searched, string substring, int expected)
        {
            Assert.Equal(expected, BasicCommands.Instr(searched, substring));
        }

        [Theory]
        [InlineData("42", 42.0)]
        [InlineData("", 0.0)]                  // empty string is 0
        [InlineData("   ", 0.0)]               // whitespace only is 0
        [InlineData("X12", 0.0)]               // no leading number is 0
        [InlineData("  123", 123.0)]           // leading spaces are skipped
        [InlineData("+5", 5.0)]                // a leading plus (ROM-confirmed)
        [InlineData("--5", 0.0)]               // a second sign is not a digit: 0 (ROM-confirmed)
        [InlineData("  -3.5", -3.5)]            // leading spaces and a sign
        [InlineData("007", 7.0)]               // leading zeros
        [InlineData("12X", 12.0)]              // value of the leading numeric part
        [InlineData("1 2", 1.0)]               // an internal space ends the number
        [InlineData(".5", 0.5)]                // a leading decimal point
        [InlineData("5.", 5.0)]                // a trailing decimal point
        [InlineData("1.2.3", 1.2)]             // only the first decimal point counts
        [InlineData(".E3", 0.0)]               // no mantissa digit: not a number
        [InlineData("&FF", 0.0)]               // VAL scans decimal only, not &hex (ROM-confirmed)
        [InlineData("1E3", 1000.0)]            // VAL scans the E exponent...
        [InlineData("1.2E10", 1.2E10)]         // ...like the rest of BBC BASIC
        [InlineData("1E-3", 0.001)]            // a signed exponent
        [InlineData("-.5E1", -5.0)]            // sign, leading point, exponent
        [InlineData("-2.5E-2", -0.025)]        // signed mantissa and signed exponent
        [InlineData("1E3+1", 1000.0)]          // stops at the operator, as VAL does
        [InlineData("123ABC", 123.0)]          // stops at the first non-numeric
        [InlineData("123E", 123.0)]            // a bare E is not an exponent: backtrack
        [InlineData("123E2", 12300.0)]         // ...but E2 is consumed
        [InlineData("123E2ABC", 12300.0)]      // exponent then stops at the letters
        [InlineData("1EX", 1.0)]               // malformed exponent: E is not consumed
        public void Val_scans_the_leading_numeric_literal_including_exponents(string s, double expected)
        {
            Assert.Equal(expected, BasicCommands.Val(s));
        }

        [Theory]
        [InlineData("FF", 255L)]               // EVAL("&"+h$): the hex value of h$
        [InlineData("7FFFFFFF", 2147483647L)]
        [InlineData("FFFFFFFF", -1L)]          // 8 hex digits: a 32-bit signed pattern
        [InlineData("FG", 15L)]                // reads the F, stops at G (ROM factor_hex)
        [InlineData("FFx", 255L)]              // trailing non-hex tolerated, no fault
        [InlineData("Ff", 15L)]                // lowercase f terminates: reads F=15, stops
        public void EvalHex_reads_the_leading_hex_run(string s, long expected)
        {
            Assert.Equal(expected, BasicCommands.EvalHex(s));
        }

        [Fact]
        public void Val_faults_too_big_on_overflow()
        {
            // VAL("1E999") overflows the float range: BBC "Too big" (error 20),
            // not an infinity.
            Assert.Throws<NumberTooBigException>(() => BasicCommands.Val("1E999"));
        }

        [Fact]
        public void EvalHex_supersets_the_ROM_to_64_bits_beyond_8_digits()
        {
            // Deliberate divergence: the ROM rolls into a 32-bit cell and the 9th
            // digit shifts off the top, so the ROM gives 0 for "&100000000". OWL
            // keeps 64 bits for 9-16 digits, matching its own hex-literal lexer.
            Assert.Equal(4294967296L, BasicCommands.EvalHex("100000000"));
        }

        [Theory]
        [InlineData("")]                       // EVAL("&"): no digit -> Bad hex (err 28)
        [InlineData("ff")]                     // leading lowercase: zero digits read -> Bad hex
        [InlineData("G")]                      // no leading hex digit -> Bad hex
        public void EvalHex_faults_when_not_led_by_a_hex_digit(string s)
        {
            Assert.Throws<BadHexException>(() => BasicCommands.EvalHex(s));
        }
    }
}
