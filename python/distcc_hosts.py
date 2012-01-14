#!/usr/bin/env python
"""
A dumb app to see which of a set of possible distcc hosts are up
"""
__author__ = "Daniel Casner <www.danielcasner.org>"
__version__ = 0.1
import sys, socket

DISTCC_PORT = 3632

USAGE = """
distcc_hosts -- USAGE

    eval `%s [options] HOSTS TO TEST`

Where HOSTS TO TEST is any number of arguments of the form
<host name>[/<num jobs>]. This will export the environmental
variables DISTCC_HOSTS and PARALLEL_JOBS.

Options:
    -p  Specify an alternate port to the default %d
    -h  Print this help message
""" % (sys.argv[0], DISTCC_PORT)

def try_connect(host, port):
    """
    Attempts to open a TCP socket to the specified host on the specified port.
    Returns True on success False on failure.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect((host, port))
    except socket.error:
        return False
    else:
        return True

def parse_host(arg):
    try:
        host, jobs = arg.split('/')
        jobs = int(jobs)
    except:
        host = arg
        jobs = 1
    return host, jobs


if __name__ == '__main__':
    args = sys.argv[1:]
    # Parse options
    if not len(args) or '-h' in args or '--help' in args:
        sys.stderr.write(USAGE)
    elif '-p' in args:
        try:
            port_str = args[x.index('-p') + 1]
            port = int(portArg)
        except Exception:
            sys.stderr.write('Invalid arguments to %s\n' % sys.argv[0])
            sys.stderr.write(USAGE)
            sys.exit(1)
        else:
            args.remove(port_str)
            args.remove('-p')
    else:
        port = DISTCC_PORT
    # Run
    alive = [host for host in args if try_connect(parse_host(host)[0], port)]
    sys.stdout.write('export DISTCC_HOSTS="%s"\n' % (' '.join(alive)))
    num_jobs = sum([parse_host(h)[1] for h in alive])
    sys.stdout.write('export PARALLEL_JOBS=%d\n' % num_jobs)
    sys.stdout.write('export PARALLEL=-j%d\n' % num_jobs)
    sys.stdout.write('export CCACHE_PREFIX=distcc\n')
