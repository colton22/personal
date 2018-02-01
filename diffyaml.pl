#!/usr/bin/perl -w

use strict;
use YAML::XS 'LoadFile';
use Switch;
use Text::Diff;
use Sort::Naturally;

# Define Variables
my $f1 = LoadFile($ARGV[0]);
my $f2 = LoadFile($ARGV[1]);
my @file1=();
my @file2=();
my @outputs = ("" , "");

# Define Functions
sub traverse {
    my $c = $_[0]; # Current path in yaml
    my $cloco = $_[1]; # Textile path in yaml 
    my $out = $_[2]; # Which Array entry

    switch (ref($c)) { # Determine which data type
        case 'HASH'     {
                            foreach my $key (keys %{ $c }) { #pull keys for hash
                                my $loco = $cloco . "." . $key; #append key to Textile path
                                traverse($c->{$key}, $loco, $out); #recursively run including new var and path
                            } 
                        } #End of 'HASH'
        case 'ARRAY'    {
                            foreach my $ae (@{ $c }) { # Dig through Array Elements
                                my $loco = $cloco . ".Array"; #append generic name to array
                                traverse($ae, $loco, $out); #recursively run including new var and path
                            }
                        } #EndOf 'ARRAY'
        else            {
                            $c =~ s/\R//g; #Remove line breaks
                            my $outa = $cloco . "='" . $c ."'"; #build new line entery with texile path and value
                            @outputs[$out] = $outputs[$out] . "\n" . $outa; #add new text to array item
                        } #EndOf 'default'
    }
}

# Build YAML files into verbose entery...
traverse($f1, "", 0);
traverse($f2, "", 1);

# Convert to Arrays
foreach my $line (split /^/, $outputs[0]) { push @file1, $line; }
foreach my $line (split /^/, $outputs[1]) { push @file2, $line; }

# Sort Arrays
@file1 = sort @file1;
@file2 = sort @file2;

# Uses Text::Diff to diff the arrays
my $diff = diff \@file1, \@file2;

# Output to screen
foreach my $line (split /^/, $diff) {
    $line =~ s/^ .*//; # Null any common lines
    $line =~ s/^\\.*//; # Null any EOF lines
    $line =~ s/^ *$//; # Null any [:space:]* lines
    $line =~ s/^-/  \</; # Convert to OldStyle Diff (Old file)
    $line =~ s/^\+/    \>/; # Convert to OldStyle Diff (New file)
    print $line if ( $line !~ /^$/ ); # Print if line != Null
}
