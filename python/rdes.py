#!/usr/bin/env python

import os, getopt, bz2
import cPickle as pickle
from Crypto.Hash import MD5 as Hasher
from Crypto.Cipher import Blowfish as Encryptor

DEFAULT_BUFFER_LENGTH = 2**20*10

class ZipEncFile(file):
    "A generator for the zipped encrypted file"

    def __init__(self, pathname, key, buffer_size=DEFAULT_BUFFER_LENGTH):
        "Initalizes the file object"
        super(ZipEncFile, self).__init__(pathname, 'rb')
        self.compressor = bz2.BZ2Compressor()
        self.encryptor  = Encryptor.new(key)
        self.buffer = buffer_size

    def read(read_length=None):
        "Gets the next chunk of zipped, encrypted data."
        if read_length is None: read_length = self.buffer_size
        data = super(ZipEncFile, self).read(read_length)
        got_length = len(data)
        data = self.compressor.compress(data)
        if got_length < read_length: data += self.compressor.flush()
        return self.encryptor.encrypt(data)


def processFile(pathname, hash_dict, key):
    """Reads, the specified file:
    returns None if the file hasn't changed,
    returns an ZipEncFile object if it has.
    """
    if not hash_dict.has_key(pathname):
        return ZipEncFile(pathname, key)
    else:
        fh = file(pathname, 'rb')
        cksum = Hasher.new(fh.read())
        fh.close();
        if cksum == hash_dict[pathname]: return None
        else: return ZipEncFile(pathname, key)
        
    
def decrypt(source, key, dest, buffer_size=DEFAULT_BUFFER_LENGTH):
    "Decrypts the specified file and writes it to dest"
    sfh = file(source, 'rb')
    dfh = file(dest, 'wb')
    decryptor = Encryptor.new(key)
    uncompressor = bz2.BZ2Decompressor()
    while True:
        try:
            dfh.write(uncompressor.decompress(decryptor.decrypt(sfh.read(buffer_size))))
        except EOFError:
            break
    dfh.close()
    sfh.close()
