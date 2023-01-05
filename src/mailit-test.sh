#!/bin/bash
# mailit-test.sh
# an example of using mailit to send a string from cmd line
# 1.0, 02/10/2008, simple example, john@masinter.net

# echo commands to terminal to show how it is being called
set -x
# this alias should go in your .bashrc to make it easy to call
alias mailit="$HOME/bin/mailit-11.py"
# replace this with one or more of your valid email addresses
T="per1@big.com,per2@big.com,per3@big.com"

# sent mail msg given as text string
mailit debug to="$T" from="admin@mlosjdev.ctdev.net" subject="Test message" mesg="This is a test"

