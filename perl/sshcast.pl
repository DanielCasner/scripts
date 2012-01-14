#!/usr/bin/perl

use POSIX;
use List::Util 'shuffle';
use strict;

use constant USAGE => q{
Usage:

	sshcast.pl HOST {DIRECTORY|PLAYLIST} [-s]

SCPs files from DIRECTORY (recursive) or PLAYLIST one at a time from HOST one at a
time and plays them. If -s is supplied then the playlist is shuffled. Use the
username@host format to specify a different user name and the computer this script
is operating on must be in allowed_keys or you will have to enter your password for
each file.

Requirements:
	* Perl
	* mpg321
	* ogg123
 
Author:
	Daniel Casner
	www.danielcasner.org
};

my $host = $ARGV[0];
if((!defined $host) or ($host eq '-h') or ($host eq '--help')) {
	print USAGE;
	exit(2);
}

my @playlist;
my $format;

if($ARGV[1] =~ /\.pls$/) {
    unless(open(PLS, $ARGV[1])) {
	print STDERR "Couldn't open playlist file\n";
	exit(1);
    }
    @playlist = <PLS>;
    close(PLS);
    $format = 'pls';
}
else {
    unless(open(PLS, "ssh $host find $ARGV[1]/ |")) {
	print STDERR "Couldn't list files in specified directory\n";
	exit(1)
    }
    @playlist = <PLS>;
    close(PLS);
    $format = 'dir';
}

@playlist = shuffle(@playlist) if $ARGV[2] eq '-s';

my $downloaded = undef;
foreach (@playlist) {
    chomp($_);
    my $file;
    if($format eq 'pls') {
	next if $_ !~ /^File\d+=(.*\.(mp3|ogg))$/; # Ignore lines that aren't files or types
	$file = $1;
    }
    elsif($format eq 'dir') {
	next if $_ !~ /.*\.(mp3|ogg)$/;
	$file = $_;
    }
    else {
	print STDERR "Invalid arguments\n";
    }
    
    my $pid = fork();
    if(!defined $pid) {
	# Check that spawn was successful.
	print STDERR "Couldn't spawn dowload thread\n";
	exit(1);
    } elsif($pid == 0) {
	# Child process, does download...
	my $scp_file = '"' . $file . '"';
	#$scp_file =~ s/ /\\ /g; # Replace all spaces with escaped spaces
	print STDOUT "Downloading: $scp_file\n";
	exec('scp', "$host:$scp_file", './');
	# If code exicution ever gets here the exec didn't work
	die "Couldn't exicute scp download command\n";
    } else {
	# Parent process, plays music.
	if(defined $downloaded) {
	    my $player = undef;
	    $player = 'mpg321' if($downloaded =~ /\.mp3$/);
	    $player = 'ogg123' if($downloaded =~ /\.ogg$/);
	    if(system($player, $downloaded)) {
		print STDERR "Error playing file $downloaded\n";
	    }
	    system('chmod', '+w', $downloaded);
	    system('rm', $downloaded);
	} else {
	    print "Please wait for the first file to download...\n";
	}
	
	waitpid($pid,0);
	if($? != 0) {
	    print STDERR "Error downloading next file skipping.\n";
	    $downloaded = undef;
	    next;
	} else {
	    my @file = split(/[\/\\]/, $file); # Split on a forward of backward slash
	    $downloaded = pop(@file);
	}
    }
}

