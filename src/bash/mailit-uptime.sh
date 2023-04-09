# mailstat.sh
# monitor list of mail servers, report any down-time
# keep up-time status on mail servers
# John Masinter, 30-Jul-2009, John_Masinter@McAfee.com

#--------------------------------------------------------------------------------
# CONFIGURATION
#--------------------------------------------------------------------------------

# revision
REV="1.0"

# frequency in seconds to test each server
FREQ=5

# logfiles for: transitions up/down, each test result, and full smtp dialog
LOG=mailstat.log
LOGFREQ=mailstat.freq.log
LOGSMTP=mailstat.smtp.log

# if non-zero output extra info
DEBUG=1

# IP-addr, isdown[0|1], downcnt, upcnt. Add desired mail IPs here.
LIST=( \
"10.14.2.123" "0" "0" "0" \
"10.15.26.150" "0" "0" "0" \
"" "" "" "" \
)

#--------------------------------------------------------------------------------
# SUBROUTINES
#--------------------------------------------------------------------------------

#--------------------
# dump starting list
welcome() {
printf "\
INFO: mailstat.sh ver $REV. Contact John Masinter with questions or improvements.\n\
INFO: Logs: Summary: $LOG, Each test: $LOGFREQ, full smtp: $LOGSMTP.\n\
"
dumplist
}

#--------------------
# dump starting list
dumplist() {
LST=""
i=0;
while [ ${#LIST[$i]} -gt 0 ] ; do
   if [ $DEBUG -ne 0 ] ; then
      echo "DBUG: IP=${LIST[$i]} isdown=${LIST[$((i+1))]} downcnt=${LIST[$((i+2))]}"
   fi
   LST="$LST ${LIST[$i]}"
   i=$((i+4))
done
echo "INFO: Monitoring mail servers:$LST"
} # dumplist

#--------------------
# dump stats for server list
stats() {
TIM=`date +'%y-%m-%d_%H:%M:%S'`
printf "$TIM: IP:down:bad:good, "
i=0;
while [ ${#LIST[$i]} -gt 0 ] ; do
   printf "STAT: ${LIST[$i]}:${LIST[$((i+1))]}:${LIST[$((i+2))]}:${LIST[$((i+3))]}"
   i=$((i+4))
   if [ ${#LIST[$i]} -gt 0 ] ; then printf ", " ; fi
done
if [ $DIFF -eq 1 ] ; then printf " CHANGED" ; fi
printf "\n"
} # stats

#--------------------
# main monitor loop

analyze() {
      #echo "Analyze $i"
      if [ $RET -eq 0 ] ; then 
         printf "Okay.\n" >> $LOGFREQ 
         # change from down to up?
         if [ ${LIST[$((i+1))]} != "0" ] ; then
            #echo "isdown = ${LIST[$((i+1))]}"
            LIST[$((i+1))]="0" # not isdown
            DIFF=1
         fi
         # keep good count
         cnt=${LIST[$((i+3))]}        # up count
         LIST[$((i+3))]=$((cnt+1))    # increment up count
      else                   
         printf "FAIL.\n" >> $LOGFREQ
         # change from up to down?
         if [ ${LIST[$((i+1))]} != "1" ] ; then
            #echo "isdown = ${LIST[$((i+1))]}"
            LIST[$((i+1))]="1" # isdown
            DIFF=1
         fi
         # keep bad count
         cnt=${LIST[$((i+2))]}        # down count
         LIST[$((i+2))]=$((cnt+1))    # increment down count
      fi
} # analyze

#--------------------
# main monitor loop
mainloop() {
while true ; do
   # make one pass thru list of IPs
   DIFF=0
   i=0;
   while [ ${#LIST[$i]} -gt 0 ] ; do
      # perform test on one IP
      TIM=`date +'%y-%m-%d_%H:%M:%S'`
      if [ $DEBUG -ne 0 ] ; then printf "$TIM: ${LIST[$i]}..." >> $LOGFREQ ; fi
      python mailit.py ${LIST[$i]} >> $LOGSMTP
      # interpret results for this IP
      RET=$?
      analyze
      # move to next IP
      i=$((i+4))
   done
   stats   
   TIM=`date +'%y-%m-%d_%H:%M:%S'`
   if [ $DEBUG -ne 0 ] ; then printf "$TIM: Sleeping for $FREQ seconds." >> $LOGFREQ ; fi
   sleep $FREQ
done
} # mainloop

#--------------------------------------------------------------------------------
# MAIN PROGRAM
#--------------------------------------------------------------------------------

# list IPs that will be monitored
welcome

# loop forever to monitor all servers
mainloop

