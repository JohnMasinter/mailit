#!/bin/bash
# scan a mail message in a text file, and mung email address to protect from spam.

if [ $# -lt 1 ] ; then
   printf "\nUsage: mailmung [file]\n\nConvert any email addresses in the file to the form \"name_at_domain_dot_com\" This is to protect from spam email harvester robots.\n\n"
   exit 0
fi

#----------------------------------------------------------------------
mung() {

# mung data file into temp file
sed -e 's/@/_at_/g' -e 's/\.com/_dot_com/g' -e 's/\.net/_dot_net/g' -e 's/\.org/_dot_org/g' $datfil > $tmpfil
if [ $? -ne 0 ] ; then
   printf "Error sed'ing file $datfil\n"
   exit 1
fi

# get size of both files
datsiz=`ls -l $datfil | awk '{ print $5 }'`
tmpsiz=`ls -l $tmpfil | awk '{ print $5 }'`
#echo "datsiz=$datsiz tmpsiz=$tmpsiz"
#exit 0

# move the new file over the original, only if it changed
if [ $datsiz -ne $tmpsiz ] ; then
   printf "$datfil\n"
   mv $tmpfil $datfil
   if [ $? -ne 0 ] ; then
      printf "Error moving file $tmpfil to  $datfil\n"
      exit 1
   fi
#else
#   printf "$datfil not changed.\n"
   
fi

} # mung
#----------------------------------------------------------------------

# make a temp file name to hold dir listing
tmpfil=`/usr/local/scripts/tempname /opt/tmp mailmung` 
if [ $? -ne 0 ] ; then
   printf "/usr/local/scripts/tempname failed.\n"
   exit 1
fi

# create temp file to make sure its writable
echo "test" > $tmpfil
if [ $? -ne 0 ] ; then
   printf "Error creating temp file $tmpfil\n"
   exit 1
fi

# process all files
while true; do

   datfil=$1
   #echo "file: $datfil"
   mung
   shift
   if [ $? -ne 0 ] || [ "$1" == "" ] ; then break; fi

done

rm -f $tmpfil

