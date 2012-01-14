#!/usr/bin/perl

use strict;
use List::Util 'shuffle';

my $regex = '"\.ogg$\|\.mp3$"';
my $files = `find . | grep -e $regex`;

my @playlist = split(/\n/, $files);

foreach (shuffle(@playlist)) {
	chomp;
	if($_ =~ m/\.ogg$/) {
		system('ogg123', $_);
	} else {
		system('mpg321', $_);
	}
}
