#!/usr/bin/perl
##This is a humble script intended to download all of a particular file type on a given webpage
##There are still some small issues to resolve like use of double quotes vs single.


require LWP::UserAgent;
$website = @ARGV[0];
$type = @ARGV[1];

my $ua = LWP::UserAgent->new;
my $response = $ua->get($website);
if($response->is_success){
	$stuff = $response->content;
	while($stuff =~ s/a href=\"(.*?\.$type)\"//){
		$link = $1;
		if($link =~ m/^http/) {$download = $link . "\n";}
		else {$download = $website . $link . "\n";}
		print "Downloading file: $download \n";
		`wget $download`;
	}
}
else{
	die $response->status_line;
}
