#!/usr/bin/perl

use strict;

my $usage = q{
tominijam.pl Used to resample / reencode mp3, ogg vorbis and files
for an mp3 player.

Usage:
	mp3shrink.pl [-q={1,2,3,4}] FILES_TO_REENCODE

The optional '-q=' parameter specifies the amount of space savings desired
compared to standard 44kHz 128kbps MP3 encoding.
	1	44.00kHz	128kbps	sterio
	2	22.05kHz	64kbps	sterio
	3	22.05kHz        32kbps  mono
        4       11.025kHz	24kbps	mono
If not specified, q=2 is used.

Author: Daniel Casner <daniel@danielcasner.org>
};


my $q = 2; # Default quality level

if($ARGV[0] eq '-h' or $ARGV[0] eq '--help') {
	print $usage;
	exit(0);
} elsif($ARGV[0] =~ m/-q=([123])/) {
	shift(@ARGV);
	$q = $1;
}

my @freq = ('44', '22.05', '22.05', '11.025');
my @rate = ('128', '64', ,'32', '24');

system('mkdir', 'out');

my @encArgs = ('lame', '-h', '-s' . $freq[$q-1], '-b' . $rate[$q-1]);

# Add mono argument
push(@encArgs, '-a') if($q == 3);

foreach (@ARGV) {
	chomp;
	die "Invaild input file format: $_" unless /(.*)\.(\w+)$/;
	my ($name, $ext) = ($1, $2);
	if($ext eq 'mp3') {
		die if system(@encArgs, '--mp3input', $_, "out/$name.mp3");
	} elsif($ext eq 'ogg') {
		die if system('ogg123', '-dwav', "-f/tmp/$name.wav", $_);
		die if system(@encArgs, "/tmp/$name.wav", "out/$name.mp3");
		die if system('rm', "/tmp/$name.wav");
	} elsif($ext eq 'wav') {
		die if system(@encArgs, $_, "out/$name.mp3");
	} elsif($ext eq 'flac') {
	    die if system('mplayer',  '-ao', "pcm:file=/tmp/$name.wav", $_);
	    die if system(@encArgs, "/tmp/$name.wav", "out/$name.mp3");
	    die if system('rm', "/tmp/$name.wav");
	} else {
		die "Invalid input file format: $_";
	}
}


print "Finished converting, output files are in the directory 'out'\n";
