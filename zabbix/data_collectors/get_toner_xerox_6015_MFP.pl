#! /usr/bin/perl
#====================================================================
#
#                   QUERY TONER LEVEL FROM XEROX 6015 MFP
#====================================================================


use strict;
use warnings;
use WWW::Curl::Easy;

my $debug = 0;
my $file_name = "/tmp/$ARGV[0]-gettoner_xerox.tmp";
my $interval = 90; #refresh rate
my $new = 0;
my %toner;
my $needle = $ARGV[1];
my $write_secs = (stat($file_name))[9];
if ($debug == 1){
        print "file $file_name updated at ", scalar(localtime($write_secs)), "\n";
};
if (!(defined $write_secs) || ($write_secs + $interval < time)) {    #file updated less then $interval seconds ago
    if ($debug == 1){print "generating new toner table \n";}
    $new = 1;
    open FH, "+<$file_name" or open FH, ">$file_name" or die "can't open '$file_name': $!";
    flock(FH, 2) or die "can't flock $file_name: $!";
    seek(FH, 0, 0); truncate(FH, 0);
}else {
    if ($debug == 1){print "using old toner table \n";}
    open FR, "<$file_name" or die "can't open '$file_name': $!";
    flock(FR, 1) or die "can't flock $file_name: $!";
    while(my $line = <FR>) {
        chomp($line);
        my ($p, $m) = split/,/, $line;
        $toner{$p} = $m;
    }
}
#=====================================
my $error;
my $c;
my @color;
$color[0] = 'Cyan';
$color[1] = 'Magenta';
$color[2] = 'Yellow';
$color[3] = 'Black';
my $curl = WWW::Curl::Easy->new;
my $response_body;
#open(my $response, '+>', \$response_body) or die "can't open '$file_name': $!";
my $site;
$site = 'http://'.$ARGV[0].'/status/statsuppliesx.asp';
if($new == 1) {
    $curl->setopt(CURLOPT_HEADER,1);
    $curl->setopt(CURLOPT_URL, $site);
    $curl->setopt(CURLOPT_TIMEOUT,10);
    $curl->setopt(CURLOPT_WRITEDATA,\$response_body);
    my $retcode = $curl->perform;
    if ($retcode == 0) {
        my $text = $response_body;
        my $i = 0;
        while ($text =~ m!((\d)+)&#37;!g)
        {
            $toner{$color[$i]} = $1;
            $i++;
        };
        while ( my ($key, $value) = each(%toner) ) {
            print FH "$key,$value\n";
        }
        } else {
                # Error code, type of error, error message
            if ($debug == 1){print("An error happened: $retcode ".$curl->strerror($retcode)." ".$curl->errbuf."\n");}
        }
};
#==================================
if (exists  $toner{ $needle })
{
    print $toner{$needle};
}else
{
    print "0";
};
print "\n";

#=============================================
#=== Close the session and exit the program ===
if($new == 1) {
        close FH;
}else {
        close FR;
}
exit 0;

