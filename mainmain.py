#!/usr/bin/python3

"""Copyright (c) 2019, Douglas Otwell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import dbus
import vlc

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
from gpiozero import CPUTemperature

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000


class MainMainAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Mainmain")
        self.include_tx_power = True


class PiService(Service):
    THERMOMETER_SVC_UUID = "00000001-0000-49ad-a3a2-d74bf3958bcf"

    def __init__(self, index):
        self.farenheit = True

        Service.__init__(self, index, self.THERMOMETER_SVC_UUID, True)
        self.add_characteristic(TempCharacteristic(self))
        self.add_characteristic(UnitCharacteristic(self))

    def is_farenheit(self):
        return self.farenheit

    def set_farenheit(self, farenheit):
        self.farenheit = farenheit


class TempCharacteristic(Characteristic):
    TEMP_CHARACTERISTIC_UUID = "00000001-0001-49ad-a3a2-d74bf3958bcf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.TEMP_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(TempDescriptor(self))

    def get_temperature(self):
        value = []
        unit = "C"

        cpu = CPUTemperature()
        temp = cpu.temperature
        if self.service.is_farenheit():
            temp = (temp * 1.8) + 32
            unit = "F"

        strtemp = str(round(temp, 1)) + " " + unit
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_temperature_callback(self):
        if self.notifying:
            value = self.get_temperature()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_temperature()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_temperature_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_temperature()

        return value


class TempDescriptor(Descriptor):
    TEMP_DESCRIPTOR_UUID = "2901"
    TEMP_DESCRIPTOR_VALUE = "CPU Temperature"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.TEMP_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.TEMP_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value


class UnitCharacteristic(Characteristic):
    UNIT_CHARACTERISTIC_UUID = "00000001-0002-49ad-a3a2-d74bf3958bcf"

    def __init__(self, service):
        Characteristic.__init__(
                self, self.UNIT_CHARACTERISTIC_UUID,
                ["read", "write"], service)
        self.add_descriptor(UnitDescriptor(self))

    def WriteValue(self, value, options):
        val = str(value[0]).upper()
        if val == "C":
            self.service.set_farenheit(False)
        elif val == "F":
            self.service.set_farenheit(True)

    def ReadValue(self, options):
        value = []

        if self.service.is_farenheit(): val = "F"
        else: val = "C"
        value.append(dbus.Byte(val.encode()))

        return value


class UnitDescriptor(Descriptor):
    UNIT_DESCRIPTOR_UUID = "2901"
    UNIT_DESCRIPTOR_VALUE = "Temperature Units (F or C)"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.UNIT_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.UNIT_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value


class VLCService(Service):
    VLC_SVC_UUID = "00000002-0000-49ad-a3a2-d74bf3958bcf"

    def __init__(self, index):
        self.movieTitle = ""

        # creating a basic vlc instance
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()

        Service.__init__(self, index, self.VLC_SVC_UUID, True)
        self.add_characteristic(PlayCharacteristic(self))
        self.add_characteristic(StopCharacteristic(self))

    def get_movie(self):
        return self.movieTitle

    def play_media_file(self, filename):
        print("play : " + filename)
        self.movieTitle = filename
        self.mediaplayer.set_media(self.instance.media_new(unicode(filename)))
        self.mediaplayer.play()

    def play(self):
        self.mediaplayer.play()

    def stop(self):
        print("stop")
        self.movieTitle = ""
        self.mediaplayer.stop()


class PlayCharacteristic(Characteristic):
    PLAY_CHARACTERISTIC_UUID = "00000002-0001-49ad-a3a2-d74bf3958bcf"

    def __init__(self, service):
        Characteristic.__init__(
                self, self.PLAY_CHARACTERISTIC_UUID,
                ["read", "write"], service)
        self.add_descriptor(PlayDescriptor(self))

    def WriteValue(self, value, options):
        print("Enter write play")
        val = str(value)
        print(val)
        self.service.play_media_file(val)

    def ReadValue(self, options):
        value = []
        val = self.service.get_movie()
        value.append(dbus.Byte(val.encode()))
        return value


class PlayDescriptor(Descriptor):
    PLAY_DESCRIPTOR_UUID = "2901"
    PLAY_DESCRIPTOR_VALUE = "Play"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.PLAY_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.PLAY_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value


class StopCharacteristic(Characteristic):
    STOP_CHARACTERISTIC_UUID = "00000002-0002-49ad-a3a2-d74bf3958bcf"

    def __init__(self, service):
        Characteristic.__init__(
                self, self.STOP_CHARACTERISTIC_UUID,
                ["read", "write"], service)
        self.add_descriptor(StopDescriptor(self))

    def WriteValue(self, value, options):
        print("Enter write stop")
        val = str(value)
        print(val)
        self.service.stop()

    def ReadValue(self, options):
        value = []
        val = self.service.get_movie()
        value.append(dbus.Byte(val.encode()))
        return value


class StopDescriptor(Descriptor):
    STOP_DESCRIPTOR_UUID = "2901"
    STOP_DESCRIPTOR_VALUE = "Stop"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.STOP_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.STOP_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value


app = Application()
app.add_service(PiService(0))
app.add_service(VLCService(1))
app.register()

adv = MainMainAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
