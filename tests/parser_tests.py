import unittest
import xml.etree.ElementTree as ET

from syntax.ast import *


class SyntaxTest(unittest.TestCase):
    
    def compiletoXml(self, basic):
        ast = yacc.parse(basic)
        xmlv = XmlVisitor()
        ast.accept(xmlv)
        xmlv.close()
        return ET.XML(xmlv.xml)
    
    def testAdvalBuffer(self):
        element = self.compileToXml('A = ADVAL-1')
        
    def testAdvalExpression(self):
        element = self.compileToXml('A = ADVAL(-10)')
        
        
        
        
        