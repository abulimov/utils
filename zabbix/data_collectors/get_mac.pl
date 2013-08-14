#! /usr/bin/perl
#
# This script is used to get a list of
# mac addresses per port on 3com switches.
# Tested on 3COM 4200G, 4210, 2916, 2924.
# License: MIT
# Author: Alexander Bulimov, lazywolf0@gmail.com
#====================================================================
#
#                   QUERY MAC ADDRESSES FROM 3COM SWITCH FROM SELECTED PORT
#====================================================================


use strict;
use Net::SNMP qw(snmp_dispatcher oid_lex_sort);

my $show_vendor = 1;
my $script = "/usr/share/zabbix/scripts/mac.sh";
my $debug = 0;
my $file_name = "/tmp/$ARGV[0]-getmac.tmp";
my $interval = 90; #refresh rate
my $new = 0;
my @list;
my $write_secs = (stat($file_name))[9];
if ($debug == 1){
        print "file $file_name updated at ", scalar(localtime($write_secs)), "\n";
};
if ($write_secs + $interval < time) {    #file updated less then $interval seconds ago
        if ($debug == 1){print "generating new mac table \n";}
        $new = 1;
        open FH, ">$file_name" or die "can't open '$file_name': $!";
}else {
        if ($debug == 1){print "using old mac table \n";}
        open FR, "<$file_name" or die "can't open '$file_name': $!";
        while(my $line = <FR>) {
                chomp($line);
                my ($p, $m) = split/;/, $line;
                @list[$p] = "@list[$p]$m, ";
        }
}
#=====================================
my $session;
my $error;
my $port = $ARGV[1];
if($new == 1) {
        #=== Setup session to remote host ===
        ($session, $error) = Net::SNMP->session(
        -hostname  => $ARGV[0] || 'localhost',
        -community => 'public',
        -version => '2c',
        -translate   => [-octetstring => 0],
        -port      => 161
        );
        #=== Was the session created? ===
        if (!defined($session)) {
                printf("ERROR: %s\n", $error);
                exit 1;
        }
};
#==================================

#=== OIDs queried to retrieve information ====
my $TpFdbAddress = '1.3.6.1.2.1.17.4.3.1.1';
my $TpFdbPort    = '1.3.6.1.2.1.17.4.3.1.2';
#=============================================
my $result;
my @tmp;
my $x;
if($new == 1) {
        if (defined($result = $session->get_table($TpFdbAddress))) {
                foreach (oid_lex_sort(keys(%{$result}))) {
                        $x = unpack('H*',$result->{$_});
                        $x =~ s/(..(?!\Z))/\1:/g;
                        push( @tmp, $x);
                }
        }else {
                if($debug == 1) {
                        printf("ERROR: %s\n\n", $session->error());
                }
        }
#==========================================
#=== Print the returned MAC ports ===
        $result;
        if (defined($result = $session->get_table(-baseoid => $TpFdbPort))) {
                my $i = 0;
        my $out = "";
                my $res = 0;
                my $tmp_port;
                my $tmp_mac_list = "";
                foreach (oid_lex_sort(keys(%{$result}))) {
                        if($result->{$_} == $port) {
                                $res = 1;
                if( $show_vendor == 1) {
                    $out = `/usr/share/zabbix/scripts/mac.sh -s $tmp[$i]`;
                                    printf("%s(%s)", $tmp[$i], $out);
                }else {
                    printf("%s", $tmp[$i]);
                };
                                print ", ";
                        };
            if( $show_vendor == 1) {
                $out = `/usr/share/zabbix/scripts/mac.sh -s $tmp[$i]`;
                            printf FH ("%s;%s(%s)\n", $result->{$_}, $tmp[$i], $out);
            }else {
                printf FH ("%s;%s\n", $result->{$_}, $tmp[$i]);
            };
                $i++;
                }
                if ($res == 0) {
                        print "null";
                };
        }else {
                if($debug == 1) {
                        printf("ERROR: %s\n\n", $session->error());
                }else {
                        print "null";
                };
        }
}else {
        if(@list[$port]) {
                print "@list[$port]";
        }else {
                print "null";
        };
}
print "\n";
#=============================================
#=== Close the session and exit the program ===
if($new == 1) {
        $session->close;
        close FH;
}else {
        close FR;
}
exit 0;

