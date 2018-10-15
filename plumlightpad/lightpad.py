import datetime
import json
import logging
import telnetlib
import threading

import requests

_LOGGER = logging.getLogger('plumlightpad')

class Lightpad(object):

    def __init__(self, device, data, websession):
        """Initialize the light."""
        self._websession = websession
        self._device = device
        self._data = data
        self._config = data['config']
        self._event_listeners = {}

        # start a new thread to listen for telnet events
        self._telnet_thread = threading.Thread(target=self.__telnet_event_listener,
                                               args=(self.ip, self.__process_event))
        self._telnet_thread.daemon = True
        self._telnet_thread.start()

    def __telnet_event_listener(self, ip, callback):
        """creates a telnet connection to the lightpad"""

        tn = telnetlib.Telnet(ip, 2708)
        self._last_event = ""
        self._telnet_running = True
        while self._telnet_running:
            try:
                raw_string = tn.read_until(b'.\n', 5)

                if len(raw_string) >= 2 and raw_string[-2:] == b'.\n':
                    # lightpad sends ".\n" at the end that we need to chop off
                    json_string = raw_string.decode('ascii')[0:-2]
                    if json_string != self._last_event:
                        callback(json.loads(json_string))

                    self._last_event = json_string

            except:
                pass
        tn.close()

    def __process_event(self, event):
        event['lpid'] = self.lpid
        event['date'] = datetime.datetime.now()
        _LOGGER.debug(event)
        event_type = event['type']
        listeners = self._event_listeners[event_type]
        if listeners is not None:
            for listener in listeners:
                listener(event)

    def close(self):
        self._telnet_running = False
        self._telnet_thread.join()

    def add_event_listener(self, event_type, listener):
        if event_type in self._event_listeners:
            self._event_listeners[event_type].append(listener)
        else:
            self._event_listeners[event_type] = [listener]

    def set_logical_load(self, logical_load):
        self._logical_load = logical_load
        # TODO handle setting friendly name ..

    @property
    def logical_load(self):
        return self._logical_load

    @property
    def access_token(self):
        return self._data['access_token']

    @property
    def lpid(self):
        return self._device['lpid']

    @property
    def ip(self):
        return self._device['ip']

    @property
    def port(self):
        return self._device['port']

    @property
    def llid(self):
        return self._data["llid"]

    @property
    def name(self):
        return self._data["lightpad_name"]

    @property
    def friendly_name(self):
        load = self.logical_load
        return load.name + " " + str(load.lightpads.index(self) + 1)

    @property
    def config(self):
        return self._data['config']

    @property
    def glow_color(self):
        return self.config['glowColor']

    @property
    def glow_timeout(self):
        return self.config['glowTimeout']

    @property
    def glow_fade(self):
        return self.config['glowFade']

    @property
    def glow_enabled(self):
        return self.config['glowEnabled']

    @property
    def force_glow(self):
        return self.config['forceGlow']

    @property
    def glow_intensity(self):
        return self.config['glowIntensity']

    @property
    def glow_tracks_dimmer(self):
        return self._config['glowTracksDimmer']

    async def set_glow_color(self, r, g, b, w):
        config = {
            "glowColor": {
                "red": r,
                "green": g,
                "blue": b,
                "white": w
            }
        }
        return await self.async_set_config(config=config)

    async def set_glow_timeout(self, timeout):
        if timeout >= 0:
            config = {"glowTimeout": timeout}
            await self.async_set_config(config=config)

    async def set_glow_intensity(self, intensity):
        if intensity >= 0:
            config = {"glowIntensity": (float(intensity) / float(100))}
            await self.async_set_config(config=config)

    async def enable_glow(self):
        await self.__enable_glow(True)

    async def disable_glow(self):
        await self.__enable_glow(False)

    async def __enable_glow(self, enable):
        await self.async_set_config({"glowEnabled": enable})

    async def set_config(self, config):
        llid = self.llid

        url = "https://%s:%s/v2/setLogicalLoadConfig" % (self.ip, self.port)
        data = {
            "config": config,
            "llid": llid
        }
        response = await self.post_async(url, data)

        _LOGGER.debug(response)

        if response.status is 204:
            return True
        else:
            _LOGGER.error("Failed to setLogicalLoadConfig", data, response)
            return False


    def post(self, url, data):

        headers = {
            "User-Agent": "Plum/2.3.0 (iPhone; iOS 9.2.1; Scale/2.00)",
            "X-Plum-House-Access-Token": self.access_token
        }
        return requests.post(url, headers=headers, json=data, verify=False)

    async def post_async(self, url, data):
        headers = {
            "User-Agent": "Plum/2.3.0 (iPhone; iOS 9.2.1; Scale/2.00)",
            "X-Plum-House-Access-Token": self.access_token
        }
        return await self._websession.post(url, headers=headers, json=data)

