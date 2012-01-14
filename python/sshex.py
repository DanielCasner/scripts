#!/usr/bin/env
"""
A python module to make executing python code on a remote machine easier.
The base method of remote execution is ssh via the subprocess module.
"""
__author__ = 'Daniel Casner <www.danielcasner.org>'
__version__ = 0.1

import sys, subprocess
import cPickle as pickle



class SSHNode(object):
    """
    A class representing an SSH connection to a user module running on a
    remote machine communicating over SSH.
    """

    def __init__(self, host, ssh_options=[], local_py_file=None, remote_module=None):
        """Constructor for an SSH execution node
        host          Specifies the ssh host argument to connect to.
        ssh_options   Optional extra arguments to ssh
        local_py_file The filename of a local python source file to
                      execute on the remote host. Exclusive with
                      remote_module
        remote_module The name of a module to import on the remote host.
                      Exclusive with local_py_file.
        """
        if local_py_file is not None and remote_module is None:
            source = file(local_py_file, 'r').read()
            self.conn = subprocess.Popen(['ssh'] + ssh_options + ['python -i'],
                                     stdin  = subprocess.PIPE,
                                     stdout = subprocess.PIPE,
                                     stderr = sys.stderr)
            sys.stdout.write(self.conn.communicate(source)[0])
        elif remote_module is not None:
            self.conn = subprocess.Popen(['ssh'] + ssh_options + ['python -m ' + remote_module],
                                     stdin  = subprocess.PIPE,
                                     stdout = subprocess.PIPE,
                                     stderr = sys.stderr)
            sys.stdout.write(self.conn.communicate()[0])
        else:
            raise TypeError, 'SSHNode requires either "local_py_file", or "remote_module" to be not None.'

    
            
        




