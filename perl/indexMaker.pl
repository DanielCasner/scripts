#!/usr/bin/perl

use strict;

# Get a list of all the files in the directory
my $ls = `ls`;
my @files = split(/\n/, $ls);

# Open index.html for writing
die unless open(FH, '>index.html');

# Print the header to the file
print FH q{<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<ul>};

# Print the file list to the index
foreach (@files) {
	print FH '  <li><a href="' . $_ . '">' . $_ . "</a></li>\n";
}

# Print the footer.
print FH q{</ul>
</body>
</html>};

# And close the file, we're done
die unless close(FH);
