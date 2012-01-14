#!/usr/bin/perl

use strict;
use File::Slurp qw(slurp);

my ($find, $replace) = @ARGV;
unless(defined $find && defined $replace) {
	print STDERR q{
replace.pl

Usage:
	replace.pl FIND_STRING REPLACEMENT_STRING

Recursively replaces all occurances of FIND_STRING with
REPLACEMENT_STRING in all files starting from the current
directory.
};
}

my $files = `grep -rl $find ./*`;
my @files = split(/\n/, $files);

foreach (@files) {
	chomp;
	print $_ . "\n";
	die unless my $text = slurp($_);
	
	$text =~ s/$find/$replace/g;
	
	die unless open(FH, ">$_");
	die unless print FH $text;
	die unless close(FH);
}
