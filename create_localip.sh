#!/bin/bash

localip=$(cat <(ifconfig | grep "inet 10." | awk '{print $2}')) && echo "LOCALIP='$localip'" >> .env