# Back_MainMain

## Description
BLE GATT server for the Mainmain app

## Requirement

Pi4 with Raspbian and bluetooth installed (The pre-installed one is enough)

## Installation
```
git clone https://github.com/ExtiaLPAS/Back_MainMain.git
cd Back_MainMain
python3 mainmain.py
```

## Services
### Service pi 

Use to interact with the pi as shutdown, CPU temp, ...

`UUID : 00000001-0000-49ad-a3a2-d74bf3958bcf`

#### CPU 

- Read: Get CPU temp

`UUID : 00000001-0001-49ad-a3a2-d74bf3958bcf`

#### Temperature Unit

- Write: Change the temp unit
- Read: Get temp unit

`UUID : 00000001-0002-49ad-a3a2-d74bf3958bcf`

### Service VLC

Use to interact with VLC

`UUID : 00000002-0000-49ad-a3a2-d74bf3958bcf`

#### Play

- Write: Play the given movie
- Read: Get the current movie playing

`UUID : 00000002-0001-49ad-a3a2-d74bf3958bcf`

#### Stop
- Write : Stop the movie

`UUID : 00000002-0002-49ad-a3a2-d74bf3958bcf`

#### Pause
- Write : Toggle pause the movie
- Read : Return if paused

`UUID : 00000002-0003-49ad-a3a2-d74bf3958bcf`


