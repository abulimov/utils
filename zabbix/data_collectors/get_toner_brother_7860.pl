#! /usr/bin/perl
#
# This script is used to get
# toner level from Brother MFC-7860DW
# 
# License: MIT
# Author: Alexander Bulimov, lazywolf0@gmail.com
#====================================================================
#
#                   QUERY TONER LEVEL FROM Brother MFC-7860DW
#====================================================================


use strict;
use warnings;
use WWW::Curl::Easy;

my $debug = 0;
my $interval = 90; #refresh rate
my $new = 0;
my $toner;
#=====================================
my $error;
my $c;
my $curl = WWW::Curl::Easy->new;
my $response_body;
my $site;

$site = 'http://'.$ARGV[0].'/etc/mnt_info.html?kind=item';
$curl->setopt(CURLOPT_HEADER,1);
$curl->setopt(CURLOPT_URL, $site);
$curl->setopt(CURLOPT_TIMEOUT,10);
$curl->setopt(CURLOPT_WRITEDATA,\$response_body);

my $retcode = $curl->perform;
if ($retcode == 0) {
    my $i;
    my @l = split /\n/ ,$response_body;
    my $arraySize = @l;
    my $line;
    my $k;
    my $colorCount = 0;
    for($i = 0; $i < $arraySize; $i++) {
        $line = $l[ $i ];
        if ($line =~ m/Toner\*\*/g) {
            my $nextline = $l[ $i + 2 ] ;
            $k = 0;
            while ($nextline =~ m!((&#x25a0;){1})!g) {
                $k++;
            };
            $toner = $k * 10;
        }
    }
} else {
    # Error code, type of error, error message
    if ($debug == 1){print("An error happened: $retcode ".$curl->strerror($retcode)." ".$curl->errbuf."\n");}
}
#==================================
if (defined  $toner) {
    print $toner;
} else {
    print "0";
};
print "\n";

#=============================================
#=== exit the program ===
exit 0;
