import sys
import unittest

import process

class ForLoopTestCase(unittest.TestCase):

    def compile(self, source):
        '''Execute the OWL compiler in a separate process.

        Args:
            source: The path to the source file to be compiled.

        Returns:
            A 2-tuple containing two strings. The first is the path to the
            compiled executable and the second is a log of standard error
            output.

        Raises:
            CompileError: If compilation failed.
        '''
        code, out, err = process.execute(sys.executable, r'C:\Users\rjs\Documents\dev\PycharmProjects\owl_basic\compiler\main.py', source)
        print code
        print out
        print err
        return "unknown.exe", out, err

    def execute(self, exe_path):
        '''Execute the provided executable and capture console output.

        Args:
            exe_path: The path to the executable.

        Returns:
            A string containing the std-out from the process.

        Raises:
            ValueError: If exe_path does not exist or cannot be executed.
        '''
        pass

    def check_compile(self, source, expected_console):
        '''Compile the source, execute the resulting program and compare output.

        Args:
            source: The path to the source file to be compiled.
        '''
        exe, out, err = self.compile(source)
        actual_console = self.execute(exe)
        self.assertEqual(actual_console, expected_console)

    def test_for_loop_01(self):
        self.check_compile(r'C:\Users\rjs\Documents\dev\PycharmProjects\owl_basic\compiler\tests\end_to_end\for_loops\for_loop_01.owl',
                           r'C:\Users\rjs\Documents\dev\PycharmProjects\owl_basic\compiler\tests\end_to_end\for_loops\for_loop_01.txt')
        
    #def test_for_loop_02(self):
    #    self.check_compile('for_loop_02.owl', 'for_loop_02.txt')

    #def test_for_loop_03(self):
    #    self.check_compile('for_loop_03.owl', 'for_loop_03.txt')




if __name__ == '__main__':
    unittest.main()
