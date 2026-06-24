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
        [InlineData("  -3.5", -3.5)]            // leading spaces and a sign
        [InlineData("12X", 12.0)]              // value of the leading numeric part
        [InlineData("X12", 0.0)]               // no leading number is 0
        [InlineData("1E3", 1000.0)]            // VAL scans the E exponent...
        [InlineData("1.2E10", 1.2E10)]         // ...like the rest of BBC BASIC
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
    }
}
