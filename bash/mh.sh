#!/bin/sh
#mh.sh stands for "mount henry"
#if henry.lawrence.edu has not been mounted, mount it and then open it

#STATUS: Stable. Complete.

#set your parameters here
username="CHANGEME" #username on henry.lawrencee.du
uid="CHANGEME" #userid of your linux user
gid="CHANGEME" #groupid of your linux user
mountpoint="CHANGEME" #mountpoint on the local machine

prevMount=$(fgrep -c "henry.lawrence.edu" /etc/mtab )
isMounted="1" # var used to indicate if henry is currently mounted
if [ $prevMount = 0 ] # /etc/mtab has no entry for //henry.lawrence.edu
then
	for i in 1 2 3 # give user 3 chances to log on
	do
		echo -n "Password for "$username" on henry.lawrence.edu: "
		stty -echo # turn off printing to console

		## use this if you want to enter the password each time
		read pass
		echo ""
		sudo mount -t smbfs -o workgroup=VIKING,username=$username,password=$pass,uid=$uid,gid=$gid,dmask=770,fmask=770 //henry.lawrence.edu/student $mountpoint
	
		## use this if you want to store your username and password in a /root/.smbcredentials file
		#sudo mount -t smbfs -o workgroup=VIKING,credentials=/root/.smbcredentials,uid=$uid,gid=$gid,dmask=770,fmask=770 //henry.lawrence.edu/student $mountpoint

		isMounted="$?" # get the return value of the last command 0=true, else false
		stty echo # turn on printing to console
		
		if [ $isMounted = 0 ] # the mount was successful
		then
			break
		else
			echo -e "\nInvalid login or network error.\n"
		fi
	done
else
	echo "henry was already mounted"
	isMounted="0" # set var since henry has already been mounted
fi

if [ $isMounted = 0 ] # if the mount was successful, open the My Documents folder
then
  	echo -e "\nSuccessfully mounted henry... opening My Documents folder in Konquerer.\n"
# 	#open mounted folder using kfmclient (utility that opens Konqueror)
 	kfmclient openURL  $mountpoint"/"$username"/my documents"
else # if the mount was unsuccessful (3 times), then return an error message and keep the terminal window open
	echo -e "\nPlease check your username and password, and the network connection.\n(Press any key to exit)"
	read dummy # keeps the terminal window open till the user presses a key
fi