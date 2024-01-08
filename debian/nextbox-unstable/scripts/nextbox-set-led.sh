#!/bin/bash


if [[ "$1" == "" || "$2" != "" ]]; then
	echo "Usage: $0 <red,blue,green,yellow,off,white>"
	exit 1
fi

col=$1
base_path="/sys/class/gpio"

setPin()
{
  echo $2 > $base_path/gpio$1/value
}

setOff()
{
  setPin 19 1
  setPin 20 1
  setPin 21 1
}

initPin()
{
  if [ ! -e "$base_path/gpio$1" ]; then
    echo "$1" > $base_path/export
    echo "out" > $base_path/gpio$1/direction
  fi
}

initPin 19
initPin 20
initPin 21

setOff

if [[ "$col" == "red" ]]; then
  setPin 19 0

elif [[ "$col" == "green" ]]; then
  setPin 20 0

elif [[ "$col" == "yellow" ]]; then
  setPin 19 0
  setPin 20 0

elif [[ "$col" == "blue" ]]; then
  setPin 21 0

elif [[ "$col" == "off" ]]; then
  setOff

elif [[ "$col" == "white" ]]; then
  setPin 19 0
  setPin 20 0
  setPin 21 0
else
  exit 1
fi

exit 0
