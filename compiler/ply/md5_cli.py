# Copyright (c) 2006 by Seo Sanghyeon
# You just DO WHAT THE FUCK YOU WANT TO
# Updated by Resolver Systems: http://www.resolversystems.com

# 2006-01-26 sanxiyn Created

from System.Security.Cryptography import MD5CryptoServiceProvider

from System.Text import Encoding
raw = Encoding.GetEncoding('iso-8859-1')
empty = raw.GetBytes('')

class MD5Type:

    def __init__(self):
        self.context = MD5CryptoServiceProvider()

    def update(self, string):
        bytes = raw.GetBytes(string)
        self.context.TransformBlock(bytes, 0, bytes.Length, bytes, 0)

    def digest(self):
        self.context.TransformFinalBlock(empty, 0, 0)
        return raw.GetString(self.context.Hash)

    def hexdigest(self):
        self.context.TransformFinalBlock(empty, 0, 0)
        string = ['%02x' % byte for byte in self.context.Hash]
        return ''.join(string)

def new(string=None):
    crypto = MD5Type()
    if string:
        crypto.update(string)
    return crypto
